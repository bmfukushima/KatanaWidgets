"""
How to use...

Double Click: Assign color to selected nodes
Click : edit current color
Hover: hovering over a color will set the display color of those nodes, leaving that widget will reset the nodes to their original color

Remove Color: drag/drop out of the widget

Add Color (+)
pop up dialog to show colors, all colors are saved in the .katana dir in a file called "color.csv"

Search Bar ( ^ ):
    The search bar will auto select nodes for you based off of the following syntax
    Param Value:
        param{param1=value,param2 =value ,param3 =value } : checks all nodes to see if a param is equal to the value, if so selects...
    Param Exists:
        hasparam{param,param1}
    Name:
        name{name, name, na*}: selects all nodes by name (* wildcard is accepted)
    Node Type:
        type{type1,type3,type2}: selects nodes by type...

    ie:
        so a search could look like:
        name{*Create} type{Group}
        would select all nodes that have *Create in the name, and all nodes that are of type group
"""

import csv
import os
import re

from qtpy.QtWidgets import (
    QWidget,
    QPushButton,
    QLayout,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QSizePolicy,
    QComboBox,
    QCompleter,
    QLabel,
    QMainWindow,
    QApplication,
    QColorDialog
)
from qtpy.QtCore import (
    Qt,
    QSortFilterProxyModel,
    QEvent,
    QMimeData,
    QTimer
)
from qtpy.QtGui import (
    QStandardItemModel,
    QStandardItem,
    QDrag,
    QPixmap
)

from Katana import UI4, NodegraphAPI, KatanaResources, DrawingModule

"""
param{param}
hasparam{param=value}
type{nodeType}
name{node_name}
"""
class MainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.does_exist = True
        self.size = 25
        self.spacing_size = 5
        self.addColorButton = QPushButton("+")
        self.addColorButton.clicked.connect(self.addColor)
        self.addColorButton.setFixedSize(self.size, self.size)
        
        self.addSearchButton = QPushButton("^")
        self.addSearchButton.clicked.connect(self.addSearchBar)
        self.addSearchButton.setFixedSize(self.size, self.size)
        
        self.search_bar = CreateSearchBox()

        self.main_layout = QVBoxLayout()
        self.search_bar_layout = QHBoxLayout()
        
        self.color_grid_widget = QWidget()
        self.color_grid_layout = QGridLayout()
        self.color_grid_widget.setLayout(self.color_grid_layout)
        self.color_grid_layout.setSpacing(self.spacing_size)

        self.color_grid_layout.setSizeConstraint(QLayout.SetFixedSize)

        self.initDefaultColors()

        self.main_layout.addLayout(self.search_bar_layout)
        self.main_layout.addWidget(self.color_grid_widget)
        self.setLayout(self.main_layout)
        self.setDropLocation(False)
        self.setAcceptDrops(True)
        self.populate()
        
    def addSearchBar(self):
        if self.search_bar.getVisibility():
            self.search_bar_layout.removeWidget(self.search_bar)
            self.search_bar.hide()
            self.search_bar.setVisibility(False)
        if not self.search_bar.getVisibility():
            self.search_bar.show()
            self.search_bar_layout.addWidget(self.search_bar)
            self.search_bar.setVisibility(True)

    def resizeEvent(self, event, *args, **kwargs):
        # to avoid recursion, checks for column count and compares to the previous column count
        node_graph = UI4.App.Tabs.FindTopTab("Node Graph")
        layout_width = node_graph.geometry().width()
        init_size = self.spacing_size + self.size
        num_columns = int ( layout_width/init_size )
        if num_columns != self.num_columns:
            self.num_columns = num_columns
            self.populate()
        self.main_layout.setSizeConstraint(QLayout.SetDefaultConstraint)
        
    def getGridSetup(self):
        node_graph = UI4.App.Tabs.FindTopTab("Node Graph")
        layout_width = node_graph.geometry().width()
        widget_list = self.initDefaultColors()
        margin_size = self.spacing_size
        color_label_size = self.size
        init_length = (margin_size + color_label_size) * len(widget_list)
        row_count = int(init_length / layout_width) + 1
        column_count = int(layout_width / (margin_size + color_label_size))
        self.num_columns = column_count
        return row_count, column_count
    
    def populate(self):
        for i in reversed(range(self.color_grid_layout.count())): 
            self.color_grid_layout.itemAt(i).widget().setParent(None)

        row_count, column_count = self.getGridSetup()
        widget_list = self.initDefaultColors()

        for count, label in enumerate(widget_list):
            column = count % column_count
            row = int(count/column_count)
            self.color_grid_layout.addWidget(label, row+1, column, 1, 1)
            self.color_grid_layout.setColumnStretch(column, QSizePolicy.Minimum)

        self.color_grid_layout.setSizeConstraint(QLayout.SetFixedSize)
        
    def initDefaultColors(self,widget=None):
        widget_list = [self.addSearchButton , self.addColorButton]
        publish_loc = KatanaResources.GetUserKatanaPath()
        file_loc = publish_loc + "/color.csv"
        if os.path.exists(file_loc):
            with open(file_loc, "rb") as csvfile:
                color_list = csvfile.readlines()[0].split("|")[:-1]
            for color in color_list:
                color = color.replace("\"", '')
                color = [int(value) for value in color.split(",")]
                widget_list.append(self.createLabel(color))
        if widget:
            widget_list.append(widget)
        return widget_list
    
    def getDropLocation(self):
        return self.drop_location
    
    def setDropLocation(self,location):
        self.drop_location = location
    
    def dragEnterEvent(self, event):
        self.setDropLocation(True)
        event.accept()
        return QWidget.dragEnterEvent(self, event)
    
    def dragLeaveEvent(self, event):
        self.setDropLocation(False)
        event.accept()
        return QWidget.dragLeaveEvent(self, event)

    def addColor(self):
        main_window = MainWindow(self)
        main_window.show()

    def createLabel(self, color):
        label = ColorLabel(color=color)
        label.setStyleSheet("background-color: rgb(%s,%s,%s);" % (color[0], color[1], color[2]))
        label.setFixedSize(self.size, self.size)
        return label
    
    def labelClicked(self, widget):
        label = widget
        selected = label.isSelected()
        if selected:
            label.setStyleSheet("background-color: rgb(%s,%s,%s);" % (label.color[0], label.color[1], label.color[2]))
            label.selected = False
        else:
            label.setStyleSheet("background-color: rgb(%s,%s,%s);       \
                            border-style: inset;               \
                            border-width: 2px;                  \
                            border-radius: 1px;                \
                            border-color: rgb(64,64,64);                \
                            " % (label.color[0], label.color[1], label.color[2]))
            label.selected = True

    def keyPressEvent(self, event, *args, **kwargs):
        if event.key() in [16777219, 16777223]:
            layout = self.color_grid_layout
            for index in range(layout.childCount()):
                label = layout.itemAt(index).widget()
                if hasattr(label, "selected"):
                    if label.isSelected():
                        label.deleteSelf()


