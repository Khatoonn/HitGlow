"""Fenetre overlay HitGlow : transparence Win32 (layered window) et rendu.

Contrainte importante : tout ce qui est dessine sur la surface doit avoir
une alpha de 0 (invisible) ou 255 (opaque) — jamais une valeur intermediaire.
La fenetre layered saute volontairement l'etape de premultiplication de
l'alpha (voir LayeredWindow.update) pour rester performante sans dependance
a numpy ; ca ne fonctionne que si l'alpha est toujours binaire. Le "fondu"
des boutons est donc un fondu de COULEUR (RGB) vers COLOR_OFF, jamais un
fondu d'alpha.
"""

import ctypes
from ctypes import wintypes

import pygame


def lerp_color(color_from, color_to, t):
    """Interpole lineairement entre deux couleurs RGB. t est clampe a [0, 1]."""
    t = max(0.0, min(1.0, t))
    return tuple(
        round(a + (b - a) * t)
        for a, b in zip(color_from, color_to)
    )


class ButtonGlow:
    """Suit la couleur d'affichage courante d'un bouton : couleur active
    tant qu'il est presse, puis fondu vers off_color sur fade_ms apres
    relachement."""

    def __init__(self, off_color, fade_ms):
        self.off_color = off_color
        self.fade_ms = fade_ms
        self._active_color = None
        self._last_pressed_ms = None

    def update(self, is_pressed, active_color, now_ms):
        if is_pressed:
            self._active_color = active_color
            self._last_pressed_ms = now_ms
            return active_color

        if self._active_color is None:
            return self.off_color

        elapsed = now_ms - self._last_pressed_ms
        if elapsed >= self.fade_ms:
            self._active_color = None
            return self.off_color

        t = elapsed / self.fade_ms
        return lerp_color(self._active_color, self.off_color, t)


def _build_font(font_spec, size):
    """Construit une pygame.font.Font a partir d'une spec {"family": ..,
    "path": ..} (voir settings_store DEFAULT_SETTINGS["font"]). path est
    prioritaire sur family ; sans spec (ou en cas d'echec de chargement),
    retombe sur la police par defaut de pygame."""
    if font_spec:
        path = font_spec.get("path")
        if path:
            try:
                return pygame.font.Font(path, size)
            except (FileNotFoundError, OSError):
                pass
        family = font_spec.get("family")
        if family:
            return pygame.font.SysFont(family, size)
    return pygame.font.SysFont(None, size)


def build_glows(off_color, fade_ms, direction_names, action_names):
    """Construit un ButtonGlow par input (directions + actions), tous
    initialises avec off_color comme couleur eteinte — la couleur active
    est fournie separement a chaque appel de ButtonGlow.update(). Centralise
    ce cablage pour eviter de le dupliquer (et de le desynchroniser) entre
    l'overlay et l'apercu de la fenetre de parametrage."""
    names = list(direction_names) + list(action_names)
    return {name: ButtonGlow(off_color, fade_ms) for name in names}


