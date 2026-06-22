# Token warna & font — ubah di sini untuk ganti tema
PRIMARY    = "#0d6efd"
PRIMARY_DK = "#0b5ed7"
DANGER     = "#dc3545"
SUCCESS    = "#198754"
WARNING    = "#ffc107"
MUTED      = "#6c757d"
BG         = "#f8f9fa"
SURFACE    = "#ffffff"
BORDER     = "#dee2e6"
TEXT       = "#212529"
TEXT_MUTED = "#6c757d"
SIDEBAR_BG = "#1e2330"
SIDEBAR_FG = "#adb5bd"


def load_stylesheet(qss_path: str) -> str:
    # Baca QSS lalu inject token warna
    try:
        with open(qss_path, "r") as f:
            qss = f.read()
    except FileNotFoundError:
        return ""

    # Ganti placeholder token dengan nilai warna aktual
    replacements = {
        "{{PRIMARY}}":    PRIMARY,
        "{{PRIMARY_DK}}": PRIMARY_DK,
        "{{DANGER}}":     DANGER,
        "{{SUCCESS}}":    SUCCESS,
        "{{WARNING}}":    WARNING,
        "{{MUTED}}":      MUTED,
        "{{BG}}":         BG,
        "{{SURFACE}}":    SURFACE,
        "{{BORDER}}":     BORDER,
        "{{TEXT}}":       TEXT,
        "{{TEXT_MUTED}}": TEXT_MUTED,
        "{{SIDEBAR_BG}}": SIDEBAR_BG,
        "{{SIDEBAR_FG}}": SIDEBAR_FG,
    }
    for token, value in replacements.items():
        qss = qss.replace(token, value)
    return qss
