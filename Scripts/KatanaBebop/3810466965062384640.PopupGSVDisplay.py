from qtpy.QtWidgets import QWidget, QComboBox, QHBoxLayout, QVBoxLayout, QMenu
from qtpy.QtCore import Qt

from cgwidgets.utils import centerWidgetOnCursor

from Katana import UI4, NodegraphAPI

"""
NAME: GSV Popup
ICON: icon.png
KEYBOARD_SHORTCUT: Alt+Shift+Q
SCOPE:
Opens a Graph State Variables editor

"""

class GsvComboBox(QComboBox):
    def __init__(self, parent, gsv_param):
        super(GsvComboBox, self).__init__(parent)
        self._param = gsv_param
        self._gsv = gsv_param.getName()
        self.populate()
        self.setMinimumWidth(300)
        self.parent().setFixedWidth(300)
        self.parent().updateGeometry()
        self.currentIndexChanged.connect(self.updateGSV)

    def param(self):
        return self._param

    def gsv(self):
        return self._gsv

    def populate(self):
        for child in self.param().getChild('options').getChildren():
            self.addItem( child.getValue(0))
        
        value = self.param().getChild('value').getValue(0)
        index = self.findText(str(value), Qt.MatchFixedString)

        if index >= 0:
            self.setCurrentIndex(index)
            
    def updateGSV(self):
        param = NodegraphAPI.GetRootNode().getParameter('variables.%s.value'%self.gsv())
        param.setValue(str(self.currentText()), 0)

# create main window
parent = UI4.App.MainWindow.CurrentMainWindow()
variables_param = NodegraphAPI.GetNode('rootNode').getParameter('variables')
variables_param_policy = UI4.FormMaster.CreateParameterPolicy(None, variables_param)
main_widget = QMenu(parent)
main_layout = QVBoxLayout()

# create individual GSV Parameter widgets
for child_policy in variables_param_policy.getChildren():
    param = child_policy.getParameter()
    param_policy = UI4.FormMaster.CreateParameterPolicy(None, child_policy._BaseParameterPolicy__param)
    form_widget = UI4.FormMaster.KatanaFactory.ParameterWidgetFactory.buildWidget(None, param_policy)

    form_widget.layout().itemAt(0).itemAt(3).setParent(None)
    f = form_widget.layout().itemAt(0).itemAt(2).itemAt(0)
    b = f.widget()
    b.setParent(None)

    hbox = QHBoxLayout()
    hbox.addWidget(form_widget)

    blah = QWidget()
    combobox = GsvComboBox(blah, param)
    hbox.addWidget(blah)
    main_layout.addLayout(hbox)

print("dodafff")

main_widget.setAttribute(Qt.WA_NoSystemBackground)
main_widget.setWindowFlags(main_widget.windowFlags() | Qt.FramelessWindowHint)
main_widget.setAttribute(Qt.WA_TranslucentBackground)
main_widget.setStyleSheet("background-color:rgba(50,50,50, 200);")

main_widget.setLayout(main_layout)
from qtpy.QtGui import QCursor
main_widget.popup(QCursor.pos())
#main_widget.show()
#centerWidgetOnCursor(main_widget)