def render_frame(
    width, height, glow_colors, direction_layout, action_layout,
    circle_radius, label_color, labels=None, font_spec=None, scale=1.0, calibration_lines=None,
):
    """Construit la frame a afficher : fond transparent + ronds colores +
    labels texte (directions et actions) + overlay de calibration
    optionnel. Retourne une pygame.Surface avec canal alpha.

    labels : dict nom logique -> texte affiche (ex: {"LEFT": "B"}). Une
    entree absente ou labels=None n'affiche aucun texte pour ce rond,
    pour rester compatible avec les appels qui ne s'en soucient pas."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    surface.fill((0, 0, 0, 0))

    labels = labels or {}
    font = None
    if direction_layout or action_layout:
        font = _build_font(font_spec, max(1, round(20 * scale)))

    def _draw(name, x, y):
        color = glow_colors[name]
        cx, cy = round(x * scale), round(y * scale)
        radius = round(circle_radius * scale)
        _draw_glossy_circle(surface, (cx, cy), radius, color)
        text = labels.get(name, "")
        if text:
            label = font.render(text, False, label_color)
            if pygame.display.get_init() and pygame.display.get_surface() is not None:
                label = label.convert_alpha()
            surface.blit(label, label.get_rect(center=(cx, cy)))

    for name, (x, y) in direction_layout.items():
        _draw(name, x, y)

    for name, (x, y) in action_layout.items():
        _draw(name, x, y)

    if calibration_lines:
        _draw_calibration_overlay(surface, calibration_lines)

    return surface


def _lighten(color, amount):
    return tuple(min(255, channel + amount) for channel in color)


def _draw_glossy_circle(surface, center, radius, color):
    """Rond 'glossy' (liseret fin + bezel sombre + reflet) : gloss discret
    inspire des overlays de manette modernes (ex: Trailpad), avec un
    liseret net qui rappelle les panneaux HUD de Tekken, sans surcharger.
    Reste 100% opaque (alpha 255 partout) pour respecter la contrainte
    alpha binaire du module."""
    cx, cy = center
    if radius <= 0:
        return

    outline_color = (95, 95, 100)
    bezel_thickness = max(2, radius // 6)
    bezel_color = (18, 18, 18)
    pygame.draw.circle(surface, outline_color, (cx, cy), radius)
    pygame.draw.circle(surface, bezel_color, (cx, cy), max(1, radius - 1))

    inner_radius = max(1, radius - bezel_thickness)
    pygame.draw.circle(surface, color, (cx, cy), inner_radius)

    highlight_color = _lighten(color, 90)
    hi_width = max(1, round(inner_radius * 1.1))
    hi_height = max(1, round(inner_radius * 0.55))
    hi_rect = pygame.Rect(0, 0, hi_width, hi_height)
    hi_rect.center = (cx, cy - round(inner_radius * 0.45))
    pygame.draw.ellipse(surface, highlight_color, hi_rect)


def _draw_calibration_overlay(surface, lines):
    """Dessine le panneau de calibration : fond opaque uni (jamais
    translucide, pour respecter la contrainte alpha binaire) + texte."""
    font = pygame.font.SysFont(None, 22)
    line_height = 24
    panel_height = 12 + line_height * len(lines)
    panel_width = 360
    panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel.fill((10, 10, 10, 255))
    has_display = pygame.display.get_init() and pygame.display.get_surface() is not None
    for i, line in enumerate(lines):
        text = font.render(line, False, (255, 255, 255))
        if has_display:
            text = text.convert_alpha()
        panel.blit(text, (8, 8 + i * line_height))
    surface.blit(panel, (0, 0))


user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
HWND_TOPMOST = -1
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
ULW_ALPHA = 0x02
AC_SRC_OVER = 0x00
AC_SRC_ALPHA = 0x01
DIB_RGB_COLORS = 0


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class SIZE(ctypes.Structure):
    _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]


class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [
        ("BlendOp", ctypes.c_byte),
        ("BlendFlags", ctypes.c_byte),
        ("SourceConstantAlpha", ctypes.c_byte),
        ("AlphaFormat", ctypes.c_byte),
    ]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


gdi32.CreateDIBSection.argtypes = [
    wintypes.HDC, ctypes.POINTER(BITMAPINFO), wintypes.UINT,
    ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE, wintypes.DWORD,
]
gdi32.CreateDIBSection.restype = ctypes.c_void_p

user32.UpdateLayeredWindow.argtypes = [
    wintypes.HWND, wintypes.HDC, ctypes.POINTER(POINT), ctypes.POINTER(SIZE),
    wintypes.HDC, ctypes.POINTER(POINT), wintypes.COLORREF,
    ctypes.POINTER(BLENDFUNCTION), wintypes.DWORD,
]
user32.UpdateLayeredWindow.restype = wintypes.BOOL

# Tous les handles/pointeurs Win32 ci-dessous peuvent depasser la plage
# d'un int C 32 bits sur un process 64 bits (ex: adresse d'un objet GDI).
# Sans argtypes explicites, ctypes convertit par defaut en c_int et leve
# "OverflowError: int too long to convert" des que la valeur est trop
# grande — d'ou la declaration systematique ci-dessous.
HGDIOBJ = wintypes.HANDLE

user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetWindowLongW.restype = ctypes.c_long

user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
user32.SetWindowLongW.restype = ctypes.c_long

user32.SetWindowPos.argtypes = [
    wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
    ctypes.c_int, ctypes.c_int, wintypes.UINT,
]
user32.SetWindowPos.restype = wintypes.BOOL

user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetWindowRect.restype = wintypes.BOOL

user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
user32.GetCursorPos.restype = wintypes.BOOL

user32.GetDC.argtypes = [wintypes.HWND]
user32.GetDC.restype = wintypes.HDC

user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
user32.ReleaseDC.restype = ctypes.c_int

gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleDC.restype = wintypes.HDC

gdi32.SelectObject.argtypes = [wintypes.HDC, HGDIOBJ]
gdi32.SelectObject.restype = HGDIOBJ

gdi32.DeleteObject.argtypes = [HGDIOBJ]
gdi32.DeleteObject.restype = wintypes.BOOL

gdi32.DeleteDC.argtypes = [wintypes.HDC]
gdi32.DeleteDC.restype = wintypes.BOOL


def get_cursor_pos():
    """Position du curseur en coordonnees ecran (pas coordonnees fenetre)."""
    pt = POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


class LayeredWindow:
    """Pousse une pygame.Surface (RGBA, alpha binaire) vers l'ecran via
    UpdateLayeredWindow pour une vraie transparence par pixel."""

    def __init__(self, hwnd, width, height):
        self.hwnd = hwnd
        self.width = width
        self.height = height

        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED)

        self._screen_dc = user32.GetDC(0)
        self._mem_dc = gdi32.CreateCompatibleDC(self._screen_dc)

        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = width
        bmi.bmiHeader.biHeight = -height  # top-down
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = 0  # BI_RGB

        self._bits_ptr = ctypes.c_void_p()
        self._bitmap = gdi32.CreateDIBSection(
            self._mem_dc, ctypes.byref(bmi), DIB_RGB_COLORS,
            ctypes.byref(self._bits_ptr), None, 0,
        )
        self._old_bitmap = gdi32.SelectObject(self._mem_dc, self._bitmap)

    def update(self, surface):
        """surface : pygame.Surface RGBA de taille (width, height), alpha
        binaire (0 ou 255) uniquement — voir le docstring du module."""
        raw = pygame.image.tostring(surface, "BGRA")
        ctypes.memmove(self._bits_ptr, raw, len(raw))

        size = SIZE(self.width, self.height)
        src_point = POINT(0, 0)
        blend = BLENDFUNCTION(AC_SRC_OVER, 0, 255, AC_SRC_ALPHA)

        user32.UpdateLayeredWindow(
            self.hwnd, self._screen_dc, None, ctypes.byref(size),
            self._mem_dc, ctypes.byref(src_point), 0, ctypes.byref(blend), ULW_ALPHA,
        )

    def close(self):
        gdi32.SelectObject(self._mem_dc, self._old_bitmap)
        gdi32.DeleteObject(self._bitmap)
        gdi32.DeleteDC(self._mem_dc)
        user32.ReleaseDC(0, self._screen_dc)


class OverlayWindow:
    """Fenetre pygame borderless, topmost, deplacable, avec transparence
    layered (ou fond chroma key de repli selon transparent_background)."""

    def __init__(self, width, height, transparent_background, chroma_fallback_color):
        self.width = width
        self.height = height
        self.chroma_fallback_color = chroma_fallback_color

        pygame.display.set_caption("HitGlow")
        self.screen = pygame.display.set_mode((width, height), pygame.NOFRAME)
        self.hwnd = pygame.display.get_wm_info()["window"]
        self._make_topmost()

        self.layered = None
        if transparent_background:
            self.layered = LayeredWindow(self.hwnd, width, height)

        self._drag_offset = None
        self._win_pos = self._get_window_pos()

    def _make_topmost(self):
        user32.SetWindowPos(self.hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)

    def _get_window_pos(self):
        rect = wintypes.RECT()
        user32.GetWindowRect(self.hwnd, ctypes.byref(rect))
        return rect.left, rect.top

    def get_pos(self):
        return self._win_pos

    def move_to(self, pos):
        x, y = pos
        user32.SetWindowPos(self.hwnd, 0, x, y, 0, 0, SWP_NOSIZE | SWP_NOZORDER)
        self._win_pos = (x, y)

    def present(self, surface):
        if self.layered is not None:
            self.layered.update(surface)
        else:
            self.screen.fill(self.chroma_fallback_color)
            self.screen.blit(surface, (0, 0))
            pygame.display.flip()
            self._make_topmost()

    def start_drag(self, cursor_pos):
        self._drag_offset = (cursor_pos[0] - self._win_pos[0], cursor_pos[1] - self._win_pos[1])

    def drag_to(self, cursor_pos):
        if self._drag_offset is None:
            return
        new_x = cursor_pos[0] - self._drag_offset[0]
        new_y = cursor_pos[1] - self._drag_offset[1]
        user32.SetWindowPos(self.hwnd, 0, new_x, new_y, 0, 0, SWP_NOSIZE | SWP_NOZORDER)
        self._win_pos = (new_x, new_y)

    def end_drag(self):
        self._drag_offset = None

    def close(self):
        if self.layered is not None:
            self.layered.close()
