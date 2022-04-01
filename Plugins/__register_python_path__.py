""" This file registers the KatanaBebop path to the system path and log that to the console.
This is needed for import purposes of the library.  This file will also store that directory
under the environment variable $KATANA_BEBOP for future use.

Notes:
Logo from:
https://patorjk.com/software/taag/#p=testall&c=c%2B%2B&f=Fire%20Font-s&t=KATANA%20BEBOP

old banner
mini
keyboard

Cybermedium
Cyberlarge

Banner
JS STICK LETTERS
Ivrit
Broadway
BroadwayKB
Big
Standard
Starwars
Electronic?

"""
import sys
import os
import inspect

# build katana bebop path from current location
CURRENT_DIR = (
    os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
)
katana_bebop_dir = "/".join(CURRENT_DIR.split("/")[:-1])


# append paths
sys.path.append(katana_bebop_dir)

# register cgwidgets
try:
    import cgwidgets
    cgwidgets_logger = ""
except ModuleNotFoundError:
    cgwidgets_dir = katana_bebop_dir + "/libs/cgwidgets"
    sys.path.append(cgwidgets_dir)
    cgwidgets_logger = f"\n\t|\t|__  Appending...  {cgwidgets_dir} to PYTHONPATH"


# packaging
try:
    import packaging
    packaging_logger = ""
except ModuleNotFoundError:
    packaging_dir = katana_bebop_dir + "/libs/packaging"
    sys.path.append(packaging_dir)
    packaging_logger = f"\n\t|\t|__  Appending...  {packaging_dir} to PYTHONPATH"


# qtpy
try:
    import qtpy
    qtpy_logger = ""
except ModuleNotFoundError:
    qtpy_dir = katana_bebop_dir + "/libs/qtpy"
    sys.path.append(qtpy_dir)
    qtpy_logger = f"\n\t|\t|__  Appending...  {qtpy_dir} to PYTHONPATH"


# update envars
os.environ["KATANABEBOP"] = katana_bebop_dir



print(f"""
...........................................................................................
................................      THE GOOD STUFF      .................................
...........................................................................................
\t|____  ENVIRONMENT
\t|\t|__  Appending...  {katana_bebop_dir} to PYTHONPATH {cgwidgets_logger} {packaging_logger} {qtpy_logger}
\t|
\t|____  MACROS
\t|\t|__ CalculateNearFarObjects
\t|\t|__ CleanupEmptyGroups
\t|\t|__ Frustum
\t|"""
)
