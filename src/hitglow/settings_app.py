"""Fenetre de parametrage HitGlow (customtkinter) : mapping par detection,
couleurs, transparence, aide OBS, apercu en direct, lancement de l'overlay
en sous-processus. Remplace l'edition manuelle d'un fichier de config.
"""

import ctypes
import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import colorchooser, filedialog

import customtkinter as ctk
import pygame

from hitglow import layout, settings_store
from hitglow.input_reader import JoystickReader, resolve_action_buttons, resolve_directions
from hitglow.overlay_window import ButtonGlow, render_frame

DIRECTION_LABELS = {"LEFT": "Gauche", "DOWN": "Bas", "RIGHT": "Droite", "UP": "Haut"}
ACTION_NAMES = ["1", "2", "3", "4", "HEAT", "RAGE"]

DETECT_TIMEOUT_MS = 6000
POLL_INTERVAL_MS = 30

PREVIEW_WIDTH = 360
PREVIEW_HEIGHT = 220
PREVIEW_SCALE = 0.55
PREVIEW_BG = (231, 231, 234)
PREVIEW_INTERVAL_MS = 50

# Palette : theme clair, minimal, inspire d'un dashboard moderne.
BG = "#f2f2f4"
CARD = "#ffffff"
BORDER = "#e3e3e8"
TEXT = "#17171b"
MUTED = "#84848c"
PRIMARY = "#17171b"
PRIMARY_HOVER = "#000000"
ACCENT = "#c8102e"

OBS_HELP_TEXT = """AJOUTER HITGLOW DANS OBS

1. Clique sur "Lancer l'overlay" en bas de cette fenetre.
2. Dans OBS, ajoute une source "Capture de fenetre" (Window Capture) et
   cible la fenetre "HitGlow".
3. Methode de capture recommandee : "Windows 10 (1903 et plus)" (Windows
   Graphics Capture) — c'est celle qui restitue correctement la
   transparence par pixel de l'overlay.
4. Positionne et redimensionne l'overlay directement sur ton bureau :
   clic-glisser pour deplacer, molette pour redimensionner. La position
   et la taille sont sauvegardees automatiquement.

SI LA FENETRE APPARAIT NOIRE/OPAQUE DANS OBS

Decoche "Transparence reelle" dans l'onglet Apparence : l'overlay
bascule sur un fond uni (magenta par defaut, modifiable). Ajoute alors
un filtre "Incrustation couleur" (Chroma Key) sur la source dans OBS,
en ciblant cette couleur.
"""


def _mapping_status_text(settings, name, is_direction):
    if is_direction:
        source = settings["direction_source"].get(name)
        if source == "hat":
            return "Hat"
        if source == "axis":
            mapping = settings["axis_mapping"].get(name)
            if mapping:
                sign = "+" if mapping[1] > 0 else "-"
                return f"Axe {mapping[0]} ({sign})"
            return "Axe (?)"
        if source == "button":
            index = settings["button_direction_mapping"].get(name)
            return f"Bouton {index}" if index is not None else "Bouton (?)"
        return "Non mappe"

    index = settings["action_buttons"].get(name)
    return f"Bouton {index}" if index is not None else "Non mappe"


def _hex(rgb):
    return "#%02x%02x%02x" % tuple(rgb)


def _hex_to_rgb(hex_color):
    return [int(hex_color[i:i + 2], 16) for i in (1, 3, 5)]


def _surface_to_photoimage(surface, background_rgb):
    """Aplati une pygame.Surface (avec alpha) sur un fond opaque et la
    convertit en tk.PhotoImage via le format PPM (supporte nativement par
    Tk, aucune dependance supplementaire type Pillow)."""
    width, height = surface.get_size()
    flat = pygame.Surface((width, height))
    flat.fill(background_rgb)
    flat.blit(surface, (0, 0))
    raw = pygame.image.tostring(flat, "RGB")
    header = f"P6 {width} {height} 255\n".encode("ascii")
    return tk.PhotoImage(data=header + raw)


def _overlay_launch_args():
    if getattr(sys, "frozen", False):
        return [sys.executable, "--overlay"]
    script = Path(__file__).resolve().parent.parent.parent / "run_hitglow.py"
    return [sys.executable, str(script), "--overlay"]


