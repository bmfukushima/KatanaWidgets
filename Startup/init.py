# add global dir here with something like
import sys
import os
import inspect

CURRENT_DIR = (
    os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
)
KATANA_RESOURCES_DIR = '/'.join(CURRENT_DIR.split('/')[:-1])

MULTITOOLS_DIR = '{KATANA_RESOURCES_DIR}/MultiTools'.format(
    KATANA_RESOURCES_DIR=KATANA_RESOURCES_DIR
)
sys.path.append(KATANA_RESOURCES_DIR)
#print('/'.join(KATANA_RESOURCES_DIR.split('/')[:-1]))
