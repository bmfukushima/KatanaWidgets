from cgwidgets.utils import multiplyRGBAValues

################################
#########    COLORS    ###########
################################

# hacky color resets
RGBA_TEXT_COLOR = (192, 192, 192, 255)
RGBA_TEXT_COLOR_DISABLED = multiplyRGBAValues(RGBA_TEXT_COLOR, mult=0.75)

RGBA_KATANA_LOCAL_YELLOW = (255, 200, 0, 255)
RGBA_KATANA_LOCAL_YELLOW_DISABLED = multiplyRGBAValues(RGBA_KATANA_LOCAL_YELLOW, mult=0.75)

RGBA_SELECTION_BG = (80, 80, 80, 255)
