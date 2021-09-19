'''
# ToDo
Necessary
    - Enter --> Signal to set isolatedFrom on isolate node
        if not showing the popup menu

Wish List
    - Deletion of '/' will reload old children
        shift+deleter = move up one dir?
    - Modifier = make ?IRF?



'''
import sys ,subprocess

from PyQt5 import QtWidgets, QtCore, Qt, QtGui
try:
    from Katana import ScenegraphManager, Nodes3DAPI, FnGeolib,NodegraphAPI, UI4
except:
    pass

class IsolateComboBox(QtWidgets.QComboBox):
    '''
    a way to create new nodes inside of the widget itself
    '''
    def __init__(self,parent=None):
        super(IsolateComboBox,self).__init__(parent)
        self.main_widget = self.parent()
        self.setFocusPolicy( QtCore.Qt.StrongFocus )
        self.setLineEdit(QtWidgets.QLineEdit("Select & Focus", self))
        
        self.setEditable(True)
        #item_list=['asdfaf','bbb','ccc','aad','bba','cced']
        lcd = self.getLCD()
        item_list = self.getChildren(lcd)
        self.completer = self.setupCompleter(item_list)
        self.lineEdit().setText(lcd)
        #self.lineEdit().selectAll()
        self.lineEdit().setFocus()   
        self.setStyleSheet('font: 24px "Arial"')
        #print lcd
    
    def setupCompleter(self,item_list=[]):
        self.completer = PathCompleter(self,item_list=item_list)
        self.completer.setCompletionMode( QtWidgets.QCompleter.PopupCompletion )
        self.completer.setCaseSensitivity( QtCore.Qt.CaseInsensitive )
        self.completer.setPopup( self.view() )
        self.setCompleter( self.completer )
        return self.completer
     
    def view( self ):
        return self.completer.popup()            
    def next_completion(self):
        row = self.completer.currentRow()
        if not self.completer.setCurrentRow(row + 1):
            self.completer.setCurrentRow(0)
        index = self.completer.currentIndex()
        self.completer.popup().setCurrentIndex(index)
        #self.completer.popup().show()
    def previous_completion(self):
        row = self.completer.currentRow()
        numRows = self.completer.completionCount()
        if not self.completer.setCurrentRow(row - 1):
            self.completer.setCurrentRow(numRows-1)
        index = self.completer.currentIndex()
        self.completer.popup().setCurrentIndex(index)

    def getTopLevelItem(self,item):  
        if not item.parent():
            return item
        else:
            return self.getTopLevelItem(item.parent())   
        
    
    def event(self, event,*args, **kwargs):
        if (event.type()==QtCore.QEvent.KeyPress) and (event.key()==QtCore.Qt.Key_Tab):
            ## Tab Pressed
            self.next_completion()
            return True

        elif (event.type()==QtCore.QEvent.KeyPress) and (event.key()==16777218):
            ## Shift Tab Pressed
            self.previous_completion()
            return True
        if (event.type()==QtCore.QEvent.KeyPress) and (event.key()==QtCore.Qt.Key_Slash):
            #print self.lineEdit().text()
            item_list = self.getChildren(self.lineEdit().text())
            #item_list = ['123','456','11','abc','bba','cced']
            self.completer = self.setupCompleter(item_list)
        elif (event.type()==QtCore.QEvent.KeyPress) and (event.key() == 16777220 or event.key() == 16777221):
            #enter pressed
            popup_vis = self.completer.popup().isVisible()
            if popup_vis == False:
                self.createNode()
                self.close()
                # send to isolate node
            elif popup_vis == True:
                return_val = super( IsolateComboBox, self ).event( event, *args, **kwargs )
                text = self.lineEdit().text() + '/'
                
                
                item_list = self.getChildren(text)
                self.completer = self.setupCompleter(item_list)
                self.lineEdit().setText(text)

            elif (event.type()==QtCore.QEvent.KeyPress) and (event.key() == QtCore.Qt.Key_Escape):
                print 'escape?'
                self.close()
            pass
        return QtWidgets.QComboBox.event(self, event,*args, **kwargs)
    #===========================================================================
    # katana functions
    #===========================================================================
    def createNode(self):
        #lcd=self.getLCD()
        def connectNode(node):
            resolve_node = NodegraphAPI.GetViewNode()
            if resolve_node.getType() != 'Render':
                
                #set node position
                NodegraphAPI.SetNodePosition(node, NodegraphAPI.GetNodePosition(resolve_node))
                upstream_nodes = getAllUpstreamNodes(resolve_node,node_list=[])
                for child_node in upstream_nodes:
                    pos = (NodegraphAPI.GetNodePosition(child_node)[0],NodegraphAPI.GetNodePosition(child_node)[1]+50)
                    NodegraphAPI.SetNodePosition(child_node, pos)
                #set node flag
                NodegraphAPI.SetNodeViewed(node,True,exclusive=True)
                #connect input
                output_port = resolve_node.getOutputPortByIndex(0)
                node.getInputPortByIndex(0).connect(output_port)
                #need function to run up and move all nodes in graph up 100 units to allow space for the new node...
                port_list = output_port.getConnectedPorts()
                #connect output...
                if len(port_list) > 0:
                    #next_node = port_list[0].getNode()
                    node.getOutputPortByIndex(0).connect(port_list[0])
            
        def getAllUpstreamNodes(node,node_list=[]):
            children = node.getInputPorts()
            node_list.append(node)
            if children > 0:
                for input_port in children:
                    connected_ports = input_port.getConnectedPorts()
                    for port in connected_ports:
                        node = port.getNode()
                        
                        getAllUpstreamNodes(node,node_list=node_list)
            return node_list
        
        #print getAllUpstreamNodes(node,node_list=[])
        
        
        
        
        selected_locations = ScenegraphManager.getActiveScenegraph().getSelectedLocations()
        isolate_string =  '%s'%' '.join(selected_locations)
        isolate_from = self.lineEdit().text()
        node_graph = UI4.App.Tabs.FindTopTab('Node Graph')
        node = NodegraphAPI.CreateNode('Isolate',NodegraphAPI.GetRootNode())
        node.getParameter('isolateLocations').resizeArray(1)
        node.getParameter('isolateLocations.i0').setValue(isolate_string,0)
        node.getParameter('isolateFrom').setValue(str(isolate_from),0)
        
        connectNode(node)
        node_graph.floatNodes([node])
    def searchLocationsForLCD(self,name_list=[],temp_string='',lcd=''):
            ### should run through a list of strings and compare...
            ### temp string == lcd
            #print '==='*5
            name = name_list[0].replace('/','')
            old_string = temp_string
            temp_string += '/%s'%name
            string_length = len(temp_string)
            if lcd[:string_length] == temp_string:
                #print name_list
                #name_list = name_list[1:]
                #print name_list
                if len(name_list) == 1:
                    return temp_string
                else:
                    return self.searchLocationsForLCD(name_list=name_list[1:],temp_string=temp_string,lcd=lcd)
    
            else:
                return old_string
    def getLCD(self):
        locations = ScenegraphManager.getActiveScenegraph().getSelectedLocations()
        lcd = locations[0]
        for loc in locations:
            name_list = loc.split('/')
            temp_string = self.searchLocationsForLCD(name_list=name_list[1:],temp_string='',lcd=lcd)
        return temp_string +'/'
    
    def getChildren(self,scenegraph_location):
        # We first need to get a hold of the runtime the UI is using
        runtime = FnGeolib.GetRegisteredRuntimeInstance()

        txn = runtime.createTransaction()
        client = txn.createClient()
        op = Nodes3DAPI.GetOp(txn, NodegraphAPI.GetViewNodes()[0])
        txn.setClientOp(client, op)
         
        # Tell the runtime to do its thing, if we don't the client will
        # exist, but won't yet be pointing to an Op
        runtime.commit(txn)
        location = client.cookLocation(scenegraph_location)

        return location.getPotentialChildren()

    
