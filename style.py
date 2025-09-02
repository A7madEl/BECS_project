# file: style.py
# עיצוב מרוכז ל-Tkinter/ttk: ערכות צבע, טיפוגרפיה וסגנונות ווידג'טים

import tkinter as tk
from tkinter import ttk

PALETTE_DARK = {
    "bg":        "#121417",
    "card":      "#1b1f24",
    "text":      "#e6e6e6",
    "muted":     "#a8b0b8",
    "accent":    "#3f8cff",
    "accent_fg": "#ffffff",
    "danger":    "#e53935",
    "danger_fg": "#ffffff",
    "ok":        "#2e7d32",
    "warn":      "#e67e22",
    "error":     "#b71c1c",
    "table_sel": "#2a3b55",
    "border":    "#2a3036",
}

PALETTE_LIGHT = {
    "bg":        "#f6f7f9",
    "card":      "#ffffff",
    "text":      "#20232a",
    "muted":     "#5c6773",
    "accent":    "#2667ff",
    "accent_fg": "#ffffff",
    "danger":    "#e53935",
    "danger_fg": "#ffffff",
    "ok":        "#2e7d32",
    "warn":      "#e67e22",
    "error":     "#b71c1c",
    "table_sel": "#dce7ff",
    "border":    "#e5e9ef",
}

def _clamp(x): return max(0, min(255, int(x)))

def _shade(hex_color: str, delta: int) -> str:
    """כהות/בהירות של צבע HEX (delta שלילי=כהה, חיובי=בהיר)."""
    hex_color = hex_color.lstrip("#")
    r = _clamp(int(hex_color[0:2], 16) + delta)
    g = _clamp(int(hex_color[2:4], 16) + delta)
    b = _clamp(int(hex_color[4:6], 16) + delta)
    return f"#{r:02x}{g:02x}{b:02x}"

def apply_theme(root: tk.Misc, mode: str = "dark"):
    """הפעלת ערכת עיצוב על חלון קיים. mode: 'dark' או 'light'"""
    palette = PALETTE_DARK if mode.lower() == "dark" else PALETTE_LIGHT
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    # רקע בסיס
    root.configure(bg=palette["bg"])

    # טיפוגרפיה
    font_title = ("Arial", 20, "bold")
    font_h2    = ("Arial", 14, "bold")
    font_base  = ("Arial", 11)

    # בסיס
    style.configure(".", font=font_base, foreground=palette["text"], background=palette["bg"])
    style.configure("TFrame", background=palette["bg"])
    style.configure("TLabel", background=palette["bg"], foreground=palette["text"])
    style.configure("TNotebook", background=palette["bg"])
    style.configure("TNotebook.Tab", padding=(14, 8), font=("Arial", 11, "bold"))
    style.map("TNotebook.Tab",
              background=[("selected", palette["card"]), ("!selected", palette["bg"])],
              foreground=[("selected", palette["text"]), ("!selected", palette["muted"])])

    # כרטיסים
    style.configure("Card.TLabelframe",
                    background=palette["card"],
                    bordercolor=palette["border"],
                    relief="solid", borderwidth=1, padding=12)
    style.configure("Card.TLabelframe.Label",
                    background=palette["card"],
                    foreground=palette["text"],
                    font=("Arial", 12, "bold"))

    # כפתורים
    style.configure("TButton", padding=10, relief="flat",
                    background=palette["card"], foreground=palette["text"])
    style.map("TButton",
              background=[("active", palette["border"])],
              relief=[("pressed", "sunken"), ("!pressed", "flat")])

    style.configure("Accent.TButton", background=palette["accent"], foreground=palette["accent_fg"])
    style.map("Accent.TButton", background=[("active", _shade(palette["accent"], -12))])

    style.configure("Danger.TButton", background=palette["danger"], foreground=palette["danger_fg"])
    style.map("Danger.TButton", background=[("active", _shade(palette["danger"], -12))])

    # שדות קלט
    field_bg = palette["card"]
    style.configure("TEntry", fieldbackground=field_bg, foreground=palette["text"])
    style.configure("TCombobox", fieldbackground=field_bg, background=field_bg, foreground=palette["text"])
    style.map("TCombobox",
              fieldbackground=[("readonly", field_bg)],
              foreground=[("readonly", palette["text"])])

    # טבלאות
    style.configure("Treeview",
                    background=palette["card"],
                    fieldbackground=palette["card"],
                    foreground=palette["text"],
                    rowheight=28,
                    bordercolor=palette["border"], borderwidth=1)
    style.configure("Treeview.Heading",
                    background=palette["bg"], foreground=palette["muted"],
                    relief="flat", font=("Arial", 11, "bold"))
    style.map("Treeview",
              background=[("selected", palette["table_sel"])],
              foreground=[("selected", palette["text"])])

    # כותרות
    style.configure("Title.TLabel", background=palette["bg"], foreground=palette["text"], font=font_title)
    style.configure("H2.TLabel",    background=palette["bg"], foreground=palette["text"], font=font_h2)

    return palette
