'''
ImageLibrary comes from the WidgetFactory
#===============================================================================
# BUGS
#===============================================================================
ImportRigs
    naming conventions... if it exists, it will not import
'''

import os

from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *

from Katana import UI4, NodegraphAPI, KatanaFile #, self
# Will need to figure out how these the self libraries will conflict...
# if you load two in??

from .ImportLightRig import ImportRig
#from ImageLibrary import self
#from ImageLibrary.Main import Library
from cgwidgets.widgets import LibraryWidget
#from cgqtpy import __utils__ as self


class MainWidget(LibraryWidget):
    def __init__(self, parent=None):
        super(MainWidget, self).__init__(parent)
        #self.library_dir = os.environ['LIBRARY_DIR']
        # self.setupActions()

    def setEventFilterHack(self, widget):
        # KATANA
        # hacky event filter to set up the event
        # filters missed in getAllGafferThreeEditors
        widget.installEventFilter(self)
        if len(widget.children()) == 0:
            return
        else:
            for child in widget.children():
                val = self.setEventFilterHack(child)
                if val is not None:
                    return val
        return None

    def importRig(self, json_file, gaffer_three_node):
        '''
        imports a light rig into a gaffer three node
        '''
        json_data = self.getJSONData(json_file)
        katana_file = None
        for item in os.listdir(json_data['data']):
            if item.endswith('.rig'):
                katana_file = str('/'.join([json_data['data'], item]))

        # import file
        if not katana_file:
            print('no rig file found...')
            return
        ImportRig(katana_file, gaffer_three_node)
        return

    def getAllGafferThreeEditors(self, widget, widget_list=[]):
        '''
        looks at a widget and returns all the gaffer three editors in it
        this is to look for all the drag/drop into the gaffer theres as
        self.parameters_widget = UI4.App.Tabs.FindTopTab('Parameters')
        self.parameters_widget._installEventFilterForChildWidgets()
        does NOT install the event filter for apparently non Katana
        based widgets?
        '''
        # children = widget.children()
        if hasattr(widget, '_GafferEditor__importRig'):
            widget_list.append(widget)
        else:
            val = None
            for child in widget.children():
                val, widget_list = self.getAllGafferThreeEditors(
                    child, widget_list=widget_list
                )
                if val is not None:
                    return val
        return None, widget_list

    def importShaderIntoNodegraph(self, json_file, import_type='katana'):
        '''
        default action to happen when a user mmb drag/drops
        a 'shader' into the nodegraph
        '''
        # find katana file
        def getFile(json_file, ends_with=None):
            json_data = self.getJSONData(json_file)
            katana_file = None
            for item in os.listdir(json_data['data']):
                if item.endswith(ends_with):
                    katana_file = '/'.join([json_data['data'], item])
            return str(katana_file)

        node_graph = UI4.App.Tabs.FindTopTab('Node Graph')
        parentNode = node_graph.getEnteredGroupNode()
        katana_file = getFile(json_file, ends_with=import_type)
        name = self.getJSONData(json_file)['name']

        # import data into Katana for different types provided in the
        # pop up menu... right now this is hard coded into the DropMenu
        if import_type == 'katana':
            nodes = KatanaFile.Import(katana_file, parentNode=parentNode)
        elif import_type == 'klf':
            node = NodegraphAPI.CreateNode("LookFileAssign", parentNode)
            node.getParameter('args.lookfile.asset.value').setValue(katana_file, 0)
            node.getParameter('args.lookfile.asset.enable').setValue(1, 0)
            node.setName(name)
            nodes = [node]
        elif import_type == 'material':
            katana_file = getFile(json_file, ends_with='klf')
            node = NodegraphAPI.CreateNode("LookFileMaterialsIn", parentNode)
            node.getParameter('lookfile').setValue(katana_file, 0)
            node.setName(name)
            nodes = [node]
        elif import_type == 'subnet':
            print('not supported yet... but this is here.. just incase I decide to do this...')
        node_graph.floatNodes(nodes)

    def importTextureIntoNodegraph(self, file_list):
        '''
        @file_list <list> list of absolute paths to texture files on disk
        default action to happen when a type 'texture' is
        dropped into the node graph, currently set up for
        3Delight
        '''
        def createDLShadingNodes(texture_file_path, index):
            node_graph = UI4.App.Tabs.FindTopTab('Node Graph')
            parent_node = node_graph.getEnteredGroupNode()

            # create nodes
            file_node = NodegraphAPI.CreateNode('DlShadingNode', parent_node)
            file_node.getParameter('nodeType').setValue('file', 0)

            place2dTextureNode = NodegraphAPI.CreateNode(
                'DlShadingNode', parent_node
            )
            place2dTextureNode.getParameter('nodeType').setValue('place2dTexture', 0)

            # set parameters
            file_node.checkDynamicParameters()
            file_node.getParameter('parameters.fileTextureName.value').setValue(texture_file_path, 0)
            file_node.getParameter('parameters.fileTextureName.enable').setValue(1, 0)

            place2dTextureNode.checkDynamicParameters()
            file_node.getInputPort('uvCoord').connect(place2dTextureNode.getOutputPort('outUV'))
            file_name = texture_file_path[texture_file_path.rindex('/')+1:]
            file_name = file_name[:file_name.index('.')]
            file_node.setName(file_name)
            file_node.getParameter('name').setValue(file_name, 0)
            place2dTextureNode.getParameter('name').setValue('place2dTexture', 0)
            place2dTextureNode.setName('place2dTexture')

            # set node position
            NodegraphAPI.SetNodePosition(place2dTextureNode,(-200, index*100))
            NodegraphAPI.SetNodePosition(file_node, (0, index*100))
            node_graph.floatNodes([file_node, place2dTextureNode])

        renderer = os.environ["DEFAULT_RENDERER"]
        for index, file_path in enumerate(file_list):
            if renderer == 'dl':
                print('filepath ===== %s'%file_path)
                createDLShadingNodes(str(file_path), index)
            else:
                print(' This is only currently setup for 3Delight... bypassing for meow')

    def imageClickedEvent(self, event, widget):
        widget.button = event.button()
        json_file = widget.json_file
        # install event filters
        node_graph_widget = UI4.App.Tabs.FindTopTab('Node Graph').getNodeGraphWidget()
        node_graph_widget.installEventFilter(self)
        parameters_widget = UI4.App.Tabs.FindTopTab('Parameters')
        parameters_widget.installEventFilter(self)
        parameters_widget._installEventFilterForChildWidgets()

        gafferThree_list = self.getAllGafferThreeEditors(parameters_widget)[1]
        for gafferThree in gafferThree_list:
            self.setEventFilterHack(gafferThree._BaseEditor__sceneGraphViewWidget)
            # gafferThree._BaseEditor__sceneGraphViewWidget.installEventFilter(self)

        # setup default display images
        if widget.button == Qt.MiddleButton:
            # set up image to be displayed during a drag
            self.drag_proxy_image_path = '/'.join([widget.proxyImageDir, widget.currentImage])
            file_type = self.getJSONData(json_file)['type']

            if file_type in ['texture', 'lighttex']:
                image_path = '/'.join([self.getJSONData(json_file)['data'], widget.currentImage])
                self.drag_image_path = image_path.replace(
                    widget.proxyFileExtension, widget.fileExtension
                )

            elif file_type in ['shader', 'lightrig']:
                self.drag_image_path = self.drag_proxy_image_path
                # potentiall have this be lookfile/macro/etc?

            return LibraryWidget.imageClickedEvent(self, event, widget)

    def getTabDropped(self, widget):
        '''
        returns the panel that the user dropped on...
        nodegraph
        parameter
        '''
        if hasattr(widget, '_ParameterPanel__navigationBar') is True:
            return 'parameter'
        elif hasattr(widget, '_NodegraphWidget__floatingNodeLayer') is True:
            return 'nodegraph'
        else:
            return self.getTabDropped(widget.parent())

    def setupActions(self):
        widget_list = [UI4.App.Tabs.FindTopTab('Node Graph')]
        self.add_drop_action(widget_list, self.test)
    
    def test(self):
        print ("api test")
        return

    def eventFilter(self, obj, event, *args, **kwargs):
        if event.type() in (
            QEvent.DragEnter,
            QEvent.DragMove,
            QEvent.Drop
        ):
            def importShader(json_file):
                # import katana file into node graph
                # This might need to go to -1 index?
                if tab_dropped == 'nodegraph':
                    import_type = None
                    if modifiers == Qt.ControlModifier:
                        # pop up menu for user to select what type of
                        # data to use for Textures/Shader in the Nodegraph
                        popup_type_list = ['shader']
                        json_data = self.getJSONData(json_file)
                        if json_data['type'] in popup_type_list:
                            m = DropMenu(
                                self,
                                data_dir=json_data['data'],
                                data_type=json_data['type']
                            )
                            import_type = m.button_pressed

                    if import_type is None:
                        import_type = 'katana'
                    self.importShaderIntoNodegraph(json_data, import_type=import_type)

            def importTexture(json_file):
                file_list = [str(event.mimeData().data('text/plain'))]
                if tab_dropped == 'nodegraph':
                    import_type = 'single'
                    if modifiers == Qt.ControlModifier:
                        file_dir = self.getJSONData(json_file)['data']
                        file_list = ['/'.join([file_dir, file_path]) for file_path in os.listdir(file_dir)]
                    self.importTextureIntoNodegraph(file_list)

            if event.type() != QEvent.Drop:
                event.acceptProposedAction()
            else:
                modifiers = QApplication.keyboardModifiers()
                pos = QCursor.pos()
                selection_list = self.model.metadata['selected']

                for json_file in selection_list:
                    #self.UndoStack.OpenGroup('Import Library Asset')
                    jsondata = self.getJSONData(json_file)
                    file_type = jsondata['type']
                    widget = qApp.widgetAt(pos)
                    tab_dropped = self.getTabDropped(widget)

                    # import shader
                    if file_type == 'shader':
                        importShader(json_file)

                    elif file_type == 'texture':
                        # current only accepts singular file path...
                        # needs to eventually expand to a list for
                        # multiple file creation
                        importTexture(json_file)

                    elif file_type in ['lighttex', 'lightrig']:
                        def getGafferThreeEditor(widget):
                            if hasattr(widget, '_BaseEditor__mainNode'):
                                return widget
                            else:
                                return getGafferThreeEditor(widget.parent())

                        if tab_dropped == 'nodegraph':
                            node_graph = UI4.App.Tabs.FindTopTab('Node Graph')
                            name = self.getJSONData(json_file)['name']
                            parentNode = node_graph.getEnteredGroupNode()
                            node = NodegraphAPI.CreateNode('GafferThree', parentNode)
                            node.setName(name)
                            node_graph.floatNodes([node])

                        elif tab_dropped == 'parameter':
                            # Import into GafferThree
                            gafferThree_editor = getGafferThreeEditor(widget)
                            node = gafferThree_editor._BaseEditor__mainNode
                        self.importRig(json_file, node)
                    self.view_layout.setCurrentIndex(0)
                self.model.metadata['selected'] = []
                self.model.updateViews()

            return True
        return QLabel.eventFilter(self, obj, event, *args, **kwargs)


