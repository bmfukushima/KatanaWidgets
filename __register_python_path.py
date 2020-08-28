import sys
import os
import inspect

CURRENT_DIR = (
    os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
)
print (CURRENT_DIR)
sys.path.append(CURRENT_DIR)
#print('/'.join(KATANA_RESOURCES_DIR.split('/')[:-1]))

