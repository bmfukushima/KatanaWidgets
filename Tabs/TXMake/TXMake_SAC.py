import sys
import os
import platform

from PyQt5.QtWidgets import (
    QWidget,
    QListWidget,
    QLineEdit,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QApplication,
    QFileSystemModel,
    QCompleter,
    QPushButton
)


from PyQt5.QtCore import Qt, QEvent, QDir


from Katana import UI4


def getWidgetAncestor(widget, instance_type):
    """
    Recursively searches up from the current widget
    until an widget of the specified instance is found

    Args:
        widget (QWidget): widget to search from
        instance_type (object): Object type to find
    """

    if isinstance(widget, instance_type):
        return widget
    else:
        parent = widget.parent()
        if parent:
            return getWidgetAncestor(widget.parent(), instance_type)
        else:
            return None


class TXConverterTab(UI4.Tabs.BaseTab):
    """ Main widget for converting textures to Pixars .tx format"""
    NAME = "TXMake"
    EXTENSIONS = (".jpg", ".exr", ".png", ".tga", ".tiff", ".tif")

    def __init__(self, parent=None):
        super(TXConverterTab, self).__init__(parent)

        QVBoxLayout(self)

        # setup directory
        self._directory_layout = QHBoxLayout()
        self._directory_label = QLabel("Directory")
        self._directory_widget = FileBrowserInputWidget()
        self._directory_layout.addWidget(self._directory_label)
        self._directory_layout.addWidget(self._directory_widget)

        # setup list
        self._files_list_widget = FilesListWidget(self)

        # setup convert button
        # self.
        # self._convert_button = QPushButton("Convert")
        # self._convert_button.clicked.connect(self.convertSelection)

        self._convert_button = QPushButton("Convert and Update")
        self._convert_button.setToolTip("""
Will convert all of the textures from the current selection to .tx files
These files will be saved in the same directory, and will have the flags set in the flags box
This will also try and update all of your image paths for every PrmanShadingNode""")
        self._convert_button.clicked.connect(self.convertSelectionAndUpdate)

        # setup directory
        self._flags_layout = QHBoxLayout()
        self._flags_label = QLabel("Flags")
        self._flags_widget = FileBrowserInputWidget()
        self._flags_layout.addWidget(self._flags_label)
        self._flags_layout.addWidget(self._flags_widget)

        self.layout().addLayout(self._directory_layout)
        self.layout().addWidget(self._files_list_widget)
        self.layout().addLayout(self._flags_layout)
        self.layout().addWidget(self._convert_button)

    def convertSelectionAndUpdate(self):
        """ Convert the selection, and update all of the existing texture maps"""
        from Katana import NodegraphAPI
        conversion_map = self.convertSelection()
        # get node list
        for node in NodegraphAPI.GetAllNodesByType("PrmanShadingNode"):
            param = node.getParameter("parameters.filename.value")
            if param:
                if param.getValue(0) in conversion_map.keys():
                    old_path = param.getValue(0)
                    new_path = conversion_map[param.getValue(0)]
                    param.setValue(str(new_path), 0)
                    print("""Updating node {NODE} from:
    {OLD_PATH}
    {NEW_PATH}
""".format(NODE=node.getName(), OLD_PATH=old_path, NEW_PATH=new_path))

    def convertSelection(self):
        """ Converts the current selection in the filesListWidget to tx files based
        on the flags that are given

        Returns (dict): {old_file_path:new_file_path}
        """
        cwd = self.directory()

        # find txmake
        txmake_dir = os.environ["RMANTREE"] + "/bin"
        os.chdir(txmake_dir)

        flags = self.flags()

        conversion_map = {}
        # open subprocess
        for index in self.filesListWidget().selectedIndexes():

            file_orig = index.data()
            file_ext = file_orig[file_orig.rindex('.'):]
            file_name = file_orig[:file_orig.rindex('.')]

            orig_name = os.path.join(cwd, file_orig).replace("\\", "/")
            converted_name = os.path.join(cwd, (file_name + '.tx')).replace("\\", "/")
            conversion_map[orig_name] = converted_name

            cmd = "txmake {FLAGS} {SRC} {DEST}".format(
                FLAGS=flags,
                SRC=orig_name,
                DEST=converted_name
            )
            os.popen(cmd)
            print("Converting {FILEPATH} to .tx".format(FILEPATH=orig_name))

        return conversion_map

    def directory(self):
        return self.directoryWidget().directory()

    def flags(self):
        return self.flagsWidget().text()

    def flagsWidget(self):
        return self._flags_widget

    def directoryWidget(self):
        return self._directory_widget

    def filesListWidget(self):
        return self._files_list_widget


class FilesListWidget(QListWidget):
    """ List of all of the image files in the directory set in the FileBrowserInputWidget"""
    def __init__(self, parent):
        super(FilesListWidget, self).__init__(parent)
        self.setSelectionMode(QListWidget.MultiSelection)

    def updateView(self, directory):
        self.clear()

        for file in os.listdir(directory):
            file_path = "{DIRECTORY}/{FILE}".format(DIRECTORY=directory, FILE=file)

            if file_path.endswith(TXConverterTab.EXTENSIONS):
                self.addItem(file)


class FileBrowserInputWidget(QLineEdit):
    def __init__(self, parent=None):
        super(FileBrowserInputWidget, self).__init__(parent=parent)

        # setup model
        self.model = QFileSystemModel()

        if platform.system() == 'Windows':
            home = os.environ["HOMEPATH"]
        elif platform.system() == 'Linux':
            home = os.environ["HOME"]
        self.model.setRootPath(home)
        filters = self.model.filter()
        self.model.setFilter(filters | QDir.Hidden)

        # setup completer
        completer = QCompleter(self.model, self)
        self.setCompleter(completer)

        self.setCompleter(completer)
        completer.setCaseSensitivity(Qt.CaseInsensitive)

        self.autoCompleteList = []

        # setup events
        self.editingFinished.connect(self.directoryChanged)

    def directory(self):
        return self._directory

    def setDirectory(self, directory):
        self._directory = directory
        main_widget = getWidgetAncestor(self, TXConverterTab)
        main_widget.filesListWidget().updateView(directory)

    def directoryChanged(self, *args):
        directory = self.text()
        if os.path.isdir(directory):
            self.setDirectory(directory)

    def checkDirectory(self):
        directory = str(self.text())
        if os.path.isdir(directory):
            self.model.setRootPath(str(self.text()))

    def event(self, event, *args, **kwargs):
        # I think this is the / key... lol
        if (event.type() == QEvent.KeyRelease) and event.key() == 47:
            self.checkDirectory()
            #self.completer().popup().show()
            self.completer().complete()

        return QLineEdit.event(self, event, *args, **kwargs)


# PluginRegistry = [("KatanaPanel", 2, "TXMake", TXConverterTab)]