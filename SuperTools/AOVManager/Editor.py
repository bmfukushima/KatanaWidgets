from qtpy.QtWidgets import QVBoxLayout, QLabel, QWidget
from qtpy.QtCore import Qt

from cgwidgets.widgets import ShojiModelViewWidget
from cgwidgets.settings import attrs

# from Widgets2 import AbstractSuperToolEditor
#

# # class AOVManagerEditor(AbstractSuperToolEditor):
# class AOVManagerEditor(AbstractSuperToolEditor):
#     def __init__(self, parent, node):
#         super(AOVManagerEditor, self).__init__(parent, node)
#
#         # setup layout
#         QVBoxLayout(self)
#         for x in range(5):
#             self.layout().addWidget(QLabel(str(x)))
#         self.layout().setAlignment(Qt.AlignTop)
#         #self.insertResizeBar()

class AbstractAOVManagerEditor(QWidget):
    def __init__(self, parent=None):
        super(AbstractAOVManagerEditor, self).__init__(parent)
        QVBoxLayout(self)

        self._aov_manager = AOVManager()
        self._aov_manager

        self.layout().addWidget(self._aov_manager)


class AOVManager(ShojiModelViewWidget):
    """ Main display for showing the user the current AOV's available to them."""
    AOV = 0
    GROUP = 1
    def __init__(self, parent=None):
        super(AOVManager, self).__init__(parent)
        self.setHeaderPosition(attrs.WEST)

    def createNewAOVGroup(self):
        group_name = "NEW AOV GROUP"
        column_data = {"name": group_name, "type": AOVManager.AOV}
        new_index = self.insertShojiWidget(self.rootItem().childCount(), column_data=column_data, widget=widget)

    def createNewAOV(self):
        aov_name = "NEW AOV"
        column_data = {"name": aov_name, "type": AOVManager.AOV}
        new_index = self.insertShojiWidget(self.rootItem().childCount(), column_data=column_data, widget=widget)


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication
    from cgwidgets.utils import centerWidgetOnScreen

    app = QApplication(sys.argv)
    widget = AbstractAOVManagerEditor()
    widget.show()
    centerWidgetOnScreen(widget)
    sys.exit(app.exec_())