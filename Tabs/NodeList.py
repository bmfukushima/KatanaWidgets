'''
To Do 

    - Drag/Drop move nodes via Node List
    - option for syncing the state
    - option for viewing super tool children
    - sometimes super tool children not sorting correctly inside of supertools?
    - rename nodes
    - sort by node type
'''

from PyQt5.QtWidgets import (
    QWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QComboBox,
    QCompleter,
    QApplication
)
from PyQt5.QtCore import Qt, QEvent, QSortFilterProxyModel
from PyQt5.QtGui import QBrush, QStandardItem, QStandardItemModel


#class MainWindow(UI4.Tabs.BaseTab):
class MainWindow(QWidget):
    def __init__(self,parent=None):
        super(MainWindow,self).__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.node_list = NodeList(self)
        self.search_box = CreateSearchBox(self)
        
        
        layout.addWidget(self.search_box)
        layout.addWidget(self.node_list)
        
        Utils.EventModule.RegisterCollapsedHandler(self.update, 'node_create',None)
        Utils.EventModule.RegisterCollapsedHandler(self.update, 'node_setName',None)
        Utils.EventModule.RegisterCollapsedHandler(self.update, 'node_setParent',None)
        Utils.EventModule.RegisterCollapsedHandler(self.updateColor, 'node_setEdited',None)
        Utils.EventModule.RegisterCollapsedHandler(self.updateColor, 'node_setViewed',None)

    def updateColor(self, eventID):
        tree_widget = self.node_list
        tree_widget.updateItemColor()

    def update(self, eventID):
        # get tree widget
        tree_widget = self.node_list
        
        # delete list
        for index in reversed(range(tree_widget.topLevelItemCount())):
            tree_widget.takeTopLevelItem(index)
        tree_widget.populate()
        tree_widget.updateItemColor()
        # repopulate


class NodeList(QTreeWidget):
    def __init__(self,parent=None):
        super(NodeList,self).__init__(parent)
        self.item_dict = {}
        self.view_item = None
        
        
        header = QTreeWidgetItem(['name','type'])
        #self.head.setResizeMode(0,QHeaderView.Stretch)
        self.setAlternatingRowColors(True)
        self.setHeaderItem(header)
        self.populate()

        #NodegraphAPI.GetAllEditedNodes()
        #NodegraphAPI.GetViewNode()
    def populate(self):

        def set_flag(item):
            if item == self.invisibleRootItem():
                return
            else:
                item.setFlag(True)
                if item.parent():
                    set_flag(item.parent())
        def populateChildren(root,item=None):
            '''
            @root: Node(Katana)
            @item: NodeListItem(QTreewidgetItem)
            need to make this recursive... so it removes empty groups
            '''
            if hasattr(self.parent(), 'search_box'):
                search_box = self.parent().search_box
                current_text = search_box.currentText()
            else:
                current_text = ''
            if len(root.getChildren()) > 0:
                for node in root.getChildren():
                    bad_list = ['Dot','Backdrop']
                    if node.getType() in bad_list:
                        pass
                    else:
                        if current_text in node.getName() or hasattr(node,'getChildren') :

                            new_item = NodeListItem(parent=item,name=node.getName())
                            new_item.setNode(node)
                            new_item.setNodeParent(root)
                            if current_text in node.getName():
                                set_flag(new_item)
                            item_dict = self.getItemDict()
                            item_dict[node.getName()] = new_item
                            self.setItemDict(item_dict)
                            
                            if hasattr(node,'getChildren'):
                                if len(node.getChildren()) > 0:
                                    parent_item = populateChildren(node,new_item)
                                    new_item.setExpanded(True)
                                    if parent_item.getFlag() == False:
                                        grand_parent_item = parent_item.parent()
                                        if not grand_parent_item:
                                            grand_parent_item = self.invisibleRootItem()
                                        index = grand_parent_item.indexOfChild(parent_item)
                                        grand_parent_item.takeChild(index)
            return item
        root = NodegraphAPI.GetRootNode()
        self.setItemDict({})
        item = self.invisibleRootItem()
        populateChildren(root,item=item)
        self.updateItemColor()
    def getViewItem(self):
        return self.view_item
    def setViewItem(self,view_item):
        self.view_item = view_item
    def getItemDict(self):
        return self.item_dict
    def setItemDict(self,item_dict):
        self.item_dict = item_dict
    def updateItemColor(self):
        item_dict = self.getItemDict()
        for key in item_dict:
            
            item = item_dict[key]
            node = item.getNode()
            item.setEdited(NodegraphAPI.IsNodeEdited(node))
            item.setViewed(NodegraphAPI.IsNodeViewed(node))
            item.setColor()
    def goToNode(self,node):

        if not hasattr(node,'getChildren'):
            node = node.getParent()
        node_graph_tab = UI4.App.Tabs.FindTopTab('Node Graph')
        node_graph_tab._NodegraphPanel__navigationToolbarCallback(node.getName(),'useless')
        node_graph_tab._NodegraphPanel__frameAll()
    def selectionChanged(self, *args, **kwargs):
        node = self.currentItem().getNode()
        self.goToNode(node)
        return QTreeWidget.selectionChanged(self, *args, **kwargs)
    def keyPressEvent(self, event, *args, **kwargs):
        node = self.currentItem().getNode()
        if event.key() == Qt.Key_E:
            NodegraphAPI.SetNodeEdited(node, True, exclusive=True)
        elif event.key() == Qt.Key_V:
            NodegraphAPI.SetNodeViewed(node, True, exclusive=True)
        self.updateItemColor()
        #return QTreeWidget.keyPressEvent(self, event, *args, **kwargs)


