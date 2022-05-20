from qtpy.QtWidgets import QLabel, QWidget, QVBoxLayout
from qtpy.QtGui import QCursor, QFont
from qtpy.QtCore import Qt

from Katana import UI4

from cgwidgets.utils import setAsTool, centerWidgetOnCursor

katana_main = UI4.App.MainWindow.CurrentMainWindow()

widget = QWidget(katana_main)
widget.setWindowFlags(widget.windowFlags() | Qt.Tool)
QVBoxLayout(widget)
label = QLabel("Hello")

widget.layout().addWidget(label)

widget.show()
# widget.resize(500,500)

label.setFont(QFont('Arial', 300))
centerWidgetOnCursor(widget)
#label.setStyleSheet("border: 2px solid rgba(128, 128, 128, 255);")