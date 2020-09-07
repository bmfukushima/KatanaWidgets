from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QSizePolicy,
)

from PyQt5.QtCore import (Qt)

from Utils2 import suppressUndooz

from Utils2.settings import (
    ACCEPT_GIF,
    CANCEL_GIF,
)

from Utils2.colors import (
    ACCEPT_COLOR_RGBA,
    CANCEL_COLOR_RGBA
)

from .GifPlayer import GifPlayer


class AbstractUserBooleanWidget(QWidget):
    """
    Abstract widget that will require user input of
    Accepting / Canceling the current event that
    is proposed to them.

    The event can be accepted/denied with the buttons
    to the left/right of the widget, or with the esc / enter/return keys.

    Args:
        central_widget (QWidget): Central widget to be displayed
            to the user.  Can also be set with setCentralWidget.
        button_width (int): The width of the accept/cancel buttons.
    Widgets:
        accept_button (QPushButton): When pressed, accepts the
            current event registered with setAcceptEvent.
        cancel_button (QPushButton): When pressed, cancels the
            current event registered with setCancelEvent.
        central_widget (QWidget): The central widget to be displayed
            to the user.
    """
    def __init__(self, parent=None, central_widget=None, button_width=None):
        super(AbstractUserBooleanWidget, self).__init__(parent)
        #self.main_widget = getMainWidget(self)

        # Create main layout
        QHBoxLayout(self)

        # create text layout
        if not central_widget:
            self.central_widget = QWidget()

        # create accept / cancel widgets
        """
        self.accept_button = QPushButton('=>')
        self.cancel_button = QPushButton('<=')
        self.accept_button.clicked.connect(self.acceptPressed)
        self.cancel_button.clicked.connect(self.cancelPressed)
        """
        self.accept_button = GifPlayer(ACCEPT_GIF, hover_color=ACCEPT_COLOR_RGBA)
        self.cancel_button = GifPlayer(CANCEL_GIF, hover_color=CANCEL_COLOR_RGBA)
        self.accept_button.setMousePressAction(self.acceptPressed)
        self.cancel_button.setMousePressAction(self.cancelPressed)

        # setup accept / cancel widgets
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.accept_button.setSizePolicy(size_policy)
        self.cancel_button.setSizePolicy(size_policy)
        self.setupButtonTooltips()

        # set up main layout
        self.layout().addWidget(self.cancel_button, 1)
        self.layout().addWidget(self.central_widget)
        self.layout().addWidget(self.accept_button, 1)

        self.layout().setAlignment(Qt.AlignTop)

        # set default button size
        if not button_width:
            self.setButtonWidth(100)

    def setupButtonTooltips(self):
        """
        Creates the tooltips for the user on how to use these buttons
        when they hover over the widget.
        """
        self.accept_button.setToolTip("""
The happy af dog bouncing around that has a massive
green border around it when you hover over it means to continue.

FYI:
You can also hit <ENTER> and <RETURN> to continue...
        """)
        self.cancel_button.setToolTip("""
The super sad dog who looks really sad with the massive red border
around it when you hover over it means to go back...

FYI:
You can also hit <ESCAPE> to go back...
        """)
        self.setStyleSheet("""
            QToolTip {
                background-color: black;
                color: white;
                border: black solid 1px
            }"""
        )

    def setButtonWidth(self, width):
        """
        Sets the accept/cancel buttons to a fixed width...
        """
        self.accept_button.setFixedWidth(width)
        self.cancel_button.setFixedWidth(width)

    """ PROPERTIES """
    def setCentralWidget(self, central_widget):
        self.layout().itemAt(1).widget().setParent(None)
        self.layout().insertWidget(1, central_widget)
        self.central_widget = central_widget

    def getCentralWidget(self):
        return self.central_widget

    """ EVENTS """
    def setAcceptEvent(self, accept):
        self._accept = accept

    def setCancelEvent(self, cancel):
        self._cancel = cancel

    def acceptPressed(self):
        #self.main_widget.layout().setCurrentIndex(0)
        self._accept()

    def cancelPressed(self):
        #self.main_widget.layout().setCurrentIndex(0)
        suppressUndooz(self._cancel)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.cancelPressed()
        elif event.key() in [Qt.Key_Enter, Qt.Key_Return]:
            self.acceptPressed()
        return QWidget.keyPressEvent(self, event)
