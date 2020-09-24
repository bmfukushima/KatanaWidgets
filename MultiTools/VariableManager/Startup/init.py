from qtpy.QtWidgets import QLabel, QMenu
from qtpy.QtGui import QPixmap
from Katana import Utils, UI4

from Utils2.settings import BEBOP_ON_JPG, BEBOP_OFF_JPG

def onGSVChange(args):
    #import NodegraphAPI

    # get arguments from event
    if args[0][2]:
        node = args[0][2]['node']
        if node.getType() == 'VariableManager':
            pass
            #print (node.getName())


def createNewPatternEvent():
    #print('start')
    Utils.EventModule.RegisterCollapsedHandler(onGSVChange, 'parameter_setValue')
    #print('end register')





