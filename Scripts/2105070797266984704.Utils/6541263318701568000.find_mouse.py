from PyQt5 import QtWidgets, QtCore, QtGui
from Katana import UI4
'''

forward = 16
back = 8
b = UI4.App.Tabs.FindTopTab('Node Graph')
b._NodegraphPanel__navigationToolbar._NavigationToolbar__backButtonClicked()
b._NodegraphPanel__navigationToolbar._NavigationToolbar__forwardButtonClicked()
'''
class RegisterMouse(QtWidgets.QWidget):
    def __init__(self,parent=None):
        super(RegisterMouse,self).__init__(parent)

    def mousePressEvent(self, event, *args, **kwargs):
        print(event.button())
        return QtWidgets.QWidget.mousePressEvent(self, event, *args, **kwargs)

    def checkTab(self):
        tabs = UI4.App.Tabs.GetAllTabs()
        visible_tab_list = []
        for tab in tabs:
            if tab.underMouse() == True:
                return tab
a = RegisterMouse()
a.show()