"""
QWidget
FormWidget
GroupFormWidget
HideTitleGroup
NodeGroupFormWidget

from Katana import QT4FormWidgets

from QT4FormWidgets import GroupFormWidget, FormWidget


def newFunc(self, value):

    if value == self.isPopdownShown():
        return
    FormWidget.showPopdown(self, value)
    if value:
        self.__syncChildren()

QT4FormWidgets.GroupFormWidget.showPopdown = newFunc

"""
from Katana import QT4FormWidgets
from .ParametersMenuWidgets import ParametersMenuButton


def showPopdownWithCustomMenu(self, value):
    if not hasattr(self, 'custom_menu'):
        widget = self.getRightControlFWidgets()

        self.custom_menu = ParametersMenuButton(node=self.getValuePolicy().getNode())
        widget.addWidget(self.custom_menu)

    QT4FormWidgets.GroupFormWidget.originalShowPopdown(self, value)


def installCustomParametersMenu():
    # backup show popdown...
    QT4FormWidgets.GroupFormWidget.originalShowPopdown = QT4FormWidgets.GroupFormWidget.showPopdown
    QT4FormWidgets.GroupFormWidget.showPopdown = showPopdownWithCustomMenu



# should_recurse = True
#
#
# def reselectNodesHack():
#     from Katana import NodegraphAPI, Utils
#     for node in NodegraphAPI.GetAllEditedNodes():
#         NodegraphAPI.SetNodeEdited(node, False)
#
#     for node in NodegraphAPI.GetAllSelectedNodes():
#         NodegraphAPI.SetNodeEdited(node, True)
#     Utils.EventModule.ProcessAllEvents()
#
#
# def createParametersMenuButton(args):
#     """
#     Creates a custom parameters menu on every single node
#     that's parameters are displayed in the Parameters tab.
#
#     This currently works as a hack so that when a node is set to edited
#     this will created the panel, if it doesn't then it will recurse and try again,
#     as the parameters widgets needs to finish making before our new menu
#     can be inserted into it
#     """
#     # imports
#     from Katana import UI4, Utils, NodegraphAPI
#     from .ParametersMenuWidgets import ParametersMenuButton
#     global should_recurse
#
#     # get all params tabs
#     param_tabs = UI4.App.Tabs.GetTabsByType('Parameters')
#
#     # check
#     for tab in param_tabs:
#         scroll_area = tab._ParameterPanel__panelScrollArea
#         layout = scroll_area.widget().layout()
#         widget = layout.itemAt(0).widget()
#         if widget:
#             control_widgets = widget.getRightControlFWidgets()
#             if not hasattr(control_widgets, 'params_button'):
#                 # create custom menu button
#                 control_widgets.params_button = ParametersMenuButton(node=args[0][2]['node'])
#                 control_widgets.addWidget(control_widgets.params_button)
#                 should_recurse = True
#                 return
#             else:
#                 # reselect node
#                 if should_recurse is True:
#                     reselectNodesHack()
#                     should_recurse = False
#                     return
#         else:
#             # reselect node
#             reselectNodesHack()
#             return