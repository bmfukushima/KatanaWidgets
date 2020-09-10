from PyQt5.QtWidgets import (
    QWidget, QStackedWidget, QTabWidget, QVBoxLayout, QLabel
)
from PyQt5.QtCore import QEvent

# local import... because PYTHONPATH is not registered yet
from .AbstractSuperToolEditor import AbstractSuperToolEditor

from Katana import UI4


class TwoFacedSuperToolWidget(AbstractSuperToolEditor):
    """
    This is the top level layout that encompasses all of the super tools
    in the which will have two faces, design, and use.  The design portion
    of the layout can have more faces as well ( custom tab ).  The design
    portion at a bare minimum should always have the tab for creating a GUI
    for the user.


    TwoFacedWidget
    VBox
        |-- QStackedWidget
        |       |-- DesignWidget ( CustomTab )
        |               |-- User Params ( Create GUI)
        |               |-- Triggers ( Setup Signals )
        |               |-- Node Edit ( Nodegraph / params )
        |       |-- UseWidget ( QWidget )
        |-- Resizer

    TODO:
        *   Get toggle button into wrench icon
                --> Edit user parameters toggle?
    """
    def __init__(self, parent, node):

        super(TwoFacedSuperToolWidget, self).__init__(parent, node)
        QVBoxLayout(self)

        self.main_widget = QStackedWidget(self)
        self._design_widget = TwoFacedDesignWidget(self)
        self._view_widget = TwoFacedViewWidget(self)
        resize_widget = UI4.Widgets.VBoxLayoutResizer(self)

        self.main_widget.addWidget(self._design_widget)
        self.main_widget.addWidget(self._view_widget)

        self.layout().addWidget(self.main_widget)
        self.layout().addWidget(resize_widget)

    """ PROPERTIES ( WIDGET )"""
    def getDesignWidget(self):
        return self._design_widget

    def setDesignWidget(self, design_widget):
        self._design_widget = design_widget

    def getViewWidget(self):
        return self._view_widget

    def setViewWidget(self, view_widget):
        self._view_widget = view_widget


class TwoFacedDesignWidget(QTabWidget):
    def __init__(self, parent=None):
        super(TwoFacedDesignWidget, self).__init__(parent)


class TwoFacedViewWidget(QWidget):
    def __init__(self, parent=None):
        super(TwoFacedViewWidget, self).__init__(parent)
        QVBoxLayout(self)
        self.layout().addWidget(QLabel('View Widget'))


class ResizeFilter(QWidget):
    """
    Event filter for auto resizing the GUI
    """
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Resize:
            """
            This is a horrible function that is going to implode later...
            but removes the horrid fixed size of the params pane which
            drives me borderline insane.
            """
            # widget below the scroll area...
            self.parent().updateSize()
            return True
        return super(ResizeFilter, self).eventFilter(obj, event)


class iParameter(object):
    """
    Parameter interface to register custom parameters.  The methods
    setEditingFinishedFunction() and setNewGetValueFunction() MUST
    be overloaded to make this work...

    This should be used with multiple inheritance when creating widgets
    ie class MyParam(QWidget, iParameter):

    Attributes:
        location (str): path to location of the parameter with . syntax
                ie user.somegroup.param
        parameter (parameter): Katana parameter that this widget should
            be linking to
        data_type (iParameter.TYPE): Data type from the iParameter
            class.
    """
    INT = 0
    STRING = 1
    def __init__(self):
        self._location = ''

    """ TRIGGER """
    def getNewValue(self):
        value = self.__getNewValue()
        return value

    def setGetNewValueFunction(self, function):
        self.__getNewValue = function

    def finishedEditing(self):
        """
        Wrapper to set the parameter
        """
        self.__finished_editing()
        new_value = self.__getNewValue
        self.setValue(new_value)

    def setEditingFinishedFunction(self, function):
        self.__finished_editing = function

    """ PROPERTIES """
    def getValue(self):
        return self.getParameter().getValue(0)

    def setValue(self, value):
        self.getParameter().setValue(value, 0)

    def getDataType(self):
        return self._data_type

    def setDataType(self, data_type):
        self._data_type = data_type

    def getLocation(self):
        return self._location

    def setLocation(self, location):
        self._location = location

    def getParameter(self):
        return self._parameter

    def setParameter(self, parameter):
        self._parameter = parameter