class DropMenu(QDialog):
    '''
    Popup menu that is displayed when a user CTRL+Drag/Drops into
    the Nodegraph.  This will popup options for the user, if there are
    multiple options for them to select from.
    '''
    def __init__(
        self,
        parent=None,
        data_dir='',
        data_type=''
    ):
        super(DropMenu, self).__init__(parent)

        # set transparent bg
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setWindowFlags(
            self.windowFlags()
            ^ Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        # set initial position
        pos = QCursor().pos()
        geo = self.geometry()
        self.setGeometry(pos.x(), pos.y(), geo.width(), geo.height())

        # set up gui
        layout = QVBoxLayout()
        self.setLayout(layout)

        something_list = os.listdir(data_dir)
        if data_type == 'shader':
            something_list.append('.material')
            something_list.append('.subnet')

        for x in something_list:
            text = x[x.rindex('.')+1:]
            button = TestButton(parent=self, text=text)
            layout.addWidget(button, QMessageBox.YesRole)
            style_sheet = "border:none"
            button.setStyleSheet(style_sheet)

        self.retval = self.exec_()

    def setButtonPressed(self, button):
        self.button_pressed = button.text()


class TestButton(QPushButton):
    def __init__(self, parent=None, text=''):
        super(TestButton, self).__init__(parent)
        self.setText(text)

    def mousePressEvent(self, *args, **kwargs):
        self.parent().setButtonPressed(self)
        self.parent().close()
        # return QtWidgets.QPushButton.mousePressEvent(self, *args, **kwargs)