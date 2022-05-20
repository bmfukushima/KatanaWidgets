#scaleResolution, getFontSize, GSVPopupWidget, PopupWidget, iColor
from Katana import NodegraphAPI

from qtpy.QtCore import QPoint, QSize, Qt
from qtpy.QtGui import QCursor

from cgwidgets.utils import scaleResolution
from cgwidgets.settings import iColor
from Widgets2 import PopupWidget, GSVPopupWidget
from Utils2 import getFontSize


if not PopupWidget.doesPopupWidgetExist("popupGSV"):
    # create popup widget
    widget = GSVPopupWidget()
    width = getFontSize() * 53
    height = getFontSize() * 70.5
    size = scaleResolution(QSize(width, height))
    popup_widget = PopupWidget.constructPopupWidget(
        "popupGSV", widget, size=size, hide_hotkey=Qt.Key_S, hide_modifiers=Qt.ShiftModifier)
    # setup style
    rgba_border = iColor["rgba_selected"]
    popup_widget.setStyleSheet(f"""
        QWidget#PopupWidget{{
            border: 1px solid rgba{rgba_border};
        }}
    """)

# hide/show popup parameters
widget = PopupWidget.getPopupWidget("popupGSV")
widget.setHideOnLeave(True)
pos = QPoint(
    QCursor.pos().x(),
    QCursor.pos().y() + widget.height() * 0.25

)

PopupWidget.togglePopupWidgetVisibility("popupGSV", pos=pos)

widget.update()

# update display
num_gsvs = len(NodegraphAPI.GetNode('rootNode').getParameter('variables').getChildren())

width = getFontSize() * 40
#height = getFontSize() * 3 * (num_gsvs) + (getFontSize() * 4)
height = getFontSize() * 3 * (num_gsvs + 1) + (getFontSize() * 4) + 10
size = scaleResolution(QSize(width, height))
widget.setFixedSize(size)

# todo figure out why mask doesn't update on scene load until GSV is created/deleted...
# set popup widget style
widget.setIsMaskEnabled(False)
offset = scaleResolution(getFontSize() * 2)
widget.setContentsMargins(0, 0, 0, 0)
widget.layout().setContentsMargins(0, 0, 0, 0)
widget.centralWidget().setContentsMargins(offset, offset, offset, offset)

# widget.setMaskSize(QSize(width, height * 2))
# widget.setContentsMargins(0, 0, 0, 0)
# widget.layout().setContentsMargins(0, 0, 0, 0)
# offset_x = scaleResolution(getFontSize() * 4.5)
# offset_y = scaleResolution(getFontSize() * 2)
# widget.centralWidget().setContentsMargins(offset_x, offset_y, offset_x, offset_y)

