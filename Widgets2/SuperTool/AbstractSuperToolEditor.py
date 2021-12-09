"""
KatanaWindow --> mainWindow
    | -- LayoutWidget
        | -- LayoutFrame
            | -- QStackedWidget --> qt_tabwidget_stackedwidget
                | -- TabWithTimeLine
                    | -- ParameterPanel --> ParametersTab
                        | -- PanelScrollArea
                            | -- QWidget --> qt_scrollarea_viewport
                                | -- QWidget
                                    | -- NodeGroupFormWidget
                                        | -- QWidget --> popdown
                                            | -- ParameterFormWidget

"""

from qtpy.QtWidgets import (
    QWidget, QStackedLayout, QTabWidget, QVBoxLayout
)
from qtpy.QtCore import QEvent, Qt

from cgwidgets.utils import getWidgetAncestor

from Utils2 import paramutils

try:
    from Katana import UI4
    from UI4.Widgets import PanelScrollArea
except ModuleNotFoundError:
    pass


class AbstractSuperToolEditor(QWidget):
    """ Custom Super Tool widget that will hold all of the base functionality
    for the rest of the supertools to inherit from.  This includes the

    * Auto Resizing
        Forces all widgets to automatically constrain to the correct dimensions
        inside of the parameters pane.
    Attributes:
        isFrozen (bool): determines if the event handlers are frozen or not.
        is_auto_resize_enabled (bool): determines if auto resize will occur on show/resize/etc
        node (node): the current node
    """
    def __init__(self, parent, node):
        super(AbstractSuperToolEditor, self).__init__(parent)
        self._is_frozen = False
        self._node = node
        self._is_auto_resize_enabled = True

        # set up resizing events
        self.__resizeEventFilter = ResizeFilter(self)
        self.installResizeEventFilter()

    """ GET KATANA WIDGETS """
    @staticmethod
    def getKatanaQtScrollAreaViewport(widget):
        """
        Returns the params widget that is central widget of the scroll area
        so that we can properly set width/height.
        """
        if widget:
            if widget.objectName() == "qt_scrollarea_viewport":
                return widget
            else:
                return AbstractSuperToolEditor.getKatanaQtScrollAreaViewport(widget.parent())
        else:
            return None

    # @staticmethod
    # def getKatanaWidgetByObjectName(widget, object_name):
    #     """
    #     Searchs up the Katana widget hierarchy to find the one with the given name
    #
    #     If no widget is found, returns None
    #
    #     Args:
    #         widget (QWidget): to start searching from
    #         object_name (str): string of widget.objectName() to search for
    #     """
    #     if not widget: return
    #     if widget.objectName() == object_name:
    #         return widget
    #     else:
    #         return AbstractSuperToolEditor.getKatanaWidgetByObjectName(widget.parent(), object_name)

    """ UTILS """
    def installResizeEventFilter(self):
        """ Installs the event filter in charge of handling the resize events"""
        scroll_area_widget = AbstractSuperToolEditor.getKatanaQtScrollAreaViewport(self)
        self.setIsAutoResizeEnabled(True)
        if scroll_area_widget:
            scroll_area_widget.parent().parent().installEventFilter(self.__resizeEventFilter)
            self.setFixedHeight(scroll_area_widget.height())
            self.setScrollBarPolicy(Qt.Horizontal, Qt.ScrollBarAlwaysOff)

    def removeResizeEventFilter(self):
        """ Removes the event filter in charge of the resize events"""
        self.setIsAutoResizeEnabled(False)
        scroll_area_widget = AbstractSuperToolEditor.getKatanaQtScrollAreaViewport(self)
        if scroll_area_widget:
            scroll_area_widget.parent().parent().removeEventFilter(self.__resizeEventFilter)

    def getParametersPanel(self):
        panel_scroll_area = getWidgetAncestor(self, PanelScrollArea)
        return panel_scroll_area.parent()

    def updateSize(self):
        """
        Updates the size of the GUI to match that of the parameters pane...
        no more of these random af scroll bars everywhere.

        # todo automatic size updates
        # horizontal scrollbar disabled in __init__
        # need to track all of these down... hard coded right now
            height =
                hscrollbar.height()
                + margins.top()
                + margins.bottom()
                + frame.height()
            width =
                vscrollbar.width()
                + margins.left()
                + margins.right()
        """
        if not self.isAutoResizeEnabled(): return

        # get attrs
        viewport = AbstractSuperToolEditor.getKatanaQtScrollAreaViewport(self)
        scrollarea = viewport.parent()
        vertical_scrollbar = scrollarea.verticalScrollBar()
        horizontal_scrollbar = scrollarea.horizontalScrollBar()

        # get dimensions
        margins = 5
        width = viewport.width() - margins
        height = viewport.height() - margins - 50
        if vertical_scrollbar.isVisible():
            width -= vertical_scrollbar.width()
        #
        # if horizontal_scrollbar.isVisible():
        #     height -= horizontal_scrollbar.height()

        # set size
        self.setFixedWidth(width)

        if self.height() < height:
            self.setFixedHeight(height)

    def setScrollBarPolicy(self, direction, scrollbar_policy):
        if direction not in [Qt.Vertical, Qt.Horizontal]: return

        viewport = AbstractSuperToolEditor.getKatanaQtScrollAreaViewport(self)
        scrollarea = viewport.parent()

        # enable scroll bar
        if direction == Qt.Vertical:
            scrollarea.setVerticalScrollBarPolicy(scrollbar_policy)
        elif direction == Qt.Horizontal:
            scrollarea.setHorizontalScrollBarPolicy(scrollbar_policy)

        # disable scroll bar

    def insertResizeBar(self, layout=None, index=None):
        """
        Inserts a resize bar widget to the specified index in the specified layout
        """
        # get defaults
        if not layout:
            layout = self.layout()
        if not index:
            index = self.layout().count()

        # insert resize bar
        self._resize_bar_widget = UI4.Widgets.VBoxLayoutResizer(self)
        layout.insertWidget(index, self._resize_bar_widget)

    """ REGISTER CUSTOM PARM"""
    def createCustomParam(self, widget, param_loc, data_type, get_new_value_function, editing_finished_function, initial_value=0):
        """
        Creates a custom parameter based off of a custom PyQt widget.

        Args:
            param_loc (str): path to location of the parameter with . syntax
                ie user.some_group.param
            data_type (iParameter.TYPE): Data type from the iParameter
                class.
            widget (AbstractBaseInputWidget): The widget type to be converted into a "param"
                This does not really support a lot right now... working on getting
                the triggers working....
                Note:
                    This needs to be of the BaseInputType from CGWidgets
            get_new_value_function (function): function that should return the new
                value that the parameter should be set to.
            editing_finished_function (function): function that is run when the user
                has finished editing the widget...
                Note:
                    This function should take the args (widget, value)
            initial_value: initial value to set the param to

        """

        # check to see if parameter exists
        if self.node().getParameter(param_loc):
            param = self.node().getParameter(param_loc)
        else:
            param = paramutils.createParamAtLocation(param_loc, self.node(), data_type, initial_value=initial_value)

        # set widget attrs
        widget.setLocation(param_loc)
        widget.setDataType(data_type)
        widget.setParameter(param)
        widget.setGetNewValueFunction(get_new_value_function)
        widget.setUserFinishedEditingEvent(editing_finished_function)

        return param

    def createKatanaParam(self, name, parent=None):
        if not parent:
            parent = self.node().getParameters()

        locationPolicy = UI4.FormMaster.CreateParameterPolicy(None, parent.getChild(name))
        factory = UI4.FormMaster.KatanaFactory.ParameterWidgetFactory
        w = factory.buildWidget(self, locationPolicy)

        return w

    # def __getCurrentParentParamFromLoc(self, location):
    #     """
    #     Simple interface to get the current parent parameter group from the location.
    #     If there is no parent, then it will use the getParameters() in Katana
    #     to gather the invisible root...
    #
    #     This should not include the actual parameter path itself, and if the parameter
    #     is at the top most level, then it should provide a blank string...
    #
    #     Args:
    #         location (str): path to location of the parameter with . syntax
    #             ie user.somegroup.param
    #                 would run .getParameter('user.somegroup')
    #
    #     """
    #     if location:
    #         param = self.node().getParameter(location)
    #     else:
    #         param = self.node().getParameters()
    #     return param
    #
    # def __setParam(self, event_signal):
    #     # ????
    #     event_signal()
    #     self.node().setParameter()
    #     pass

    # def undoParam(self):
    #     # ????
    #     pass

    def getCustomParamDict(self):
        return self._custom_param_dict

    """ PROPERTIES """
    def node(self):
        return self._node

    def setNode(self, node):
        self._node = node

    def isFrozen(self):
        return self._is_frozen

    def setIsFrozen(self, is_frozen):
        self._is_frozen = is_frozen

    def isAutoResizeEnabled(self):
        return self._is_auto_resize_enabled

    def setIsAutoResizeEnabled(self, enabled):
        self._is_auto_resize_enabled = enabled

    def resizeBarWidget(self):
        return self._resize_bar_widget

    """ EVENTS """
    def setupEventHandlers(self, bool):
        """ Interface to determine where the event handlers will be setup. """
        pass

    def hideEvent(self, event):
        self.setupEventHandlers(False)
        self.setIsFrozen(True)
        return QWidget.hideEvent(self, event)

    def showEvent(self, event):
        self.setupEventHandlers(True)
        self.setIsFrozen(False)
        self.updateSize()

        return QWidget.showEvent(self, event)


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
            # return True
        return False
        #return super(ResizeFilter, self).eventFilter(obj, event)


class iParameter(object):
    """
    Todo:
        move this into param utils
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
    STRING = 0
    NUMBER = 1
    GROUP = 2
    NUMBER_ARRAY = 3
    STRING_ARRAY = 4

    def __init__(self):
        self._location = ''

    """ TRIGGER """
    def getNewValue(self):
        value = self.__getNewValue()
        return value

    def setGetNewValueFunction(self, function):
        self.__getNewValue = function

    # def finishedEditing(self):
    #     """
    #     Wrapper to set the parameter
    #     """
    #     self.__finished_editing()
    #     new_value = self.__getNewValue
    #     self.setValue(new_value)
    #
    # def setEditingFinishedFunction(self, function):
    #     self.__finished_editing = function

    """ PROPERTIES """
    def getValue(self):
        return self.getParameter().getValue(0)

    def setValue(self, value, frame=0):
        self.getParameter().setValue(value, frame)

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