class CreateSearchBox(QComboBox):
    """a way to create new nodes inside of the widget itself"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)

        self.completer = QCompleter(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setPopup(self.view())
        self.setCompleter(self.completer)
        
        self.pFilterModel = QSortFilterProxyModel(self)

        self.nodeTypes = [''] + NodegraphAPI.GetNodeTypes()
        self.populate()
        self.visible = False
        
    def setVisibility(self, visibility):
        self.visible = visibility
        
    def getVisibility(self):
        return self.visible
    
    def populate(self):       
        create_new_node_widget = self
        model = QStandardItemModel()
        for i, nodeType in enumerate(self.nodeTypes):
            item = QStandardItem(nodeType)
            model.setItem(i, 0, item)

        create_new_node_widget.setModel(model)
        create_new_node_widget.setModelColumn(0)

    def setModel(self, model):
        super(CreateSearchBox, self).setModel(model)
        self.pFilterModel.setSourceModel(model)
        self.completer.setModel(self.pFilterModel)

    def setModelColumn(self, column):
        self.completer.setCompletionColumn(column)
        self.pFilterModel.setFilterKeyColumn(column)
        super(CreateSearchBox, self).setModelColumn(column)

    def view( self ):
        return self.completer.popup()            

    def selectNodes(self):
        node_list = str(self.currentText()).replace(" ", '').split("}")[:-1]
        for node in NodegraphAPI.GetAllSelectedNodes():
            NodegraphAPI.SetNodeSelected(node, False)
        selection_list = []
        for node in NodegraphAPI.GetAllNodes():
            for text in node_list:
                if "name{" in self.currentText() or "param{" in self.currentText():
                    regex_list = text[text.index("{")+1:].replace("*",".*").split(",")
                    for regex in regex_list:
                        if text[:5] == "name{":
                            if re.match(regex,node.getName()):
                                selection_list.append(node)
                        elif text[:6] == "param{":
                            param, value = regex.split("=")
                            if node.getParameter(param):
                                if str(node.getParameter(param).getValue(0)) == str(value):
                                    selection_list.append(node)
                        elif text[:9] == "hasparam{":
                            if node.getParameter(regex):
                                selection_list.append(node)
        for text in node_list:
            regex_list = text[text.index("{")+1:].replace("*",".*").split(",")
            if text[:5] == "type{":
                for node_type in regex_list:
                    if node_type in self.nodeTypes:
                        selection_list += NodegraphAPI.GetAllNodesByType(node_type)

        for node in selection_list:
            NodegraphAPI.SetNodeSelected(node,True)
            
    def textChanged(self):
        pass
    
    def event(self, event,*args, **kwargs):
        if (event.type() == QEvent.KeyPress) and (event.key() == 16777220 or event.key() == 16777221):
            self.selectNodes()
        
        return QComboBox.event(self, event, *args, **kwargs)


class MainWindow(QMainWindow):
    def __init__(self, parent=None, label=None):
        super().__init__(parent=parent)
        main_widget = QWidget()
        self.label = label
        self.color_picker = ColorDialog(parent=self)
        self.setCentralWidget(self.color_picker)
        layout = QVBoxLayout(main_widget)
        hbox = QHBoxLayout()
        button = QPushButton("add color")
        button.clicked.connect(self.addColor)
        
        button2 = QPushButton("add color (close)")
        button2.clicked.connect(self.addColorAndClose)
        hbox.addWidget(button)
        hbox.addWidget(button2)
        layout.addWidget(self.color_picker)
        
        layout.addLayout(hbox)
        self.setCentralWidget(main_widget)
        self.color = None
        
    def addColor(self):
        self.color = self.color_picker.currentColor().getRgb()
        if not self.label:
            label = self.parent().createLabel(self.color)
            # add to reloadable list...
            publish_loc = KatanaResources.GetUserKatanaPath()
            color = ",".join([str(self.color[0]), str(self.color[1]), str(self.color[2])])
            file_loc = publish_loc + "/color.csv"
            if not os.path.isfile(file_loc):
                open(file_loc, "wb")
            with open(file_loc, "a") as csvfile:
                csv_writer = csv.writer(csvfile, lineterminator="|")
                csv_writer.writerow([color])

            # append widget
            num_children = self.parent().color_grid_layout.count()
            row_count, column_count = self.parent().getGridSetup()
            index = num_children % column_count
            row = int(num_children/column_count)
            self.parent().color_grid_layout.addWidget(label, row+1, index, 1, 1)

        elif self.label:
            label = self.label
            # reset csv file

            publish_loc = KatanaResources.GetUserKatanaPath()
            # import csv
            file_loc = publish_loc + "/color.csv"
            if os.path.exists(file_loc):
                with open(file_loc, "rb") as csvfile:
                    color_list = csvfile.readlines()[0].split("|")[:-1]
            new_color = ",".join([str(label.color[0]), str(label.color[1]), str(label.color[2])])
            for index, color in enumerate(color_list):
                if color == "\"" + new_color + "\"":
                    color_list[index] = "\"" + ",".join([str(self.color[0]), str(self.color[1]), str(self.color[2])]) + "\""

            file_loc = publish_loc + "/color.csv"
            file = open(file_loc, "w")
    
            write_text = "|".join(color_list) + "|"
            file.write(write_text)
            file.close()
            
            label.setStyleSheet("background-color: rgb(%s,%s,%s);" % (self.color[0], self.color[1], self.color[2]))
            label.setColor(self.color)
        
    def addColorAndClose(self):
        self.addColor()
        self.close()
        
    def getColor(self):
        return self.color


class ColorLabel(QLabel):
    def __init__(self, parent=None, color=None):
        super().__init__(parent)
        self.selected = False
        self.color = color
        self.node_list = []
        self.setMouseTracking(True)
        
    def isSelected(self):
        return self.selected
    
    def setColor(self, color):
        self.color = color
        
    def getColor(self):
        return self.color

    def deleteSelf(self):
        # delete color from csv / label / layout
        publish_loc = KatanaResources.GetUserKatanaPath()
        file_loc = publish_loc + "/color.csv"
        if os.path.exists(file_loc):
            with open(file_loc, "rb") as csvfile:
                color_list = csvfile.readlines()[0].split("|")[:-1]
        new_color = ",".join([str(self.color[0]), str(self.color[1]), str(self.color[2])])
        color_list.remove("\"" + new_color + "\"")

        file_loc = publish_loc + "/color.csv"
        
        write_text = "|".join(color_list) + "|"
        print(write_text)
        if write_text == "|":
            print("removing...")
            os.remove(file_loc)
        else:
            file = open(file_loc, "w")
            print("writing...")
            file.write(write_text)
            file.close()

        # delete widget
        self.parent().layout().removeWidget(self)
        self.deleteLater()
        self = None
        
    def mouseMoveEvent(self, event):
        # preflight
        if event.buttons() != Qt.LeftButton: return
        # drag delete set up handlers
        mimedata = QMimeData()
        mimedata.setText("%d,%d" % (event.x(), event.y()))

        pixmap = QPixmap.grabWidget(self)

        drag = QDrag(self)
        drag.setMimeData(mimedata)
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())

        if drag.exec_(Qt.CopyAction | Qt.MoveAction) == Qt.MoveAction:
            self.checkMouse(event)
        else:
            self.checkMouse(event)
        return QLabel.mouseMoveEvent(self, event)

    def checkMouse(self):
        if not self.parent().parent().getDropLocation():
            self.deleteSelf()
            self.parent().parent().populate()
    
    def mousePressEvent(self, event):
        self.last = "Click"
    
    def mouseReleaseEvent(self, event):
        if self.last == "Click":
            QTimer.singleShot(
                QApplication.instance().doubleClickInterval(),
                self.singleClick)
        #return QLabel.mouseReleaseEvent(self, event,*args, **kwargs)
        
    def singleClick(self):
        # set color to nodes
        self.last = "Double Click"
        for node in NodegraphAPI.GetAllSelectedNodes():
            self.node_list.append([node, DrawingModule.GetCustomNodeColor(node)])
            DrawingModule.SetCustomNodeColor(node, self.color[0]/255, self.color[1]/255, self.color[2]/255)
        UI4.App.Tabs.FindTopTab("Node Graph").update()

    def mouseDoubleClickEvent(self, *args, **kwargs):
        # pop up window to change the label color
        if self.last == "Click":
            main_window = MainWindow(self.parent(), label=self)
            main_window.show()
        
    def enterEvent(self, event):
        # displaying the border around labels
        # displaying node colors
        self.node_list = []
        for node in NodegraphAPI.GetAllSelectedNodes():
            self.node_list.append([node , DrawingModule.GetCustomNodeColor(node)])
            DrawingModule.SetCustomNodeColor(node, self.color[0]/255, self.color[1]/255, self.color[2]/255)
        UI4.App.Tabs.FindTopTab("Node Graph").update()
        self.parent().parent().labelClicked(self)
        return QLabel.enterEvent(self, event)

    def leaveEvent(self, event):
        # removing borders around labels upon leaving label
        # removing display node colors
        for item in self.node_list:
            node = item[0]
            color = item[1]
            if not color:
                color = (0.28, 0.28, 0.28)
            DrawingModule.SetCustomNodeColor(node, color[0], color[1], color[2])
            UI4.App.Tabs.FindTopTab("Node Graph").update()
        self.parent().parent().labelClicked(self)
        return QLabel.leaveEvent(self, event)


class ColorDialog(QColorDialog):
    # subclass of the QColorDialog to be used as a popup menu for users to pick colors
    # to add to their default color bar with
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setVisible(True)
        self.setOption(self.NoButtons, True)


# primary calling function used to open/close the gui.  This gui is embedded
# into the Nodegraph Widget
from Katana import UI4
node_graph = UI4.App.Tabs.FindTopTab("Node Graph")
layout = node_graph.layout()
does_exist = None
for index in range(layout.count()):
    item = layout.itemAt(index)
    widget = item.widget()
    if hasattr(widget, "does_exist"):
        widget.close()
        widget.parent().layout().removeWidget(widget)
        widget.deleteLater()
        widget = None
        does_exist = True
if not does_exist:
    widget = MainWidget()
    node_graph.layout().insertWidget(2, widget)


mainFunction()



