import os

from Utils2.colors import GRID_COLOR, GRID_HOVER_COLOR

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
SPLITTER_STYLE_SHEET = """
        QSplitter::handle {                        \
            border: 1px double rgba%s;      \
            margin: 5px 5px;                                    \
        }
        QSplitter::handle:hover {                     \
            border: 2px double rgba%s;           \
            margin: 10px 0px;                                    \
        }
"""%(repr(GRID_COLOR), repr(GRID_HOVER_COLOR))

SPLITTER_STYLE_SHEET_HIDE = """
        QSplitter::handle {                        \
            border: 1px double rgba%s;      \
            margin: 0px 0px;                                    \
        }
"""%(repr(GRID_COLOR))

SPLITTER_HANDLE_WIDTH = 10


