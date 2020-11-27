
from qtpy.QtWidgets import (
    QLabel, QVBoxLayout, QWidget
)

from qtpy.QtCore import Qt, QEvent

from cgwidgets.utils import attrs
from cgwidgets.widgets import TansuModelViewWidget, TansuHeaderListView


try:
    from Katana import UI4
    from Widgets2 import AbstractSuperToolEditor
except (ImportError, ModuleNotFoundError) as e:
    pass


#class TansuStackEditor(AbstractSuperToolEditor):
    # def __init__(self, parent, node):
    #     super(TansuStackEditor, self).__init__(parent, node)
class TansuStackEditor(QWidget):
    """
    The top level widget for the editor.  This is here to encapsulate
    the main widget with a stretch box...

    Attributes:
        should_update (bool): determines if this tool should have
            its GUI updated or not during the next event idle process.

    """
    def __init__(self, parent, node):
        super(TansuStackEditor, self).__init__(parent)
        # set up attrs
        self.__node = node
        self._node_type = "<multi>"
        # setup layout
        QVBoxLayout(self)
        self.layout().setAlignment(Qt.AlignTop)

        main_widget = TansuStackMainWidget(self)

        for x in range(3):
            name = '<title {}>'.format(str(x))
            main_widget.insertTansuWidget(x, column_data={'name': name})

        self.layout().addWidget(main_widget)
        #self.insertResizeBar()

    """ PROPERTIES """
    def nodeType(self):
        return self._node_type

    def setNodeType(self, _node_type):
        self._node_type = _node_type

class TansuStackMainWidget(TansuModelViewWidget):
    def __init__(self, parent=None):
        super(TansuStackMainWidget, self).__init__(parent)
        view = TansuStackViewWidget(self)
        # setup header
        self.setHeaderWidget(view)
        self.setHeaderPosition(attrs.WEST)
        self.setHeaderData(['name', 'test', 'three'])

        # set dynamic
        self.setDelegateType(
            TansuModelViewWidget.DYNAMIC,
            dynamic_widget=TansuStackDynamicWidget,
            dynamic_function=TansuStackDynamicWidget.updateGUI
        )


class TansuStackViewWidget(TansuHeaderListView):
    def __init__(self, parent=None):
        super(TansuStackViewWidget, self).__init__(parent)


class TansuStackDynamicWidget(QWidget):
    """
    Simple example of overloaded class to be used as a dynamic widget for
    the TansuModelViewWidget.
    """
    def __init__(self, parent=None):
        super(TansuStackDynamicWidget, self).__init__(parent)
        QVBoxLayout(self)
        self.label = QLabel('init')
        self.layout().addWidget(self.label)

    @staticmethod
    def updateGUI(parent, widget, item):
        """
        widget (TansuModelDelegateWidget)
        item (TansuModelItem)
        """
        if item:
            print ('----------------------------')
            print(parent, widget, item)
            name = parent.model().getItemName(item)
            widget.setName(name)
            widget.getMainWidget().label.setText(name)


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QLabel, QVBoxLayout
    from qtpy.QtGui import QCursor
    from cgwidgets.widgets import TansuModelViewWidget
    app = QApplication(sys.argv)

    w = TansuStackEditor(None, None)
    w.resize(500, 500)

    w.show()
    w.move(QCursor.pos())
    sys.exit(app.exec_())