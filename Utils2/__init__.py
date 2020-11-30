from .Utils2 import *

try:
    # loading int katana
    import gsvutils
    import nodeutils
    import nodeinterface
    import colors
except ModuleNotFoundError:
    # loading locally
    from . import gsvutils
    from . import nodeutils
    from . import nodeinterface
    from . import colors

