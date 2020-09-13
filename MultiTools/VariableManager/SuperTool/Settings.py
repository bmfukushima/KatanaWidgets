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
