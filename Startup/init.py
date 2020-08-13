# add global dir here with something like
import sys
import os

print(os.path.abspath(__file__))
#print(__path__)
#print(__module__)
#print(__all__)
KATANA_RESOURCES_DIR = os.path.dirname(os.path.dirname(__file__))
MULTITOOLS_DIR = '{KATANA_RESOURCES_DIR}/MultiTools'.format(
    KATANA_RESOURCES_DIR=KATANA_RESOURCES_DIR
)
sys.path.append(MULTITOOLS_DIR)
print(MULTITOOLS_DIR)
#from ..MultiTools.VariableManager import createNewPatternEvent

from VariableManager import createNewPatternEvent

createNewPatternEvent()