# core/config.py
# Centralized configuration — edit here to restyle the whole app

STATUT_COLORS = {
    "terminé":    "#2ecc71",
    "done":       "#2ecc71",
    "en cours":   "#3498db",
    "in progress":"#3498db",
    "à faire":    "#95a5a6",
    "todo":       "#95a5a6",
    "bloqué":     "#e74c3c",
    "blocked":    "#e74c3c",
    "en retard":  "#e67e22",
    "late":       "#e67e22",
}

# Fallback color when a status value is not in the map above
DEFAULT_STATUS_COLOR = "#bdc3c7"

# Columns the user can color by, in priority order (first available wins)
COLOR_BY_PRIORITY = ["Responsable", "Statut", "Catégorie"]

# Visual settings
CHART_FONT_FAMILY = "Inter, Arial, sans-serif"
CHART_FONT_SIZE   = 13
CHART_BG_PLOT     = "#fafafa"
CHART_BG_PAPER    = "#ffffff"
CHART_GRID_COLOR  = "#ececec"
CHART_ROW_HEIGHT  = 45   # pixels per task row
CHART_MIN_HEIGHT  = 420  # minimum chart height in pixels
CHART_PROGRESS_FILL = "rgba(0,0,0,0.25)"
TODAY_LINE_COLOR  = "#e74c3c"