class PathCompleter(QtWidgets.QCompleter):
    ConcatenationRole = QtCore.Qt.UserRole + 1
    def __init__(self,parent=None,item_list=None):
        super(PathCompleter,self).__init__(parent)
        
        self.create_model(item_list)
    
    def splitPath(self, path):
        #the path that will be searched against
        if '/' in path:
            path = path[path.rindex('/')+1:]
        return path.split('.')

    def pathFromIndex(self, ix):
        #returns the path when an index is selected and replaces the line edit with that
        current_line = self.parent().lineEdit().text()
        new_line = ix.data(PathCompleter.ConcatenationRole)

        if '/' in current_line:
            new_path = current_line[:current_line.rindex('/')+1] + new_line
        else:
            new_path = new_line
        return new_path

    def create_model(self, data):
        def addItems(parent, elements, t=""):
            for text in elements:
                item = QtGui.QStandardItem(text)
                font = item.font()
                font.setPointSize(24)
                item.setFont(font)
                data = t + "." + text if t else text
                item.setData(data, PathCompleter.ConcatenationRole)
                parent.appendRow(item)
                
        model = QtGui.QStandardItemModel(self)
        addItems(model, data)
        self.setModel(model)

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)
else:
    app = QtWidgets.QApplication.instance()
GUI = IsolateComboBox()
main_window = UI4.App.MainWindow.GetMainWindow().geometry()
x_pos = QtGui.QCursor.pos().x()
y_pos = QtGui.QCursor.pos().y()
height = 25
GUI.setGeometry(main_window.left(), y_pos - height , main_window.width(), height * 2)
GUI.show()
#GUI.show()
#app.exec_()