class SettingsApp:
    def __init__(self, root):
        self.root = root
        self.settings = settings_store.load_settings()
        self.joystick_names = []
        self.joystick_reader = None
        self.overlay_process = None
        self.detect_target = None
        self.detect_baseline = None
        self.detect_deadline = None
        self.status_var = tk.StringVar(value="")
        self.direction_rows = {}
        self.action_rows = {}
        self.color_swatches = {}
        self.preview_image = None
        self.glows = {}
        self._rebuild_glow_states()

        ctk.set_appearance_mode("light")
        root.title("HitGlow — Parametres")
        root.geometry("1040x760")
        root.configure(fg_color=BG)
        root.minsize(860, 620)

        content = ctk.CTkFrame(self.root, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=16)

        # Le panneau d'apercu (largeur fixe, side="right") doit etre empaquete
        # AVANT le panneau gauche (fill="both", expand=True) : sinon ce dernier
        # reclame toute la cavite disponible en premier et ne laisse plus de
        # place au panneau de droite, quelle que soit sa taille demandee.
        self._build_preview_section(content)

        left = ctk.CTkFrame(content, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        self._build_joystick_section(left)
        self._build_footer(left)
        self._build_tabs(left)

        self._refresh_joysticks()
        self._sync_mapping_labels()
        self._update_preview()

    # ------------------------------------------------------------ cards
    @staticmethod
    def _card(parent, **kwargs):
        opts = dict(fg_color=CARD, corner_radius=14, border_width=1, border_color=BORDER)
        opts.update(kwargs)
        return ctk.CTkFrame(parent, **opts)

    # -------------------------------------------------------- joystick
    def _build_joystick_section(self, parent):
        card = self._card(parent)
        card.pack(side="top", fill="x", pady=(0, 12))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(inner, text="Manette", text_color=TEXT, font=("Segoe UI", 13, "bold")).pack(side="left")
        self.joystick_var = tk.StringVar(value="(aucune manette detectee)")
        self.joystick_menu = ctk.CTkOptionMenu(
            inner, values=["(aucune manette detectee)"], variable=self.joystick_var,
            command=self._on_joystick_selected, width=280, fg_color=CARD, button_color=BORDER,
            button_hover_color=BORDER, text_color=TEXT, dropdown_fg_color=CARD, dropdown_text_color=TEXT,
        )
        self.joystick_menu.pack(side="left", padx=12)
        ctk.CTkButton(
            inner, text="Rafraichir", command=self._refresh_joysticks, width=100,
            fg_color=CARD, hover_color=BORDER, text_color=TEXT, border_width=1, border_color=BORDER,
        ).pack(side="left")

    def _refresh_joysticks(self):
        pygame.joystick.quit()
        pygame.joystick.init()
        self.joystick_names = [pygame.joystick.Joystick(i).get_name() for i in range(pygame.joystick.get_count())]
        values = self.joystick_names or ["(aucune manette detectee)"]
        self.joystick_menu.configure(values=values)
        index = settings_store.resolve_joystick_index(
            self.joystick_names, self.settings["joystick_name"], self.settings["joystick_index"],
        )
        if index is not None:
            self.joystick_var.set(self.joystick_names[index])
            self._open_joystick(index)
        else:
            self.joystick_var.set("(aucune manette detectee)")
            self.joystick_reader = None

    def _on_joystick_selected(self, value):
        if value not in self.joystick_names:
            return
        index = self.joystick_names.index(value)
        self.settings["joystick_name"] = value
        self.settings["joystick_index"] = index
        settings_store.save_settings(self.settings)
        self._open_joystick(index)

    def _open_joystick(self, index):
        try:
            self.joystick_reader = JoystickReader(index)
        except RuntimeError:
            self.joystick_reader = None

    # ------------------------------------------------------------ tabs
    def _build_tabs(self, parent):
        card = self._card(parent)
        card.pack(side="top", fill="both", expand=True)

        tabview = ctk.CTkTabview(
            card, fg_color=CARD, segmented_button_fg_color=BG,
            segmented_button_selected_color=PRIMARY, segmented_button_selected_hover_color=PRIMARY_HOVER,
            segmented_button_unselected_color=BG, text_color=TEXT, text_color_disabled=MUTED,
        )
        tabview.pack(fill="both", expand=True, padx=12, pady=12)

        mapping_tab = tabview.add("Mapping")
        appearance_tab = tabview.add("Apparence")
        obs_tab = tabview.add("Aide OBS")

        self._build_mapping_tab(mapping_tab)
        self._build_appearance_tab(appearance_tab)
        self._build_obs_tab(obs_tab)

    # ---------------------------------------------------------- mapping
    def _build_mapping_tab(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll, text="Directions", text_color=TEXT, font=("Segoe UI", 13, "bold")).pack(anchor="w")
        for name in ("LEFT", "DOWN", "RIGHT", "UP"):
            self.direction_rows[name] = self._build_mapping_row(scroll, DIRECTION_LABELS[name], name, True)

        ctk.CTkLabel(scroll, text="Actions", text_color=TEXT, font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(14, 0))
        for name in ACTION_NAMES:
            self.action_rows[name] = self._build_mapping_row(scroll, name, name, False)

        ctk.CTkLabel(
            scroll,
            text="Le champ texte est le nom affiche sur le rond (renommable).\n"
                 "Clique \"Detecter\" puis appuie sur le bouton physique correspondant sur ta manette.",
            text_color=MUTED, justify="left",
        ).pack(anchor="w", pady=(10, 0))

    def _build_mapping_row(self, parent, label_text, target, is_direction):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=3)

        ctk.CTkLabel(row, text=label_text, text_color=TEXT, width=70, anchor="w").pack(side="left")

        name_var = tk.StringVar(value=self.settings["labels"].get(target, target))
        name_entry = ctk.CTkEntry(row, textvariable=name_var, width=70, fg_color=BG, text_color=TEXT, border_color=BORDER)
        name_entry.pack(side="left", padx=6)
        name_entry.bind("<FocusOut>", lambda e, t=target, v=name_var: self._on_label_renamed(t, v))
        name_entry.bind("<Return>", lambda e, t=target, v=name_var: self._on_label_renamed(t, v))

        status_label = ctk.CTkLabel(row, text="", text_color=MUTED, width=110, anchor="w")
        status_label.pack(side="left", padx=6)

        button = ctk.CTkButton(row, text="Detecter", width=110, fg_color=CARD, hover_color=BG,
                                text_color=TEXT, border_width=1, border_color=BORDER)
        button.configure(command=lambda: self._start_detect(target, is_direction, button, status_label))
        button.pack(side="left")
        return status_label

    def _on_label_renamed(self, target, name_var):
        text = name_var.get().strip() or target
        name_var.set(text)
        self.settings["labels"][target] = text
        settings_store.save_settings(self.settings)

    def _sync_mapping_labels(self):
        for name, label in self.direction_rows.items():
            label.configure(text=_mapping_status_text(self.settings, name, True))
        for name, label in self.action_rows.items():
            label.configure(text=_mapping_status_text(self.settings, name, False))

    def _start_detect(self, target, is_direction, button, status_label):
        if self.joystick_reader is None:
            self.status_var.set("Selectionne une manette avant de mapper.")
            return
        if self.detect_target is not None:
            return
        hat, axes, buttons = self.joystick_reader.poll(self.settings["hat_index"])
        self.detect_baseline = {"hat": hat, "axes": axes, "buttons": buttons}
        self.detect_target = (target, is_direction, button, status_label)
        self.detect_deadline = self.root.after(DETECT_TIMEOUT_MS, self._cancel_detect)
        button.configure(text="Appuie...")
        self.status_var.set("")
        self._poll_detect()

    def _poll_detect(self):
        if self.detect_target is None:
            return
        target, is_direction, button, status_label = self.detect_target
        hat, axes, buttons = self.joystick_reader.poll(self.settings["hat_index"])
        current = {"hat": hat, "axes": axes, "buttons": buttons}
        result = settings_store.detect_new_input(self.detect_baseline, current)
        if result is not None and (is_direction or result[0] == "button"):
            settings_store.apply_detection(self.settings, target, is_direction, result)
            settings_store.save_settings(self.settings)
            status_label.configure(text=_mapping_status_text(self.settings, target, is_direction))
            self._finish_detect()
            return
        self._detect_after_id = self.root.after(POLL_INTERVAL_MS, self._poll_detect)

    def _finish_detect(self):
        if self.detect_target is not None:
            _, _, button, _ = self.detect_target
            button.configure(text="Detecter")
        if self.detect_deadline is not None:
            self.root.after_cancel(self.detect_deadline)
        self.detect_target = None
        self.detect_baseline = None
        self.detect_deadline = None

    def _cancel_detect(self):
        self.status_var.set("Rien detecte, reessaie.")
        self._finish_detect()

    # ------------------------------------------------------- appearance
    def _build_appearance_tab(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        colors = self.settings["colors"]
        color_defs = [
            ("off", "Eteint"),
            ("direction", "Directions"),
            ("row_top", "Rangee haute"),
            ("row_bottom", "Rangee basse"),
            ("label_text", "Texte"),
        ]
        for key, label_text in color_defs:
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label_text, text_color=TEXT, width=120, anchor="w").pack(side="left")
            swatch = ctk.CTkButton(
                row, text="", width=48, height=28, corner_radius=8, fg_color=_hex(colors[key]),
                hover_color=_hex(colors[key]), border_width=1, border_color=BORDER,
            )
            swatch.configure(command=lambda k=key, s=swatch: self._pick_color(k, s))
            swatch.pack(side="left")
            self.color_swatches[key] = swatch

        self._separator(scroll)

        self.transparent_var = tk.BooleanVar(value=self.settings["transparent_background"])
        ctk.CTkSwitch(
            scroll, text="Transparence reelle (sinon fond uni chroma key)", variable=self.transparent_var,
            command=self._on_transparent_toggle, text_color=TEXT, progress_color=PRIMARY, button_color=CARD,
        ).pack(anchor="w")

        fallback_row = ctk.CTkFrame(scroll, fg_color="transparent")
        fallback_row.pack(fill="x", pady=(8, 3))
        ctk.CTkLabel(fallback_row, text="Fond de repli (chroma key)", text_color=TEXT, width=180, anchor="w").pack(side="left")
        self.fallback_swatch = ctk.CTkButton(
            fallback_row, text="", width=48, height=28, corner_radius=8,
            fg_color=_hex(self.settings["chroma_fallback_color"]), hover_color=_hex(self.settings["chroma_fallback_color"]),
            border_width=1, border_color=BORDER, command=self._pick_fallback_color,
        )
        self.fallback_swatch.pack(side="left")

        self._separator(scroll)

        ctk.CTkLabel(scroll, text="Duree du fondu", text_color=TEXT, font=("Segoe UI", 13, "bold")).pack(anchor="w")
        self.fade_value_label = ctk.CTkLabel(scroll, text=f"{self.settings['fade_ms']} ms", text_color=MUTED)
        fade_scale = ctk.CTkSlider(
            scroll, from_=0, to=600, number_of_steps=60, command=self._on_fade_change,
            fg_color=BORDER, progress_color=PRIMARY, button_color=PRIMARY, button_hover_color=PRIMARY_HOVER,
        )
        fade_scale.set(self.settings["fade_ms"])
        fade_scale.pack(fill="x", pady=(4, 0))
        self.fade_value_label.pack(anchor="e")

        self._separator(scroll)

        ctk.CTkLabel(scroll, text="Police des labels", text_color=TEXT, font=("Segoe UI", 13, "bold")).pack(anchor="w")
        font_row = ctk.CTkFrame(scroll, fg_color="transparent")
        font_row.pack(fill="x", pady=(4, 0))
        current_family = self.settings["font"].get("family")
        self.font_var = tk.StringVar(value=current_family or "(par defaut)")
        available_fonts = ["(par defaut)"] + sorted(pygame.font.get_fonts())
        self.font_menu = ctk.CTkOptionMenu(
            font_row, values=available_fonts, variable=self.font_var, command=self._on_font_selected,
            width=260, fg_color=CARD, button_color=BORDER, button_hover_color=BORDER,
            text_color=TEXT, dropdown_fg_color=CARD, dropdown_text_color=TEXT,
        )
        self.font_menu.pack(side="left")
        ctk.CTkButton(
            font_row, text="Fichier .ttf/.otf...", command=self._browse_font_file, width=150,
            fg_color=CARD, hover_color=BG, text_color=TEXT, border_width=1, border_color=BORDER,
        ).pack(side="left", padx=8)
        self.font_path_label = ctk.CTkLabel(scroll, text=self._font_path_display(), text_color=MUTED)
        self.font_path_label.pack(anchor="w", pady=(4, 0))

    @staticmethod
    def _separator(parent):
        ctk.CTkFrame(parent, fg_color=BORDER, height=1).pack(fill="x", pady=14)

    def _font_path_display(self):
        path = self.settings["font"].get("path")
        return f"Fichier : {path}" if path else "Fichier : (aucun, police systeme)"

    def _on_font_selected(self, value):
        self.settings["font"]["path"] = None
        self.settings["font"]["family"] = None if value == "(par defaut)" else value
        self.font_path_label.configure(text=self._font_path_display())
        settings_store.save_settings(self.settings)

    def _browse_font_file(self):
        path = filedialog.askopenfilename(
            title="Choisir une police",
            filetypes=[("Polices", "*.ttf *.otf"), ("Tous les fichiers", "*.*")],
        )
        if not path:
            return
        self.settings["font"]["path"] = path
        self.settings["font"]["family"] = None
        self.font_var.set("(fichier personnalise)")
        self.font_path_label.configure(text=self._font_path_display())
        settings_store.save_settings(self.settings)

    def _pick_color(self, key, swatch):
        _, hex_color = colorchooser.askcolor(color=_hex(self.settings["colors"][key]), title="Choisir une couleur")
        if hex_color is None:
            return
        self.settings["colors"][key] = _hex_to_rgb(hex_color)
        swatch.configure(fg_color=hex_color, hover_color=hex_color)
        settings_store.save_settings(self.settings)
        if key in ("off", "direction"):
            self._rebuild_glow_states()

    def _pick_fallback_color(self):
        _, hex_color = colorchooser.askcolor(
            color=_hex(self.settings["chroma_fallback_color"]), title="Couleur de fond de repli",
        )
        if hex_color is None:
            return
        self.settings["chroma_fallback_color"] = _hex_to_rgb(hex_color)
        self.fallback_swatch.configure(fg_color=hex_color, hover_color=hex_color)
        settings_store.save_settings(self.settings)

    def _on_transparent_toggle(self):
        self.settings["transparent_background"] = bool(self.transparent_var.get())
        settings_store.save_settings(self.settings)

    def _on_fade_change(self, value):
        self.settings["fade_ms"] = int(float(value))
        self.fade_value_label.configure(text=f"{self.settings['fade_ms']} ms")
        settings_store.save_settings(self.settings)
        self._rebuild_glow_states()

    # -------------------------------------------------------------- OBS
    def _build_obs_tab(self, parent):
        box = ctk.CTkTextbox(parent, fg_color=BG, text_color=TEXT, wrap="word", border_width=0)
        box.insert("1.0", OBS_HELP_TEXT)
        box.configure(state="disabled")
        box.pack(fill="both", expand=True)

    # ------------------------------------------------------------ footer
    def _build_footer(self, parent):
        card = self._card(parent, fg_color="transparent", border_width=0)
        card.pack(side="bottom", fill="x", pady=(12, 0))
        self.launch_button = ctk.CTkButton(
            card, text="Lancer l'overlay", command=self._toggle_overlay, height=42, corner_radius=21,
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER, text_color="#ffffff", font=("Segoe UI", 13, "bold"),
        )
        self.launch_button.pack(side="left")
        ctk.CTkLabel(card, textvariable=self.status_var, text_color=MUTED).pack(side="left", padx=14)

    def _toggle_overlay(self):
        if self.overlay_process is not None and self.overlay_process.poll() is None:
            self.overlay_process.terminate()
            self.overlay_process = None
            self.launch_button.configure(text="Lancer l'overlay")
            self.status_var.set("Overlay arrete.")
            return

        settings_store.save_settings(self.settings)
        self.overlay_process = subprocess.Popen(_overlay_launch_args())
        self.launch_button.configure(text="Arreter l'overlay")
        self.status_var.set("Overlay lance.")

    # ----------------------------------------------------------- preview
    def _rebuild_glow_states(self):
        off_color = tuple(self.settings["colors"]["off"])
        direction_color = tuple(self.settings["colors"]["direction"])
        fade_ms = self.settings["fade_ms"]
        self.glows = {name: ButtonGlow(direction_color, fade_ms) for name in layout.DIRECTION_LAYOUT}
        for name in layout.ACTION_LAYOUT:
            self.glows[name] = ButtonGlow(off_color, fade_ms)

    def _active_colors(self):
        colors = self.settings["colors"]
        direction_color = tuple(colors["direction"])
        row_top = tuple(colors["row_top"])
        row_bottom = tuple(colors["row_bottom"])
        result = {name: direction_color for name in layout.DIRECTION_LAYOUT}
        for name in layout.ACTION_LAYOUT:
            result[name] = row_top if name in layout.ACTION_ROW_TOP else row_bottom
        return result

    def _build_preview_section(self, parent):
        card = self._card(parent, width=PREVIEW_WIDTH + 32, height=560)
        card.pack(side="right", fill="y")
        card.pack_propagate(False)

        ctk.CTkLabel(card, text="Apercu en direct", text_color=TEXT, font=("Segoe UI", 13, "bold")).pack(
            anchor="w", padx=16, pady=(16, 8),
        )

        preview_wrap = ctk.CTkFrame(card, fg_color=_hex(PREVIEW_BG), corner_radius=12)
        preview_wrap.pack(padx=16)
        self.preview_label = tk.Label(preview_wrap, bg=_hex(PREVIEW_BG), bd=0, highlightthickness=0)
        self.preview_label.pack(padx=8, pady=8)

        self.joystick_status_label = ctk.CTkLabel(card, text="", text_color=MUTED, wraplength=PREVIEW_WIDTH, justify="left")
        self.joystick_status_label.pack(anchor="w", padx=16, pady=(10, 0))

        ctk.CTkLabel(
            card,
            text="Reagit en direct a ta manette : appuie sur un bouton pour verifier "
                 "que le mapping et les couleurs sont corrects.",
            text_color=MUTED, wraplength=PREVIEW_WIDTH, justify="left",
        ).pack(anchor="w", padx=16, pady=(10, 16))

    def _update_preview(self):
        if self.joystick_reader is not None:
            hat, axes, buttons = self.joystick_reader.poll(self.settings["hat_index"])
            if hasattr(self, "joystick_status_label"):
                self.joystick_status_label.configure(text=f"Manette connectee : {self.joystick_var.get()}")
        else:
            hat, axes, buttons = (0, 0), [], []
            if hasattr(self, "joystick_status_label"):
                self.joystick_status_label.configure(text="Aucune manette connectee.")

        directions = resolve_directions(
            hat, axes, buttons,
            self.settings["direction_source"], self.settings["axis_mapping"], self.settings["axis_deadzone"],
            self.settings["button_direction_mapping"],
        )
        actions = resolve_action_buttons(buttons, self.settings["action_buttons"])
        pressed = {**directions, **actions}

        now_ms = pygame.time.get_ticks()
        active_colors = self._active_colors()
        glow_colors = {
            name: self.glows[name].update(pressed.get(name, False), active_colors[name], now_ms)
            for name in self.glows
        }

        surface = render_frame(
            PREVIEW_WIDTH, PREVIEW_HEIGHT, glow_colors,
            layout.DIRECTION_LAYOUT, layout.ACTION_LAYOUT, layout.CIRCLE_RADIUS,
            tuple(self.settings["colors"]["label_text"]), labels=self.settings["labels"],
            font_spec=self.settings["font"], scale=PREVIEW_SCALE,
        )
        self.preview_image = _surface_to_photoimage(surface, PREVIEW_BG)
        self.preview_label.configure(image=self.preview_image)

        self.root.after(PREVIEW_INTERVAL_MS, self._update_preview)


def _create_hidden_sdl_window():
    """Cree une fenetre SDL (pygame) invisible. Necessaire car sur Windows,
    le sous-systeme joystick de SDL ne recoit les evenements manette que
    s'il existe un contexte fenetre — meme pour du simple polling, sans
    lire d'evenements clavier/souris. La fenetre est cachee immediatement
    via Win32 pour ne pas apparaitre a cote de la fenetre tkinter."""
    pygame.display.set_mode((2, 2), pygame.NOFRAME)
    hwnd = pygame.display.get_wm_info()["window"]
    ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE


def launch():
    os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")
    pygame.init()
    _create_hidden_sdl_window()
    root = ctk.CTk()
    SettingsApp(root)
    root.mainloop()
