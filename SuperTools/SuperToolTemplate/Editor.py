
from qtpy.QtWidgets import (
    QLabel, QVBoxLayout, QWidget
)

from qtpy.QtCore import Qt, QEvent

from cgwidgets.settings import attrs
from cgwidgets.widgets import ShojiModelViewWidget
from cgwidgets.views import AbstractDragDropListView

from Katana import UI4
from Widgets2 import AbstractSuperToolEditor


class SuperToolEditor(AbstractSuperToolEditor):
    def __init__(self, parent, node):
        super(SuperToolEditor, self).__init__(parent, node)
        # Use this initializer for local shenanigans
        # class SuperToolEditor(QWidget):
        #     """
        #     The top level widget for the editor.  This is here to encapsulate
        #     the main widget with a stretch box...
        #
        #     Attributes:
        #         should_update (bool): determines if this tool should have
        #             its GUI updated or not during the next event idle process.
        #
        #     """
        #     def __init__(self, parent, node):
        #         super(SuperToolEditor, self).__init__(parent)
        # set up attrs
        self.__node = node
        self._node_type = ""
        # setup layout
        QVBoxLayout(self)
        """TODO BUG for some reason setting the layout alignment breaks
        katanas internal resize bar"""
        #self.layout().setAlignment(Qt.AlignTop)

        main_widget = SuperToolMainWidget(self)

        for x in range(3):
            name = '<title {}>'.format(str(x))
            main_widget.insertShojiWidget(x, column_data={'name': name})

        self.layout().addWidget(main_widget)
        self.insertResizeBar()

    """ PROPERTIES """
    def nodeType(self):
        return self._node_type

    def setNodeType(self, _node_type):
        self._node_type = _node_type


class SuperToolMainWidget(ShojiModelViewWidget):
    def __init__(self, parent=None):
        super(SuperToolMainWidget, self).__init__(parent)
        # view = SuperToolViewWidget(self)
        # setup header
        # self.setHeaderViewWidget(view)
        self.setHeaderPosition(attrs.WEST, attrs.NORTH)
        self.setHeaderData(['name', 'test', 'three'])

        # set dynamic
        self.setDelegateType(
            ShojiModelViewWidget.DYNAMIC,
            dynamic_widget=SuperToolDynamicWidget,
            dynamic_function=SuperToolDynamicWidget.updateGUI
        )


class SuperToolViewWidget(AbstractDragDropListView):
    def __init__(self, parent=None):
        super(SuperToolViewWidget, self).__init__(parent)


class SuperToolDynamicWidget(QWidget):
    """
    Simple example of overloaded class to be used as a dynamic widget for
    the ShojiModelViewWidget.
    """
    def __init__(self, parent=None):
        super(SuperToolDynamicWidget, self).__init__(parent)
        QVBoxLayout(self)
        self.label = QLabel('init')
        self.layout().addWidget(self.label)

    @staticmethod
    def updateGUI(parent, widget, item):
        """
        widget (ShojiModelDelegateWidget)
        item (ShojiModelItem)
        """
        if item:
            print ('----------------------------')
            print(parent, widget, item)
            name = parent.model().getItemName(item)
            widget.setName(name)
            widget.getMainWidget().label.setText(name)


if __name__ == "__builtin__":
    import sys
    from qtpy.QtWidgets import QApplication, QLabel, QVBoxLayout
    from qtpy.QtGui import QCursor
    from cgwidgets.widgets import ShojiModelViewWidget
    app = QApplication(sys.argv)
    node = NodegraphAPI.GetAllSelectedNodes()[0]
    w = SuperToolEditor(None, node)
    w.resize(500, 500)

    w.show()
    w.move(QCursor.pos())
    sys.exit(app.exec_())