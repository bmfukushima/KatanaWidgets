class Example(QtWidgets.QWidget):
    def __init__(self,parent=None):
        super(Example,self).__init__(parent)
        NodeGraph = UI4.App.Tabs.FindTopTab('Node Graph')
        self.NodeGraphWidget = NodeGraph._NodegraphPanel__nodegraphWidget
        self.NodeGraphWidget.installEventFilter(self)

    def closeEvent(self, *args, **kwargs):
        self.NodeGraphWidget.removeEventFilter(self)
        return QtWidgets.QWidget.closeEvent(self, *args, **kwargs)

    def eventFilter(self, obj, event, *args, **kwargs):
        #QtCore.QEvent.
        if event.type() == QtCore.QEvent.DragEnter:
            event.acceptProposedAction()
            print('drag enter')
            '''
        elif event.type() == QtCore.QEvent.DragMove:
            event.acceptProposedAction()
            '''
        elif event.type() == QtCore.QEvent.MouseButtonPress:
            print('mouse button press')
        elif event.type() == QtCore.QEvent.MouseButtonRelease:
            print('mouse release event = ', event.pos())
        elif event.type() == QtCore.QEvent.Enter:
            print('enter')
        elif event.type() == QtCore.QEvent.HoverEnter:
            print('hover enter')
            event.accept()
        elif event.type() == QtCore.QEvent.Drop:
            print('drop')

        return QtWidgets.QLabel.eventFilter(self, obj, event, *args, **kwargs)

e = Example()
e.show()
'''

a = UI4.App.Tabs.FindTopTab('Monitor')
mw = a.getMonitorWidget()
class TestFilter(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(TestFilter, self).__init__(parent)
        a = UI4.App.Tabs.FindTopTab('Monitor')
        mw = a.getMonitorWidget()
        mw.installEventFilter(self)
    def eventFilter(self, obj, event, *args, **kwargs):
        #print dir(event)
        #print(event.type())
        if event.type() == QtCore.QEvent.KeyRelease:
            print event.text()
            #print dir(event)
            print 'a'
        return QtWidgets.QWidget.eventFilter(self, obj, event,  *args, **kwargs)

s = TestFilter()
'''