from .Utils2 import *
try:
    import ParametersMenu
except ModuleNotFoundError:
    pass
try:
    # loading int katana
    import gsvutils
    import nodeutils
    import colors
except ModuleNotFoundError:
    # loading locally
    from . import gsvutils
    from . import nodeutils
    from . import colors

