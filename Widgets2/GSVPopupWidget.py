""" Todo:
        * Create new GSV with header
        * Rename GSVs
"""

from qtpy.QtCore import Qt

from cgwidgets.widgets import FrameInputWidgetContainer, LabelledInputWidget, ListInputWidget
from Utils2 import gsvutils


class GSVPopupWidget(FrameInputWidgetContainer):
    def __init__(self, parent=None):
        super(GSVPopupWidget, self).__init__(parent)
        self.setDirection(Qt.Vertical)
        self.setTitle("GSV")
        self.setIsHeaderShown(True)
        self.setIsHeaderEditable(True)
        self._widgets = {}

    def showEvent(self, event):
        self.update()
        return FrameInputWidgetContainer.showEvent(self, event)

    def update(self):
        self._widgets = {}
        self.clearInputWidgets()
        self.populate()

    def createGSVParamWidget(self, param):
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

    def populate(self):
        """ Adds all of the labelled widgets to this frame"""
        gsv_params = gsvutils.getAllGSV(return_as=gsvutils.PARAMETER)
        for gsv_param in gsv_params:
            gsv_param_widget = self.createGSVParamWidget(gsv_param)

            input_widget = LabelledInputWidget(name=gsv_param.getName(), delegate_widget=gsv_param_widget)
            input_widget.setDefaultLabelLength(100)
            input_widget.setDirection(Qt.Horizontal)

            # add to group layout
            self.addInputWidget(input_widget)