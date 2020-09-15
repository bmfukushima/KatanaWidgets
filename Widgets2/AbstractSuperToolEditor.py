from PyQt5.QtWidgets import (
    QWidget, QStackedLayout, QTabWidget, QVBoxLayout
)
from PyQt5.QtCore import QEvent

from cgwidgets.utils import getWidgetAncestor

try:
    from UI4.Widgets import PanelScrollArea
except ModuleNotFoundError:
    pass


class AbstractSuperToolEditor(QWidget):
    """
    Custom Super Tool widget that will hold all of the base functionality
    for the rest of the supertools to inherit from.  This includes the
    * Auto Resizing
        Forces all widgets to automatically constrain to the correct dimensions
        inside of the parameters pane.
    Attributes:
        is_frozen (bool): determines if the event handlers are
            frozen or not.
        node (node): the current node
    """
    def __init__(self, parent, node):
        super(AbstractSuperToolEditor, self).__init__(parent)
        self._is_frozen = False
        self.node = node

        # set up resizing events
        self.__resizeEventFilter = ResizeFilter(self)
        self.getKatanaParamsScrollAreaWidget().parent().parent().installEventFilter(self.__resizeEventFilter)
        self.setFixedHeight(self.getKatanaParamsScrollAreaWidget().height())

    def getKatanaParamsScrollAreaWidget(self):
        """
        Returns the params widget that is central widget of the scroll area
        so that we can properly set width/height.
        """
        return self.parent().parent().parent().parent()

    def setupEventHandlers(self, bool):
        """
        Interface to determine where the event handlers will
        be setup.
        """
        pass

    def hideEvent(self, event):
        self.setupEventHandlers(False)
        self.is_frozen = True
        return QWidget.hideEvent(self, event)

    def showEvent(self, event):
        self.setupEventHandlers(True)
        self.is_frozen = False
        self.updateSize()

        return QWidget.showEvent(self, event)

    """ UTILS """
    def getParametersPanel(self):
        panel_scroll_area = getWidgetAncestor(self, PanelScrollArea)
        return panel_scroll_area.parent()

    def updateSize(self):
        """
        Updates the size of the GUI to match that of the parameters pane...
        no more of these random af scroll bars everywhere.
        """
        # set width
        width = self.getKatanaParamsScrollAreaWidget().width()
        width -= 25
        self.setFixedWidth(width)

        # set height
        height = self.getKatanaParamsScrollAreaWidget().height()
        if self.height() < height:
            self.setFixedHeight(height)

    """ REGISTER CUSTOM PARM"""
    def registerCustomParameter(self, widget, param_loc, data_type, get_new_value_function, editing_finished_function):
        """
        Creates a custom parameter based off of a custom PyQt widget.

        Args:
            param_loc (str): path to location of the parameter with . syntax
                ie user.some_group.param
            data_type (iParameter.TYPE): Data type from the iParameter
                class.
            widget (QWidget): The widget type to be converted into a "param"
                This does not really support a lot right now... working on getting
                the triggers working....
            get_new_value_function (function): function that should return the new
                value that the parameter should be set to.
            editing_finished_function (function): function that is run when the user
                has finished editing the widget...

        """

        # check to see if parameter exists
        if self.node.getParameter(param_loc):
            widget.setLocation(param_loc)
            widget.setDataType(data_type)
            widget.setParameter(self.node.getParameter(param_loc))
            widget.setGetNewValueFunction(get_new_value_function)
            widget.setEditingFinishedFunction(editing_finished_function)
            return

        # get attrs
        param_group = '.'.join(param_loc.split('.')[:-1])
        param_name = param_loc.split('.')[-1]

        # create recursive groups
        if param_group:
            self.createParamHierarchy(param_group)

        # initialize new parameter on node
        parent_param = self.__getCurrentParentParamFromLoc(param_group)
        if data_type == iParameter.INT:
            new_param = parent_param.createChildNumber(param_name, 0)
        elif data_type == iParameter.STRING:
            new_param = parent_param.createChildString(param_name, '')

        # set widget attrs
        widget.setLocation(param_loc)
        widget.setDataType(data_type)
        widget.setParameter(new_param)
        widget.setGetNewValueFunction(get_new_value_function)
        widget.setEditingFinishedFunction(editing_finished_function)
        # widget will have the signalTrigger to send to this...
        # so all custom parms need the new widget as an interface...
        pass

    def createParamHierarchy(self, param_loc):
        """
        Recursively create group params if they don't exist until
        the param location is available?

        Args:
            param_loc (str): path to location of the parameter with . syntax
                ie user.somegroup.param
        """
        param_group = param_loc.split('.')
        for index, location in enumerate(param_group):
            current_location = param_group[:index]
            current_group = self.__getCurrentParentParamFromLoc(current_location)
            current_group.createChildGroup(location)

    def __getCurrentParentParamFromLoc(self, location):
        """
        Simple interface to get the current parent parameter group from the location.
        If there is no parent, then it will use the getParameters() in Katana
        to gather the invisible root...

        This should not include the actual parameter path itself, and if the parameter
        is at the top most level, then it should provide a blank string...

        Args:
            location (str): path to location of the parameter with . syntax
                ie user.somegroup.param
                    would run .getParameter('user.somegroup')

        """
        if location:
            param = self.node.getParameter(location)
        else:
            param = self.node.getParameters()
        return param

    def __setParam(self, event_signal):
        event_signal()
        self.node.setParameter()
        pass

    def undoParam(self):
        # ????
        pass

    def getCustomParamDict(self):
        return self._custom_param_dict

    """ PROPERTIES """
    @property
    def is_frozen(self):
        return self._is_frozen

    @is_frozen.setter
    def is_frozen(self, is_frozen):
        self._is_frozen = is_frozen


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

