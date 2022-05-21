""" Todo:
        * Create new GSV with header
        * Rename GSVs
"""
from qtpy.QtWidgets import QScrollArea, QWidget, QVBoxLayout
from qtpy.QtCore import QPoint, QSize, Qt
from qtpy.QtGui import QCursor

from Katana import NodegraphAPI

from cgwidgets.utils import scaleResolution, getWidgetAncestor, clearLayout
from cgwidgets.widgets import (
    FrameInputWidgetContainer,
    LabelledInputWidget,
    ListInputWidget,
    OverlayInputWidget,
    ButtonInputWidget)
from cgwidgets.settings import iColor

from Utils2 import gsvutils, getFontSize, getValidName
from Widgets2 import PopupWidget, GSVPopupWidget

WIDTH = getFontSize() * 40

class GSVPopupHeaderWidget(OverlayInputWidget):
    def __init__(self, parent=None):
        super(GSVPopupHeaderWidget, self).__init__(parent)
        delegate_widget = ButtonInputWidget(title="< Create new GSV >", user_clicked_event=self.createNewGSV)
        self.setDelegateWidget(delegate_widget)
        delegate_widget.setMinimumHeight(getFontSize() * 2.5)
        self.setTitle("GSV")
        self.setDisplayMode(OverlayInputWidget.ENTER)

    def createNewGSV(self, widget):
        popup_widget = getWidgetAncestor(self, GSVPopupWidget)
        popup_widget.createNewGSVEvent()


class GSVPopupWidget(FrameInputWidgetContainer):
    """ Main container holding the GSVPopupWidget"""
    def __init__(self, parent=None):
        super(GSVPopupWidget, self).__init__(parent)
        self.setDirection(Qt.Vertical)

        # setup header widget
        header_widget = GSVPopupHeaderWidget()
        self.setHeaderWidget(header_widget)
        self.headerWidget().setFixedHeight(getFontSize() * 3)

    """ UTILS """
    def createGSVParamListWidget(self, param):
        def updateOptions():
            """ Updates the options available to the user"""
            return [[option] for option in gsvutils.getGSVOptions(param.getName())]

        def gsvChanged(widget, value):
            """ Changes the current GSV to the one set by the user"""
            gsv = widget.param.getName()
            option = str(value)
            if gsvutils.isGSVOptionValid(gsv, option):
                gsvutils.setGSVOption(gsv, option)
            else:
                gsvutils.createNewGSVOption(gsv, option)

        gsv_param_widget = ListInputWidget(self)
        gsv_param_widget.filter_results = False
        gsv_param_widget.dynamic_update = True
        gsv_param_widget.param = param
        gsv_param_widget.setCleanItemsFunction(updateOptions)
        gsv_param_widget.setUserFinishedEditingEvent(gsvChanged)

        return gsv_param_widget

    def createGSVParamWidget(self, gsv_param):
        """ Creates a new input widget entry for the GSV Param provided

        Args:
            gsv_param (param):
        """
        gsv_param_widget = self.createGSVParamListWidget(gsv_param)

        input_widget = LabelledInputWidget(name=gsv_param.getName(), delegate_widget=gsv_param_widget)
        input_widget.setViewAsReadOnly(False)
        input_widget.setViewWidgetUserFinishedEditingEvent(self.userChangedGSVNameEvent)
        input_widget.setDefaultLabelLength(100)
        input_widget.setDirection(Qt.Horizontal)
        input_widget.setMinimumHeight(getFontSize() * 3)
        # add to group layout
        self.addInputWidget(input_widget)

        return input_widget

    """ EVENTS"""
    def showEvent(self, event):
        self.update()
        return FrameInputWidgetContainer.showEvent(self, event)

    def update(self):
        self.clearInputWidgets()
        self.populate()

    def createNewGSVEvent(self):
        # create new gsv
        gsv_param = gsvutils.createNewGSV("newGSV", force_create=True)
        gsv_name = gsv_param.getName()

        # add entry
        self.createGSVParamWidget(gsvutils.getGSVParameter(gsv_name))

        # update display
        num_gsvs = len(NodegraphAPI.GetNode('rootNode').getParameter('variables').getChildren())

        spacer_offset = self.layout().spacing() * 2 + self._separator_width
        height = getFontSize() * 3 * (num_gsvs + 1) + (getFontSize() * 4) + spacer_offset + (num_gsvs + 1) * 3
        if 512 < height:
            height = 512
        size = scaleResolution(QSize(WIDTH, height))
        from .PopupWidget import PopupWidget
        popup_widget = getWidgetAncestor(self, PopupWidget)
        popup_widget.setFixedSize(size)

    def userChangedGSVNameEvent(self, widget, new_gsv_name):
        """ Updates the name of a GSV on user event"""
        old_gsv_name = widget.parent().viewWidget().text()
        if old_gsv_name == new_gsv_name: return

        new_name = gsvutils.renameGSV(old_gsv_name, new_gsv_name)
        widget.parent().viewWidget().setText(new_name)

    def populate(self):
        """ Adds all of the labelled widgets to this frame"""
        gsv_params = gsvutils.getAllGSV(return_as=gsvutils.PARAMETER)
        for gsv_param in gsv_params:
            self.createGSVParamWidget(gsv_param)


def toggleGSVPopup():
    if not PopupWidget.doesPopupWidgetExist("popupGSV"):
        # create popup widget
        widget = GSVPopupWidget()
        size = scaleResolution(QSize(WIDTH, 200))
        popup_widget = PopupWidget.constructPopupWidget(
            "popupGSV", widget, size=size, hide_hotkey=Qt.Key_S, hide_modifiers=Qt.ShiftModifier)

    # hide/show popup parameters
    PopupWidget.togglePopupWidgetVisibility("popupGSV")
