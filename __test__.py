import sys

from qtpy.QtWidgets import QApplication

from cgwidgets.widgets.userInputWidgets import FloatUserInputWidget


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = FloatUserInputWidget()
    w.show()
    sys.exit(app.exec_())