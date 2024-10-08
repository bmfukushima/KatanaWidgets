"""
QWidget
FormWidget
GroupFormWidget
HideTitleGroup
NodeGroupFormWidget
"""
from Katana import QT4FormWidgets, NodegraphAPI
from .ParametersMenuWidgets import ParametersMenuButton


def showPopdownWithCustomMenu(self, value):
    if not hasattr(self, 'custom_menu'):
        widget = self.getRightControlFWidgets()
        try:
            # get policy
            policy = self.getValuePolicy()

            # latch onto wrench display policy
            if policy.shouldDisplayWrench():
                node = self.getValuePolicy().getNode()
                if node != NodegraphAPI.GetRootNode():
                    self.custom_menu = ParametersMenuButton(node=self.getValuePolicy().getNode())
                    widget.addWidget(self.custom_menu)

        except AttributeError:
            pass
    # Node2DGroupFormWidget
    QT4FormWidgets.GroupFormWidget.originalShowPopdown(self, value)


def installCustomParametersMenu():
    # backup show popdown...
    QT4FormWidgets.GroupFormWidget.originalShowPopdown = QT4FormWidgets.GroupFormWidget.showPopdown

    # patch
    QT4FormWidgets.GroupFormWidget.showPopdown = showPopdownWithCustomMenu
