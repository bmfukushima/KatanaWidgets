""" Creates a new popup widget

This widget can be triggered by giving this script a hotkey

Then setting the relevant hotkey/modifers in "hide_hotkey", and "hide_modifiers".
Note that this step is not necessary, as the hide_hotkey/modifiers is merely
a key combination to close the widget, and the widget will show based off of the
hotkey that is given to this script.
"""

from qtpy.QtWidgets import QLabel
from qtpy.QtCore import QSize, Qt
from Widgets2 import PopupWidget

if not PopupWidget.doesPopupWidgetExist("popupParameters"):
    # create popup widget
    widget = QLabel("test")
    """ constructPopupWidget takes 2 args, and 3 kwargs
        name (str): internal name to display
        widget (QWidget): widget to be displayed
        size (QSize): Display size of the widget
        hide_hotkey (Qt.Key): When pressed in combination with the "hide_modifier"
            the widget will close
        hide_modifier (Qt.Modifier): When pressed in combination with the "hide_hotkey"
            the widget will close
    """
    popup_widget = PopupWidget.constructPopupWidget(
        "test",
        widget,
        size=QSize(512, 512),
        hide_hotkey=Qt.Key_E,
        hide_modifiers=Qt.AltModifier
    )

# hide/show popup parameters
widget = PopupWidget.getPopupWidget("test")
widget.setIsPinned(True)
PopupWidget.togglePopupWidgetVisibility("test")