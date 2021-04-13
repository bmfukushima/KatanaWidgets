from qtpy import QtWidgets, QtGui, QtCore, Qt
from Katana import UI4, NodegraphAPI
import sys 
'''
b =UI4.App.Tabs.FindTopTab('Parameters')
'_GafferEditor__importRig'
def getEditor(widget,widget_list=[]):
    #print widget
    #print widget.children()
    children = widget.children()
    #print widget , children
    
    if hasattr(widget,'_GafferEditor__importRig'):
        print 'widget == %s'%widget
        widget_list.append(widget)
        return widget_list
        #break
    else:
        val = None
        for child in widget.children():
            val = getEditor(child,widget_list=widget_list)
            if val is not None:
                return val
    return None

print getEditor(b)
'''
class DragButton(QtWidgets.QPushButton):
    def __init__(self,parent=None):
        super(DragButton,self).__init__(parent)
        self.setText('lkjasdf')
        #event filter has to be installed on the nodegraph widget
        #self.node_graph_widget = UI4.App.Tabs.FindTopTab('Node Graph').getNodeGraphWidget()
        self.parameters_widget = UI4.App.Tabs.FindTopTab('Parameters')
        #.getNodeGraphWidget()
        self.parameters_widget.installEventFilter(self)
        self.parameters_widget._installEventFilterForChildWidgets()
        #self.node_graph_widget.installEventFilter(self)
        
    def mousePressEvent(self, event, *args, **kwargs):
        '''
        drag = QtGui.QDrag(self)
        image_path = '/media/ssd01/Eclipse/Python/qtpyExamples/image.jpg'
        pixmap = QtGui.QPixmap(image_path)

        pixmap = pixmap.scaledToWidth(500)

        drag.setPixmap(pixmap)

        hotspot = QtCore.QPoint(pixmap.width() * .5 , pixmap.height() *.5)
        drag.setHotSpot(hotspot)
        mime_data = QtCore.QMimeData()
        mime_data.setText('test')
        mime_data.setData('test/this','this is a test string')
        
        drag.setMimeData(mime_data)
        drag.exec_(QtCore.Qt.MoveAction)
        '''
        return QtWidgets.QPushButton.mousePressEvent(self, event, *args, **kwargs)

    def mouseReleaseEvent(self, event, *args, **kwargs):
        #print 'release'
        
        pos = QtGui.QCursor.pos()
        widget = QtWidgets.qApp.widgetAt(pos)

        #print dir(widget)
        '''
        print widget 
        print widget.parent() 
        print widget.parent().parent()
        print widget.parent().parent().parent()
        print widget.parent().parent().parent().parent()
        '''
        rig = '/media/ssd01/Katana/scenes/testrig.rig'
        gaffer_editor = widget.parent().parent().parent().parent()
        print gaffer_editor
        c = gaffer_editor._BaseEditor__sceneGraphViewWidget.parent()
        for child in c.children():
            print child , len(child.children())
        '''
        for x in dir(gaffer_editor):
            print x
        
        print gaffer_editor.getSceneGraphView()
        print gaffer_editor.getMainPanelWidget()
        

        
        #gaffer_editor._GafferEditor__importRig()
        #print gaffer_editor._BaseEditor__mainNode
        #for x in dir(gaffer_editor):
            #print x
        
        _GafferEditor__importRig
        _BaseEditor__addPackage
        _BaseEditor__mainNode
        _BaseEditor__mainPanel
        _BaseEditor__createChildPackage
        '''
        #<__plugins0__.GafferThree.v1.Editor.GafferEditor object at 0x7f49aeca4640>
        '''
        print widget.parent().parent().parent().parent().parent()
        print widget.parent().parent().parent().parent().parent().parent()
        print widget.parent().parent().parent().parent().parent().parent().parent()
        print widget.parent().parent().parent().parent().parent().parent().parent().parent()
        print widget.parent().parent().parent().parent().parent().parent().parent().parent().parent()
        print widget.parent().parent().parent().parent().parent().parent().parent().parent().parent().parent()
        parameters_panel = widget.parent().parent().parent().parent().parent().parent().parent().parent().parent().parent()
        '''
        
        print 'end'
        return QtWidgets.QPushButton.mouseReleaseEvent( self, event, *args, **kwargs )

    #def eventFilterParameters(self, *args, **kwargs):
        #return QtWidgets.QPushButton.eventFilter(self, *args, **kwargs)
    def eventFilter(self,obj,event,*args,**kwargs):

        if event.type() in (QtCore.QEvent.DragEnter, QtCore.QEvent.DragMove, QtCore.QEvent.Drop):
            if event.type() != QtCore.QEvent.Drop:
                event.acceptProposedAction()
            else:
                print 'dropped!'
                pos = QtGui.QCursor.pos()
                widget = QtWidgets.qApp.widgetAt(pos)
                print widget
                #print dir(widget)
                
                print widget 
                print widget.parent()
                print widget.parent().parent()
                print widget.parent().parent().parent()
                print widget.parent().parent().parent().parent()
                print widget.parent().parent().parent().parent().parent()
                print widget.parent().parent().parent().parent().parent().parent()
                print widget.parent().parent().parent().parent().parent().parent().parent()
                print widget.parent().parent().parent().parent().parent().parent().parent().parent()
                print widget.parent().parent().parent().parent().parent().parent().parent().parent().parent()
                    
                rig = '/media/ssd01/Katana/scenes/testrig.rig'
                gaffer_editor = widget.parent().parent().parent().parent()
                #gaffer_editor._GafferEditor__importRig()
                #print gaffer_editor._BaseEditor__mainNode
                '''
                
                node_list = []
                for x in range (0,5):
                    node = NodegraphAPI.CreateNode('Group', NodegraphAPI.GetRootNode())
                    NodegraphAPI.SetNodePosition(node,(0,x*50))
                    node_list.append(node)

                self.node_graph_widget.parent().floatNodes(node_list)
                '''
            return True

        '''
        print event.type()
        if event.type() == QtCore.QEvent.DragEnter:
            event.acceptProposedAction()
            print 'enter'
        elif event.type() == QtCore.QEvent.DragMove:
            event.acceptProposedAction()
            print 'drag move'
        elif event.type() == QtCore.QEvent.Drop:
            print 'drop'
            node = NodegraphAPI.CreateNode('Group', NodegraphAPI.GetRootNode())
            self.node_graph_widget.floatNodes([node])
        '''
        return QtWidgets.QPushButton.eventFilter(self, obj, event, *args, **kwargs)
main_widget = DragButton()
main_widget.show()

#sys.exit(app.exec_())
