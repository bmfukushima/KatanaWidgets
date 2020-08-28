import os

try:
    from Katana import NodegraphAPI, KatanaResources
    PUBLISH_DIR = KatanaResources.GetUserKatanaPath() + '/VariableManager'
except ImportError:
    print('not running in Katana')
    pass

PATTERN_PREFIX = 'pattern__'
USER_PREFIX = 'u_'
BLOCK_PREFIX = 'block__'

NODEREFNAME = 'nodeReference'

""" STYLES """
"""
################################
#########    COLORS    ###########
################################
"""
""" BLOCK / PATTERN """
# item bg color
# push button hover color
""" ACCEPTS / DECLINE / MAYBE"""
def convertToHoverColor(rgba, hover_mult=1.5):
    """
    """
    new_color = []
    for value in rgba:
        value *= hover_mult
        if 255 < value:
            value = 255
        new_color.append(int(value))

    return tuple(new_color)

ACCEPT_COLOR_RGBA = (64, 128, 64, 255)
CANCEL_COLOR_RGBA = (128, 64, 64, 255)
MAYBE_COLOR_RGBA = (64, 64, 128, 255)

ACCEPT_HOVER_COLOR_RGBA = convertToHoverColor(ACCEPT_COLOR_RGBA)
CANCEL_HOVER_COLOR_RGBA = convertToHoverColor(CANCEL_COLOR_RGBA)
MAYBE_HOVER_COLOR_RGBA = convertToHoverColor(MAYBE_COLOR_RGBA)

GRID_COLOR = (10, 95, 20, 255)
TEXT_COLOR = (192, 192, 192, 255) # this is hacky... for some reason the QBrush goes =( when using setColor...
#(255,200, 0, 255) KATANA YELLOW

SPLITTER_STYLE_SHEET = """
        QSplitter::handle {                        \
            border: 1px double rgba(10, 95, 20, 255);      \
            margin: 5px 5px;                                    \
        }
        QSplitter::handle:hover {                     \
            border: 2px double rgb(20, 190, 40);           \
            margin: 10px 0px;                                    \
        }
"""

SPLITTER_STYLE_SHEET_HIDE = """
        QSplitter::handle {                        \
            border: 1px double rgba(10, 95, 20, 0);      \
            margin: 0px 0px;                                    \
        }
"""
SPLITTER_HANDLE_WIDTH = 10

""" GIFS """
__gif_dir = '{directory}/gif'.format(
    directory=os.path.dirname(__file__)
)
ACCEPT_GIF = __gif_dir + '/accept.gif'
CANCEL_GIF = __gif_dir + '/cancel.gif'
