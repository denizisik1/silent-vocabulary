import os

ZOOM_STEP_PERCENT = 5

DEFAULT_ZOOM_PERCENT = int(os.environ.get("SILENT_VOCABULARY_DEFAULT_ZOOM_PERCENT", "100"))
DEFAULT_MONO_ZOOM_PERCENT = int(
    os.environ.get("SILENT_VOCABULARY_DEFAULT_MONO_ZOOM_PERCENT", "100")
)
DEFAULT_REFERENCE_ZOOM_PERCENT = int(
    os.environ.get("SILENT_VOCABULARY_DEFAULT_REFERENCE_ZOOM_PERCENT", "100")
)
MIN_ZOOM_PERCENT = 80
MAX_ZOOM_PERCENT = 150


def clamp_zoom_percent(value: int) -> int:
    if value < MIN_ZOOM_PERCENT:
        return MIN_ZOOM_PERCENT
    if value > MAX_ZOOM_PERCENT:
        return MAX_ZOOM_PERCENT
    return value


def scale_px(base_px: int, zoom_percent: int) -> int:
    scaled = round(base_px * clamp_zoom_percent(zoom_percent) / 100)
    return max(1, scaled)
