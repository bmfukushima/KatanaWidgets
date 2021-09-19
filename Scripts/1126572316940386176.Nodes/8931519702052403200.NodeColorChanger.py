"""
Hierarchy:
    NodeColorModifierWidget --> (QWidget)
        |- QVBoxLayout
            |- nodeSearchBoxLayout() --> (QHBoxLayout)
            |  |- nodeSearchBoxWidget() --> (NodeSearchBox)
            |- color_grid_widget --> (QWidget)
               |- color_grid_layout --> (QGridLayout)
                   |- search_button --> (QPushButton)
                   |- add_color_button --> (QPushButton)


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
"""
TODO:
    *   Clean... Everything...
        - Populate
            For some reason the search button/add color button are being added/removed
            with every population.  Rather than one time, and only repopulating the colors.
        - StyleSheets
            Hard coded with horrid syntax
        - Color seems to be stored as a string? Instead of a QColor?
        - Docstrings...
        - CSV --> JSON
    
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
from qtpy.QtCore import (Qt, QSortFilterProxyModel, QEvent, QTimer)
from qtpy.QtGui import (QStandardItemModel, QStandardItem)

from Katana import UI4, NodegraphAPI, KatanaResources, DrawingModule

from cgwidgets.utils import centerWidgetOnCursor, getWidgetAncestor


