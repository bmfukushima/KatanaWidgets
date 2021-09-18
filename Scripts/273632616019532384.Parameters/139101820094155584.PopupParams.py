""" Shows how to create parameter widgets.

For each node selected, the parameters of that node
will be displayed as a tab in a QTabWidget

How to use:
    Select nodes, and run script
"""

import platform
from Katana import UI4, NodegraphAPI
from PyQt5 import QtWidgets, QtCore


def createParam(node):
    # create parameter

    factory = UI4.FormMaster.KatanaFactory.ParameterWidgetFactory
    locationPolicy = UI4.FormMaster.CreateParameterPolicy(None, node.getParameters())
    locationPolicy.getWidgetHints().update(open="True")
    w = factory.buildWidget(None, locationPolicy)   
    return w

# create tab widget
tab_widget = QtWidgets.QTabWidget()

# create tabs
for node in NodegraphAPI.GetAllSelectedNodes():
    w = createParam(node)
    tab_widget.addTab(w, node.getName())

tab_widget.show()

