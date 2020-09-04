import sys
import os
import inspect

CURRENT_DIR = (
    os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
)
print ('Adding {CURRENT_DIR} to PYTHONPATH'.format(CURRENT_DIR=CURRENT_DIR))
sys.path.append(CURRENT_DIR)

