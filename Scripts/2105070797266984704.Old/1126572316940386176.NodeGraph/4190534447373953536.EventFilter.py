class asdf(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(asdf, self).__init__(parent)
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress:
            print "press"
        elif event.type() == QtCore.QEvent.KeyRelease:
            print ('release')
        return True
    

f = asdf()

ng = UI4.App.Tabs.FindTopTab('Node Graph')
ng.installEventFilter(f)