class NodeListItem(QTreeWidgetItem):
    def __init__(self,parent=None,name=''):
        super(NodeListItem,self).__init__(parent)
        self.viewed = False
        self.edited = False
        self.flag = False
        self.setText(0,name)
        self.default_text = self.foreground(0)
        self.setColor()

    def setFlag(self,flag):
        self.flag = flag

    def getFlag(self):
        return self.flag

    def resetTextColor(self):
        self.setForeground(0,self.default_text)
        pass

    def getViewed(self):
        return self.viewed

    def setViewed(self,viewed):
        self.viewed = viewed

    def getEdited(self):
        return self.edited

    def setEdited(self,edited):
        self.edited = edited

    def setColor(self):
        self.setForeground(0,QBrush(QColor(200,200,200)))
        if self.getViewed() == True:
            self.setForeground(0,QBrush(QColor(128,128,255)))
        if self.getEdited() == True:
            self.setForeground(0,QBrush(QColor(100,200,100)))
        if self.getViewed() == True and self.getEdited() == True:
            self.setForeground(0,QBrush(QColor(255,200,0)))

    def getName(self):
        return self.name

    def setName(self, name):
        self.name = name
        self.setText(0,name)

    def getNode(self):
        return self.node

    def setNode(self, node):
        self.node = node
        self.setText(1,node.getType())
    def getNodeParent(self):
        return self.node_parent

    def setNodeParent(self,node_parent):
        self.node_parent = node_parent


class CreateSearchBox(QComboBox):
    '''
    so... this could be a line edit... not a combo box.. dont really need that popup search
    '''
    def __init__(self,parent=None):
        super(CreateSearchBox,self).__init__(parent)

        
        self.setEditable(True)
        self.main_widget = self.getMainWidget(self)
        self.lineEdit().textChanged.connect(self.textChanged)
        self.completer = QCompleter(self)

        self.completer.setCaseSensitivity(Qt.CaseInsensitive)

        self.setCompleter( self.completer )
        
        self.pFilterModel = QSortFilterProxyModel( self )
        node_names = self.main_widget.node_list.getItemDict().keys()
        self.nodeTypes = [''] + node_names
        #self.editTextChanged.connect(self.textChanged)
        self.populate()
        
        self.visible = False

    def setVisibility(self,visibility):
        self.visible = visibility

    def getVisibility(self):
        return self.visible

    def populate(self):       
        createNewNodeWidget = self
        model = QStandardItemModel()
        for i,nodeType in enumerate( self.nodeTypes ):
            item = QStandardItem(nodeType)
            model.setItem(i, 0, item)

        createNewNodeWidget.setModel(model)
        createNewNodeWidget.setModelColumn(0)     

    def setModel( self, model ):
        super(CreateSearchBox, self).setModel( model )
        self.pFilterModel.setSourceModel( model )
        self.completer.setModel(self.pFilterModel)

    def setModelColumn(self, column ):
        self.completer.setCompletionColumn( column )
        self.pFilterModel.setFilterKeyColumn( column )
        super(CreateSearchBox, self).setModelColumn( column )            

    def view(self):
        return self.completer.popup()            

    def getMainWidget(self, widget):
        if isinstance(widget, UI4.Tabs.BaseTab):
            return widget
        else:
            return self.getMainWidget(widget.parent())

    def textChanged(self, *args, **kwargs):
        #main_widget = self.getMainWidget(self)
        self.main_widget.update(None)

    def keyPressEvent(self, event):
        accept_list = [Qt.Key_Enter, Qt.Key_Return]
        if (event.type()==QEvent.KeyPress) and (event.key() == 16777220 or event.key() == 16777221):
            pass
            #self.selectNodes()

        return QComboBox.keyPressEvent(self, event)


if __name__ == '__main__':
    #MainWindow()
    import sys
    app = QApplication(sys.argv)
    a = CreateSearchBox()
    a.show()
    sys.exit(app.exec_())

else:
    from Katana import UI4, NodegraphAPI, Utils
    PluginRegistry = [("KatanaPanel", 2, "Node List", MainWindow)]
    #main_widget = MainWindow()
#a = MainWindow()
#a.show()


