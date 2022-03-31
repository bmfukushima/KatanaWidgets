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
cgwidgets_dir = katana_bebop_dir + "/cgwidgets"

# append paths
sys.path.append(katana_bebop_dir)

CGWIDGETS_EXISTS = False
for path in sys.path:
    if "cgwidgets" in path:
        CGWIDGETS_EXISTS = True
        cgwidgets_logger = ""

if not CGWIDGETS_EXISTS:
    sys.path.append(cgwidgets_dir)
    cgwidgets_logger = f"\n\t|\t|__  Appending...  {cgwidgets_dir} to PYTHONPATH\n"

# update envars
os.environ["KATANABEBOP"] = katana_bebop_dir



print(f"""
...........................................................................................
................................      THE GOOD STUFF      .................................
...........................................................................................
\t|____  ENVIRONMENT
\t|\t|__  Appending...  {katana_bebop_dir} to PYTHONPATH {cgwidgets_logger}
\t|
\t|____  MACROS
\t|\t|__ CalculateNearFarObjects
\t|\t|__ CleanupEmptyGroups
\t|\t|__ Frustum
\t|"""
)