"""
param{param}
hasparam{param=value}
type{nodeType}
name{node_name}
"""
class NodeColorModifierWidget(QWidget):
    """ Main widget for modifying node colors.  This will be displayed at the top of the NodeGraph

    Attributes:
        color_label_widgets (list): of ColorLabel widgets
        is_node_color_modifier_widget (bool): flag to search for when hiding/showing the widget
        label_size (int): size of each label to be displayed to the user
        label_spacing (int): space between each label
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # setup default attrs
        self._color_label_widgets = []
        self._is_node_color_modifier_widget = True
        self._label_size = 35
        self._label_spacing = 5

        # setup Add color button
        self._add_color_widget = QPushButton("+")
        self.addColorWidget().clicked.connect(self.showColorPickerWidget)
        self.addColorWidget().setFixedSize(self.labelSize(), self.labelSize())

        # setup node search box
        self._node_search_display_toggle_widget = QPushButton("^")
        self._node_search_display_toggle_widget.clicked.connect(self.toggleNodeSearchBarDisplay)
        self._node_search_display_toggle_widget.setFixedSize(self.labelSize(), self.labelSize())

        self._node_search_box_widget = NodeSearchBox()
        self._node_search_box_layout = QHBoxLayout()
        self.nodeSearchBoxLayout().addWidget(self.nodeSearchBoxWidget())
        self._node_search_box_widget.hide()

        # setup color grid
        self._color_grid_widget = QWidget()
        self._color_grid_layout = QGridLayout()
        self._color_grid_widget.setLayout(self.colorGridLayout())
        self.colorGridLayout().setSpacing(self.labelSpacing())
        self.colorGridLayout().setSizeConstraint(QLayout.SetFixedSize)

        # setup main layout
        QVBoxLayout(self)
        self.layout().setContentsMargins(0, 5, 0, 0)
        self.layout().addLayout(self.nodeSearchBoxLayout())
        self.layout().addWidget(self._color_grid_widget)

        # setup style
        self.setStyleSheet("""QPushButton{{border: {border_size}px dotted rgba(128,128,128,128);}}""".format(
            border_size=int(self.labelSize()*0.2)))

        # initialize widgets
        self.initDefaultColors()
        self.populate()

    """ WIDGETS """
    def addColorWidget(self):
        return self._add_color_widget

    def colorGridWidget(self):
        return self._color_grid_widget

    def colorGridLayout(self):
        return self._color_grid_layout

    def nodeSearchBoxLayout(self):
        return self._node_search_box_layout

    def nodeSearchBoxWidget(self):
        return self._node_search_box_widget

    def nodeSearchDisplayToggleWidget(self):
        return self._node_search_display_toggle_widget

    """ UTILS """
    def toggleNodeSearchBarDisplay(self):
        """ Hides/Shows the Node search bar"""
        if self.nodeSearchBoxWidget().isVisible():
            self.nodeSearchBoxWidget().hide()
        elif not self.nodeSearchBoxWidget().isVisible():
            self.nodeSearchBoxWidget().show()

    def getGridSetup(self):
        """ Gets the row/column count based off of the current labelSize() of the NodeGraph"""
        node_graph = UI4.App.Tabs.FindTopTab("Node Graph")
        layout_width = node_graph.geometry().width()
        widget_list = self.initDefaultColors()
        margin_size = self.labelSpacing()
        color_label_size = self.labelSize()
        init_length = (margin_size + color_label_size) * len(widget_list)
        row_count = int(init_length / layout_width) + 1
        column_count = int(layout_width / (margin_size + color_label_size))
        self.num_columns = column_count
        return row_count, column_count
    
    def populate(self):
        """ Adds all of the ColorLabels to the colorGridLayout """

        # clear existing labels
        for i in reversed(range(self.colorGridLayout().count())):
            self.colorGridLayout().itemAt(i).widget().setParent(None)

        # get attrs
        row_count, column_count = self.getGridSetup()
        widget_list = self.initDefaultColors()

        # add widgets to the color grid
        for count, label in enumerate(widget_list):
            column = count % column_count
            row = int(count/column_count)
            self.colorGridLayout().addWidget(label, row+1, column, 1, 1)
            self.colorGridLayout().setColumnStretch(column, QSizePolicy.Minimum)

        self.colorGridLayout().setSizeConstraint(QLayout.SetFixedSize)
        
    def initDefaultColors(self):
        """ Creates all of the Color Labels from the source file

        Returns (list): of all widgets

        """
        widget_list = [self.nodeSearchDisplayToggleWidget(), self.addColorWidget()]
        publish_loc = KatanaResources.GetUserKatanaPath()
        file_loc = publish_loc + "/color.csv"
        if os.path.exists(file_loc):
            with open(file_loc, "r") as csvfile:
                for line in csvfile.readlines():
                    color_list = line.split("|")[:-1]
                    for color in color_list:
                        color = color.replace("\"", '')
                        color = [int(value) for value in color.split(",")]
                        widget_list.append(self.createColorLabel(color))

        return widget_list

    def createColorLabel(self, color):
        """ Creates a color label.

        The color label's are the squares of color that show up in the main display

        Args:
            color (tuple): rgb string values 0-255"""
        label = ColorLabel(color=color)
        label.setStyleSheet("background-color: rgb(%s,%s,%s);" % (color[0], color[1], color[2]))
        label.setFixedSize(self.labelSize(), self.labelSize())
        return label

    def labelClicked(self, widget):
        label = widget
        selected = label.isSelected()
        if selected:
            label.setStyleSheet("background-color: rgb(%s,%s,%s);" % (label.color[0], label.color[1], label.color[2]))
            label.selected = False
        else:
            label.setStyleSheet("""
                background-color: rgb({r},{g},{b});
                border: {border_size}px dotted rgba(128,128,128,255)""".format(
                r=label.color[0], g=label.color[1], b=label.color[2], border_size=int(self.labelSize() * 0.2)))
            label.selected = True

    """ PROPERTIES """
    def colorLabelWidgets(self):
        return self._color_label_widgets

    def labelSize(self):
        return self._label_size

    def setLabelSize(self, label_size):
        self._label_size = label_size

    def labelSpacing(self):
        return self._label_spacing

    def setLabelSpacing(self, label_spacing):
        self._label_spacing = label_spacing

    """ EVENTS """
    def showColorPickerWidget(self):
        """ Shows the color picket widget to the user"""
        color_picker_widget = ColorPickerWidget(self)
        color_picker_widget.show()
        centerWidgetOnCursor(color_picker_widget)

    def resizeEvent(self, event):
        """ On resize, layout all of the ColorLabels to fit in the active view """
        # to avoid recursion, checks for column count and compares to the previous column count
        node_graph = UI4.App.Tabs.FindTopTab("Node Graph")
        layout_width = node_graph.geometry().width()
        init_size = self.labelSpacing() + self.labelSize()
        num_columns = int(layout_width/init_size)
        if num_columns != self.num_columns:
            self.num_columns = num_columns
            self.populate()
        self.layout().setSizeConstraint(QLayout.SetDefaultConstraint)

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Delete, Qt.Key_Backspace]:
            for index in range(self.colorGridLayout().childCount()):
                label = self.colorGridLayout().itemAt(index).widget()
                if hasattr(label, "selected"):
                    if label.isSelected():
                        label.deleteSelf()


class NodeSearchBox(QComboBox):
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
        super(NodeSearchBox, self).setModel(model)
        self.pFilterModel.setSourceModel(model)
        self.completer.setModel(self.pFilterModel)

    def setModelColumn(self, column):
        self.completer.setCompletionColumn(column)
        self.pFilterModel.setFilterKeyColumn(column)
        super(NodeSearchBox, self).setModelColumn(column)

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


class ColorPickerWidget(QMainWindow):
    """ Color picker widget for users to choose new colors for nodes.

    When the user clicks on the "+" button, or double clicks a color this
    widget is activated over the current cursors location.  This widget is
    activated from NodeColorModifierWidget.showColorPickerWidget()

    Args:
        parent
        label

    Attributes:
    """
    def __init__(self, parent=None, label=None):
        super(ColorPickerWidget, self).__init__(parent=parent)

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
            label = self.parent().createColorLabel(self.color)
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
            num_children = self.parent().colorGridLayout().count()
            row_count, column_count = self.parent().getGridSetup()
            index = num_children % column_count
            row = int(num_children/column_count)
            self.parent().colorGridLayout().addWidget(label, row+1, index, 1, 1)

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
    """ Displays a solid color to the user """
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

    """ UTILS """
    def setNodeColor(self):
        # set color to nodes
        for node in NodegraphAPI.GetAllSelectedNodes():
            self.node_list.append([node, DrawingModule.GetCustomNodeColor(node)])
            DrawingModule.SetCustomNodeColor(node, self.color[0]/255, self.color[1]/255, self.color[2]/255)
        UI4.App.Tabs.FindTopTab("Node Graph").update()

    def deleteSelf(self):
        # delete color from csv / label / layout
        publish_loc = KatanaResources.GetUserKatanaPath()
        file_loc = publish_loc + "/color.csv"
        if os.path.exists(file_loc):
            with open(file_loc, "r") as csvfile:
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

        node_modifier_widget = getWidgetAncestor(self, NodeColorModifierWidget)
        node_modifier_widget.populate()

    """ EVENTS """
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.deleteSelf()
        if event.button() == Qt.LeftButton:
            QTimer.singleShot(
                QApplication.instance().doubleClickInterval(),
                self.setNodeColor)
        #return QLabel.mouseReleaseEvent(self, event,*args, **kwargs)

    def mouseDoubleClickEvent(self, *args, **kwargs):
        # pop up window to change the label color
        node_color_modifier_widget = getWidgetAncestor(self, NodeColorModifierWidget)
        node_color_modifier_widget.showColorPickerWidget()
        
    def enterEvent(self, event):
        """ Display border around color when hovering over it """
        self.node_list = []
        for node in NodegraphAPI.GetAllSelectedNodes():
            self.node_list.append([node, DrawingModule.GetCustomNodeColor(node)])
            DrawingModule.SetCustomNodeColor(node, self.color[0]/255, self.color[1]/255, self.color[2]/255)
        UI4.App.Tabs.FindTopTab("Node Graph").update()
        self.parent().parent().labelClicked(self)
        return QLabel.enterEvent(self, event)

    def leaveEvent(self, event):
        """Remove borders around labels upon leaving label"""
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
node_graph = UI4.App.Tabs.FindTopTab("Node Graph")
layout = node_graph.layout()
_is_node_color_modifier_widget = None
for index in range(layout.count()):
    item = layout.itemAt(index)
    if item:
        widget = item.widget()
        if hasattr(widget, "_is_node_color_modifier_widget"):
            widget.close()
            widget.parent().layout().removeWidget(widget)
            widget.deleteLater()
            widget = None
            _is_node_color_modifier_widget = True
if not _is_node_color_modifier_widget:
    widget = NodeColorModifierWidget()
    node_graph.layout().insertWidget(2, widget)




