"""Fenetre de parametrage HitGlow (tkinter) : mapping par detection,
couleurs, transparence, aide OBS, lancement de l'overlay en sous-processus.
Remplace l'edition manuelle d'un fichier de configuration.
"""

import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import colorchooser, filedialog, ttk

import pygame

from hitglow import layout, settings_store
from hitglow.input_reader import JoystickReader, resolve_action_buttons, resolve_directions
from hitglow.overlay_window import ButtonGlow, render_frame

DIRECTION_LABELS = {"LEFT": "Gauche", "DOWN": "Bas", "RIGHT": "Droite", "UP": "Haut"}
ACTION_NAMES = ["1", "2", "3", "4", "HEAT", "RAGE"]

DETECT_TIMEOUT_MS = 6000
POLL_INTERVAL_MS = 30

PREVIEW_WIDTH = 340
PREVIEW_HEIGHT = 210
PREVIEW_SCALE = 0.5
PREVIEW_BG = (36, 36, 41)
PREVIEW_INTERVAL_MS = 50

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

        root.title("HitGlow — Parametres")
        root.geometry("980x720")
        root.configure(bg="#1b1b1f")
        root.resizable(True, True)

        self._build_style()

        content = ttk.Frame(self.root)
        content.pack(fill="both", expand=True)
        left = ttk.Frame(content)
        left.pack(side="left", fill="both", expand=True)

        self._build_preview_section(content)
        self._build_joystick_section(left)
        self._build_footer(left)
        self._build_notebook(left)

        self._refresh_joysticks()
        self._sync_mapping_labels()
        self._update_preview()

    # ------------------------------------------------------------ style
    def _build_style(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        bg, panel, fg, accent = "#1b1b1f", "#242429", "#f0f0f0", "#c8102e"
        style.configure(".", background=bg, foreground=fg, fieldbackground=panel)
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg)
        style.configure("TButton", background=panel, foreground=fg, padding=6)
        style.map("TButton", background=[("active", accent)])
        style.configure("Accent.TButton", background=accent, foreground="#ffffff", padding=8)
        style.map("Accent.TButton", background=[("active", "#e0143a")])
        style.configure("TCheckbutton", background=bg, foreground=fg)
        style.configure("TNotebook", background=bg, tabmargins=0)
        style.configure("TNotebook.Tab", background=panel, foreground=fg, padding=(12, 6))
        style.map("TNotebook.Tab", background=[("selected", accent)])
        style.configure("TCombobox", fieldbackground=panel, background=panel, foreground=fg)
        style.configure("TSeparator", background=panel)

    # -------------------------------------------------------- joystick
    def _build_joystick_section(self, parent):
        frame = ttk.Frame(parent, padding=10)
        frame.pack(side="top", fill="x")
        ttk.Label(frame, text="Manette :").pack(side="left")
        self.joystick_var = tk.StringVar()
        self.joystick_combo = ttk.Combobox(frame, textvariable=self.joystick_var, state="readonly", width=32)
        self.joystick_combo.pack(side="left", padx=8)
        self.joystick_combo.bind("<<ComboboxSelected>>", self._on_joystick_selected)
        ttk.Button(frame, text="Rafraichir", command=self._refresh_joysticks).pack(side="left")

    def _refresh_joysticks(self):
        pygame.joystick.quit()
        pygame.joystick.init()
        self.joystick_names = [pygame.joystick.Joystick(i).get_name() for i in range(pygame.joystick.get_count())]
        self.joystick_combo["values"] = self.joystick_names or ["(aucune manette detectee)"]
        index = settings_store.resolve_joystick_index(
            self.joystick_names, self.settings["joystick_name"], self.settings["joystick_index"],
        )
        if index is not None:
            self.joystick_var.set(self.joystick_names[index])
            self._open_joystick(index)
        else:
            self.joystick_var.set("(aucune manette detectee)")
            self.joystick_reader = None

    def _on_joystick_selected(self, event=None):
        name = self.joystick_var.get()
        if name not in self.joystick_names:
            return
        index = self.joystick_names.index(name)
        self.settings["joystick_name"] = name
        self.settings["joystick_index"] = index
        settings_store.save_settings(self.settings)
        self._open_joystick(index)

    def _open_joystick(self, index):
        try:
            self.joystick_reader = JoystickReader(index)
        except RuntimeError:
            self.joystick_reader = None

    # -------------------------------------------------------- notebook
    def _build_notebook(self, parent):
        notebook = ttk.Notebook(parent)
        notebook.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        mapping_tab = ttk.Frame(notebook, padding=10)
        appearance_tab = ttk.Frame(notebook, padding=10)
        obs_tab = ttk.Frame(notebook, padding=10)
        notebook.add(mapping_tab, text="Mapping")
        notebook.add(appearance_tab, text="Apparence")
        notebook.add(obs_tab, text="Aide OBS")

        self._build_mapping_tab(mapping_tab)
        self._build_appearance_tab(appearance_tab)
        self._build_obs_tab(obs_tab)

    # ---------------------------------------------------------- mapping
    def _build_mapping_tab(self, parent):
        ttk.Label(parent, text="Directions", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        dir_frame = ttk.Frame(parent)
        dir_frame.pack(fill="x", pady=(4, 12))
        for name in ("LEFT", "DOWN", "RIGHT", "UP"):
            self.direction_rows[name] = self._build_mapping_row(dir_frame, DIRECTION_LABELS[name], name, True)

        ttk.Label(parent, text="Actions", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        act_frame = ttk.Frame(parent)
        act_frame.pack(fill="x", pady=(4, 12))
        for name in ACTION_NAMES:
            self.action_rows[name] = self._build_mapping_row(act_frame, name, name, False)

        ttk.Label(
            parent,
            text="Le champ texte est le nom affiche sur le rond (renommable). "
                 "Clique \"Detecter\" puis appuie sur le bouton physique correspondant sur ta manette.",
            wraplength=480, foreground="#a0a0a8",
        ).pack(anchor="w", pady=(8, 0))

    def _build_mapping_row(self, parent, label_text, target, is_direction):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=label_text, width=10).pack(side="left")

        name_var = tk.StringVar(value=self.settings["labels"].get(target, target))
        name_entry = ttk.Entry(row, textvariable=name_var, width=8)
        name_entry.pack(side="left", padx=4)
        name_entry.bind("<FocusOut>", lambda e, t=target, v=name_var: self._on_label_renamed(t, v))
        name_entry.bind("<Return>", lambda e, t=target, v=name_var: self._on_label_renamed(t, v))

        status_label = ttk.Label(row, text="", width=16)
        status_label.pack(side="left", padx=6)
        button = ttk.Button(row, text="Detecter")
        button.config(command=lambda: self._start_detect(target, is_direction, button, status_label))
        button.pack(side="left")
        return status_label

    def _on_label_renamed(self, target, name_var):
        text = name_var.get().strip() or target
        name_var.set(text)
        self.settings["labels"][target] = text
        settings_store.save_settings(self.settings)

    def _sync_mapping_labels(self):
        for name, label in self.direction_rows.items():
            label.config(text=_mapping_status_text(self.settings, name, True))
        for name, label in self.action_rows.items():
            label.config(text=_mapping_status_text(self.settings, name, False))

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
        button.config(text="Appuie sur la manette...")
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
            status_label.config(text=_mapping_status_text(self.settings, target, is_direction))
            self._finish_detect()
            return
        self._detect_after_id = self.root.after(POLL_INTERVAL_MS, self._poll_detect)

    def _finish_detect(self):
        if self.detect_target is not None:
            _, _, button, _ = self.detect_target
            button.config(text="Detecter")
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
        colors = self.settings["colors"]
        color_defs = [
            ("off", "Eteint"),
            ("direction", "Directions"),
            ("row_top", "Rangee haute"),
            ("row_bottom", "Rangee basse"),
            ("label_text", "Texte"),
        ]
        for key, label_text in color_defs:
            row = ttk.Frame(parent)
            row.pack(fill="x", pady=3)
            ttk.Label(row, text=label_text, width=14).pack(side="left")
            swatch = tk.Label(row, text="   ", bg=_hex(colors[key]), relief="solid", borderwidth=1, width=6)
            swatch.pack(side="left", padx=6)
            swatch.bind("<Button-1>", lambda e, k=key, s=swatch: self._pick_color(k, s))
            self.color_swatches[key] = swatch

        ttk.Separator(parent).pack(fill="x", pady=10)

        self.transparent_var = tk.BooleanVar(value=self.settings["transparent_background"])
        ttk.Checkbutton(
            parent, text="Transparence reelle (decoche = fond uni chroma key)",
            variable=self.transparent_var, command=self._on_transparent_toggle,
        ).pack(anchor="w")

        fallback_row = ttk.Frame(parent)
        fallback_row.pack(fill="x", pady=3)
        ttk.Label(fallback_row, text="Fond de repli (chroma key)", width=22).pack(side="left")
        self.fallback_swatch = tk.Label(
            fallback_row, text="   ", bg=_hex(self.settings["chroma_fallback_color"]),
            relief="solid", borderwidth=1, width=6,
        )
        self.fallback_swatch.pack(side="left", padx=6)
        self.fallback_swatch.bind("<Button-1>", lambda e: self._pick_fallback_color())

        ttk.Separator(parent).pack(fill="x", pady=10)

        ttk.Label(parent, text="Duree du fondu (ms)").pack(anchor="w")
        self.fade_var = tk.IntVar(value=self.settings["fade_ms"])
        self.fade_value_label = ttk.Label(parent, text=f"{self.settings['fade_ms']} ms")
        fade_scale = ttk.Scale(parent, from_=0, to=600, variable=self.fade_var, command=self._on_fade_change)
        fade_scale.pack(fill="x")
        self.fade_value_label.pack(anchor="e")

        ttk.Separator(parent).pack(fill="x", pady=10)

        ttk.Label(parent, text="Police des labels", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        font_row = ttk.Frame(parent)
        font_row.pack(fill="x", pady=3)
        current_family = self.settings["font"].get("family")
        self.font_var = tk.StringVar(value=current_family or "(par defaut)")
        available_fonts = ["(par defaut)"] + sorted(pygame.font.get_fonts())
        self.font_combo = ttk.Combobox(
            font_row, textvariable=self.font_var, state="readonly", values=available_fonts, width=26,
        )
        self.font_combo.pack(side="left")
        self.font_combo.bind("<<ComboboxSelected>>", self._on_font_selected)
        ttk.Button(font_row, text="Fichier .ttf/.otf...", command=self._browse_font_file).pack(side="left", padx=6)
        self.font_path_label = ttk.Label(parent, text=self._font_path_display(), foreground="#a0a0a8")
        self.font_path_label.pack(anchor="w")

    def _font_path_display(self):
        path = self.settings["font"].get("path")
        return f"Fichier : {path}" if path else "Fichier : (aucun, police systeme)"

    def _on_font_selected(self, event=None):
        value = self.font_var.get()
        self.settings["font"]["path"] = None
        self.settings["font"]["family"] = None if value == "(par defaut)" else value
        self.font_path_label.config(text=self._font_path_display())
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
        self.font_path_label.config(text=self._font_path_display())
        settings_store.save_settings(self.settings)

    def _pick_color(self, key, swatch):
        _, hex_color = colorchooser.askcolor(color=_hex(self.settings["colors"][key]), title="Choisir une couleur")
        if hex_color is None:
            return
        self.settings["colors"][key] = _hex_to_rgb(hex_color)
        swatch.config(bg=hex_color)
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
        self.fallback_swatch.config(bg=hex_color)
        settings_store.save_settings(self.settings)

    def _on_transparent_toggle(self):
        self.settings["transparent_background"] = self.transparent_var.get()
        settings_store.save_settings(self.settings)

    def _on_fade_change(self, value):
        self.settings["fade_ms"] = int(float(value))
        self.fade_value_label.config(text=f"{self.settings['fade_ms']} ms")
        settings_store.save_settings(self.settings)
        self._rebuild_glow_states()

    # -------------------------------------------------------------- OBS
    def _build_obs_tab(self, parent):
        text = tk.Text(parent, wrap="word", bg="#242429", fg="#f0f0f0", relief="flat", padx=10, pady=10)
        text.insert("1.0", OBS_HELP_TEXT)
        text.config(state="disabled")
        text.pack(fill="both", expand=True)

    # ------------------------------------------------------------ footer
    def _build_footer(self, parent):
        frame = ttk.Frame(parent, padding=10)
        frame.pack(side="bottom", fill="x")
        self.launch_button = ttk.Button(frame, text="Lancer l'overlay", style="Accent.TButton", command=self._toggle_overlay)
        self.launch_button.pack(side="left")
        ttk.Label(frame, textvariable=self.status_var).pack(side="left", padx=10)

    def _toggle_overlay(self):
        if self.overlay_process is not None and self.overlay_process.poll() is None:
            self.overlay_process.terminate()
            self.overlay_process = None
            self.launch_button.config(text="Lancer l'overlay")
            self.status_var.set("Overlay arrete.")
            return

        settings_store.save_settings(self.settings)
        self.overlay_process = subprocess.Popen(_overlay_launch_args())
        self.launch_button.config(text="Arreter l'overlay")
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
        frame = ttk.Frame(parent, padding=10)
        frame.pack(side="right", fill="y")
        ttk.Label(frame, text="Apercu en direct", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.preview_label = tk.Label(
            frame, bg=_hex(PREVIEW_BG), width=PREVIEW_WIDTH, height=PREVIEW_HEIGHT,
        )
        self.preview_label.pack(pady=6)
        ttk.Label(
            frame,
            text="Reagit en direct a ta manette : appuie sur un bouton pour verifier "
                 "que le mapping et les couleurs sont corrects.",
            wraplength=PREVIEW_WIDTH, foreground="#a0a0a8",
        ).pack(anchor="w")

    def _update_preview(self):
        if self.joystick_reader is not None:
            hat, axes, buttons = self.joystick_reader.poll(self.settings["hat_index"])
        else:
            hat, axes, buttons = (0, 0), [], []

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
        self.preview_label.config(image=self.preview_image)

        self.root.after(PREVIEW_INTERVAL_MS, self._update_preview)


def launch():
    pygame.init()
    root = tk.Tk()
    SettingsApp(root)
    root.mainloop()
