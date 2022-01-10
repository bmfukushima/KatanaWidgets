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

CURRENT_DIR = (
    os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
)
CURRENT_DIR = "/".join(CURRENT_DIR.split("/")[:-1])

sys.path.append(CURRENT_DIR)
os.environ["KATANABEBOP"] = CURRENT_DIR


print("""
...........................................................................................
................................      THE GOOD STUFF      .................................
...........................................................................................
\t|____  ENVIRONMENT
\t|\t|__  Appending...  {CURRENT_DIR} to PYTHONPATH
\t|
\t|____  MACROS
\t|\t|__ Frustum
\t|\t|__ CleanupEmptyGroups
\t|""".format(CURRENT_DIR=CURRENT_DIR)
)
