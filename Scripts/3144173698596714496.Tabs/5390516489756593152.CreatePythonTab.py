class PythonWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(PythonWidget, self).__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)
        python_tab = UI4.App.Tabs.CreateTab('Python', None)

        layout.addWidget(python_tab)

        widget = python_tab.getWidget()
        python_widget = widget._pythonWidget
        script_widget = python_widget._FullInteractivePython__scriptWidget
        self.command_widget = script_widget.commandWidget()

    def getCommandWidget(self):
        return self.command_widget

widget = PythonWidget()
file_path = "/media/ssd02/dev/katana/KatanaResources_old/Scripts/scripts/1101951632188788352.SceneGraph/90387519.placeNode.py"
current_file = open('%s' % (file_path), 'r')
text_list = current_file.readlines()
text = ''.join(text_list)
widget.getCommandWidget().setPlainText(text)
current_file.close()
widget.show()