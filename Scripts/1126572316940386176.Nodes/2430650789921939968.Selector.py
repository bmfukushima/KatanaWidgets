"""
TODO
    *   Connect to single port
            - show prompt if connected
    *   Node Colors
            - Change node glow color
    *   Node Name
            Add node name to top of selection



"""
from qtpy.QtCore import Qt, QPoint
from qtpy.QtGui import QCursor

from Katana import Utils, QT4Widgets, QT4GLLayerStack, NodegraphAPI, DrawingModule, ResourceFiles, KatanaPrefs, logging, PrefNames, UI4
from UI4.Tabs.NodeGraphTab.Layers.TransientLayer import TransientLayer
from UI4.Tabs.NodeGraphTab.Layers.LinkConnectionLayer import LinkConnectionLayer

from cgwidgets.widgets import ButtonInputWidgetContainer
from cgwidgets.utils import centerWidgetOnCursor, setAsPopup, setAsTransparent
from Utils2 import nodeutils

main_window = UI4.App.MainWindow.CurrentMainWindow()

INPUT_PORT = 0
OUTPUT_PORT = 1


class MultiPortPopupMenu(ButtonInputWidgetContainer):
    """ Popup widget displayed when the user queries a node with multiple inputs

    This will show the user a list of all of the available ports to be selected.
    If no port is currently selected, this will activate a port selection, if one is
    currently selected, then this will connect the ports.

    Args:
        node (node): node
        ports (list): of ports
        port_type (PORT_TYPE): the type of ports that will be displayed to the user
        selected_port (port): port currently selected

    """
    def __init__(self, node, port_type=OUTPUT_PORT, selected_port=None,  parent=None):
        super(MultiPortPopupMenu, self).__init__(parent, Qt.Vertical)

        # setup attrs
        self._selected_port = selected_port
        self._node = node
        self._port_type = port_type
        self.setIsToggleable(False)

        for port in self.getDisplayPorts():
            self.addButton(port.getName(), port.getName(), self.portSelectedEvent)

        setAsTransparent(self)

        nodeutils.setGlowColor(node, (0.5, 0.5, 1))

    """ EVENTS """
    def closeEvent(self, event):
        main_window.activateWindow()
        nodeutils.setGlowColor(self._node, None)
        ButtonInputWidgetContainer.closeEvent(self, event)

    def leaveEvent(self, event):
        self.close()
        ButtonInputWidgetContainer.leaveEvent(self, event)

    def showEvent(self, event):
        return_val = ButtonInputWidgetContainer.showEvent(self, event)
        if self.width() < 100:
            self.setFixedWidth(100)

        return return_val

    def portSelectedEvent(self, widget):
        """ Event run when the user selects a port"""
        port = self.getSelectedPort(widget.flag())

        # connect selected ports
        if self._port_type == INPUT_PORT:
            self._selected_port.connect(port)

        # show noodle
        elif self._port_type == OUTPUT_PORT:
            NodeConnector.showNoodle(port)

        self.close()

    """ UTILS """
    def getDisplayPorts(self):
        if self._port_type == INPUT_PORT:
            ports = self._node.getInputPorts()
        elif self._port_type == OUTPUT_PORT:
            ports = self._node.getOutputPorts()

        return ports

    def getSelectedPort(self, port_name):
        """ Gets the port from the port name provided

        Args:
            port_name (str): """
        if self._port_type == INPUT_PORT:
            port = self._node.getInputPort(port_name)
        elif self._port_type == OUTPUT_PORT:
            port = self._node.getOutputPort(port_name)

        return port


class NodeConnector():
    def __init__(self):
        self.output_port = None
        self.main()

    def main(self):
        nodegraph_tab = UI4.App.Tabs.FindTopTab('Node Graph')
        nodegraph_widget = nodegraph_tab.getNodeGraphWidget()
        node = nodeutils.getClosestNode()
        graph_interaction = nodegraph_widget.getGraphInteraction()

        # has not selected a port yet
        if graph_interaction is True:
            # no port selected yet...
            if len(node.getOutputPorts()) == 1:
                self.output_port = node.getOutputPorts()[0]
                self.showNoodle(self.output_port)
            elif len(node.getOutputPorts()) > 1:
                main_window._port_popup_menu = MultiPortPopupMenu(node)
                main_window._port_popup_menu.show()
                centerWidgetOnCursor(main_window._port_popup_menu)

        elif graph_interaction is False:
            link_connection_layer = nodegraph_widget.getLayers()[-1]
            if isinstance(link_connection_layer, LinkConnectionLayer):
                base_ports = link_connection_layer.getBasePorts()

                if len(node.getInputPorts()) == 1:
                    for base_port in base_ports:
                        node.getInputPortByIndex(0).connect(base_port)

                elif len(node.getInputPorts()) > 1:
                    main_window._port_popup_menu = MultiPortPopupMenu(node, port_type=INPUT_PORT, selected_port=base_ports[0])
                    main_window._port_popup_menu.show()
                    centerWidgetOnCursor(main_window._port_popup_menu)

                    # action = 'linkConnectionPortChosen'
                    #self.showMultiPopupMenu(node, True, action=action)

                nodegraph_widget.idleUpdate()
                nodegraph_widget.removeLayer(link_connection_layer)
            # port is selected... so do this

    @staticmethod
    def showNoodle(port):
        """ Shows the noodle from the port provided

        Args:
            port (Port): """
        nodegraph_tab = UI4.App.Tabs.FindTopTab('Node Graph')
        nodegraph_widget = nodegraph_tab.getNodeGraphWidget()
        port_layer = nodegraph_widget.getLayerByName("PortInteractions")

        ls = port_layer.layerStack()
        layer = LinkConnectionLayer([port], None, enabled=True)
        ls.appendLayer(layer, stealFocus=True)


    def showMultiPopupMenu(self, node, input, action=None):
        NodegraphTab = UI4.App.Tabs.FindTopTab('Node Graph')
        widget = NodegraphTab._NodegraphPanel__nodegraphWidget
        layer = widget._NodegraphWidget__structuredPortsNodeInteractionLayer
        mouse_pos = widget._LayerStack__mousePos
        #mousePos = QtGui.QCursor.pos()
        menu = layer.getPortMenu()
        layer.fillPortMenu(menu, node, input)

        layer.showPortMenu(mouse_pos, node, action=action)


nc = NodeConnector()

# Embedded file name: bin/python/UI4/Tabs/NodeGraphTab/Layers/TransientLayer.py
# Embedded file name: bin/python/UI4/Tabs/NodeGraphTab/Layers/LinkConnectionLayer.py

# __all__ = [
#     'LinkConnectionLayer']
# log = logging.getLogger('LinkConnectionLayer')
# PortDescription = collections.namedtuple('PortDescription', [
#     'node', 'type', 'name',
#     'isSendOrReturnPort'])

# class TransientLayer(QT4GLLayerStack.Layer):
#
#     def __init__(self, name=None, visible=False, interactive=False, enabled=False):
#         """
#         Initializes an instance of the class.
#
#         @type name: C{str} or C{None}
#         @type visible: C{bool}
#         @type interactive: C{bool}
#         @type enabled: C{bool}
#         @param name: A name to use for the layer, or C{None} to not name the
#             layer.
#         @param visible: Flag to control whether the layer is visible within its
#             layer stack.
#         @param interactive: Flag to control whether the layer can be used by a
#             user interactively.
#         @param enabled: Flag that controls whether the layer is available for
#             users to interact with.
#         """
#         QT4GLLayerStack.Layer.__init__(self, name, visible, interactive, enabled)
#         self.__savedInteraction = False
#
#     def setLayerStack(self, stack):
#         if self.layerStack():
#             self.layerStack().setGraphInteraction(self.__savedInteraction)
#         if stack:
#             self.__savedInteraction = stack.getGraphInteraction()
#             stack.setGraphInteraction(False)
#         QT4GLLayerStack.Layer.setLayerStack(self, stack)


# class LinkConnectionLayer(TransientLayer):
#     __pixmaps = {}
#
#     def __init__(self, basePorts, savedLinks, disableScenegraphUpdates=False, *args, **kwargs):
#         TransientLayer.__init__(self, *args, **kwargs)
#         self.__basePorts = []
#         for port in list(basePorts):
#             if port is None or port.getNode() is None:
#                 raise ValueError('Invalid port given: %s' % port)
#             self.__basePorts.append(self.__getPortDescription(port))
#
#         if not savedLinks:
#             self.__savedLinks = []
#         else:
#             self.__savedLinks = savedLinks
#             if self.__savedLinks:
#                 for portA, portB in self.__savedLinks:
#                     DrawingModule.nodeShape_setPortLinkHidden(portA, portB)
#
#         self.__preselectPort = None
#         self.__preselectLink = None
#         self.__menu = QtWidgets.QMenu()
#         #self.__menu.connect(self.__menu, QtCore.Qt.SIGNAL('triggered(QAction*)'), self.__menuCallback)
#         self.__menuNodeName = ''
#         if not self.__pixmaps:
#             self.__pixmaps['linkArrow'] = QtGui.QPixmap(ResourceFiles.GetIconPath('linkArrow.png'))
#         Utils.EventModule.RegisterEventHandler(self.__nodeDeleteHandler, 'node_delete', None, True)
#         self.__startTime = time.time()
#         DrawingModule.nodeWorld_setLargePortAreaEnabled(True)
#         basePorts = self.getBasePorts()
#         if basePorts:
#             DrawingModule.nodeWorld_setLargePortAreaIncludeTypes(basePorts[0].getType() == NodegraphAPI.Port.TYPE_PRODUCER, basePorts[0].getType() == NodegraphAPI.Port.TYPE_CONSUMER)
#         return
#
#     def __del__(self):
#         DrawingModule.nodeWorld_setLargePortAreaEnabled(False)
#         if self.__savedLinks:
#             DrawingModule.nodeShape_clearAllHiddenPortLinks()
#
#     def getBasePorts(self):
#         """
#         @rtype: C{list} of C{NodegraphAPI.Port}
#         @return: A list of C{Port} objects representing the ports that sit at
#             either end of the node connection that is represented and drawn by
#             this layer. This list typically contains two ports, but may contain
#             only one port if the user is in the process of creating a
#             connection from a particular port.
#         """
#         result = []
#         for portDescription in self.__basePorts:
#             if portDescription.type == NodegraphAPI.Port.TYPE_PRODUCER:
#                 if portDescription.isSendOrReturnPort:
#                     getPortFunction = portDescription.node.getSendPort
#                     portTypeName = 'Send'
#                 else:
#                     getPortFunction = portDescription.node.getOutputPort
#                     portTypeName = 'Output'
#             else:
#                 if portDescription.isSendOrReturnPort:
#                     getPortFunction = portDescription.node.getReturnPort
#                     portTypeName = 'Return'
#                 else:
#                     getPortFunction = portDescription.node.getInputPort
#                     portTypeName = 'Input'
#             port = getPortFunction(portDescription.name)
#             if port is not None:
#                 result.append(port)
#             else:
#                 log.warning('LinkConnectionLayer.getBasePorts(): %s port "%s" no longer exists on node "%s".' % (
#                  portTypeName, portDescription.name,
#                  portDescription.node.getName()))
#
#         return result
#
#     def paintGL(self):
#         self.layerStack().applyWorldSpace()
#         mousePoint = self.layerStack().mapFromGlobal(QtGui.QCursor.pos())
#         mousePoint = self.layerStack().mapFromQTLocalToWorld(mousePoint.x(), mousePoint.y())
#         if self.__preselectPort is not None:
#             DrawingModule.nodeWorld_drawSelectedPort(self.layerStack().getCurrentNodeView(), self.__preselectPort, self.layerStack().getViewScale()[0])
#             for port in self.getBasePorts():
#                 DrawingModule.nodeWorld_drawSelectedPort(self.layerStack().getCurrentNodeView(), port, self.layerStack().getViewScale()[0])
#
#         if self.__preselectLink is not None:
#             DrawingModule.nodeWorld_drawSelectedLink(self.layerStack().getCurrentNodeView(), self.__preselectLink[0], self.__preselectLink[1], self.layerStack().getViewScale()[0])
#         if self.__preselectPort:
#             floatingLinkColor = (0.65, 0.65, 0.45, 1.0)
#             floatingLinkOutlineColor = (0, 0, 0, 1)
#         else:
#             floatingLinkColor = (0.35, 0.35, 0.35, 1.0)
#             floatingLinkOutlineColor = (0, 0, 0, 1)
#         for port in self.getBasePorts():
#             DrawingModule.nodeWorld_drawFloatingLink(self.layerStack().getCurrentNodeView(), port, mousePoint[0], mousePoint[1], self.layerStack().getViewScale()[0])
#
#         return
#
#     def processEvent(self, event):
#         if event.type() == QtCore.QEvent.MouseMove:
#             return self.__processMouseMove(event)
#         if event.type() == QtCore.QEvent.MouseButtonPress:
#             return self.__processMousePress(event)
#         if event.type() == QtCore.QEvent.MouseButtonRelease:
#             if time.time() - self.__startTime < 0.25:
#                 return
#             return self.__processMousePress(event)
#         if event.type() == QtCore.QEvent.KeyPress:
#             return self.__processKeyPress(event)
#         if isinstance(event, QT4Widgets.GlobalEventFilter.UnfocusedKeyEvent):
#             if event.data().type() == QtCore.QEvent.KeyPress:
#                 return self.__processKeyPress(event.data())
#             return False
#         return False
#
#     def __processMouseMove(self, event):
#         self.__preselectPort = None
#         self.__preselectLink = None
#         basePorts = self.getBasePorts()
#         if not basePorts:
#             self.__exitNoChange()
#             return True
#         clickPoint = self.layerStack().mapFromQTLocalToWorld(event.x(), event.y())
#         if event.modifiers() & QtCore.Qt.ShiftModifier:
#             hitLink = None
#             result = self.layerStack().hitTestForType(clickPoint, 'LINK')
#             if result:
#                 hitLink = (result[1]['portA'], result[1]['portB'])
#             if hitLink is None or type(hitLink[0]) != NodegraphAPI.Port:
#                 self.layerStack().idleUpdate()
#                 return True
#             if basePorts[0].getType() == NodegraphAPI.Port.TYPE_CONSUMER and hitLink[1].getType() == NodegraphAPI.Port.TYPE_CONSUMER:
#                 self.__preselectLink = hitLink
#         else:
#             hitPort = None
#             result = self.layerStack().hitTestForType(clickPoint, 'PORT')
#             if result:
#                 hitPort = result[1]['portA']
#             if hitPort is not None and self.__isConnectionViable(basePorts[0], hitPort):
#                 self.__preselectPort = hitPort
#             else:
#                 if basePorts[0].getType() == NodegraphAPI.Port.TYPE_PRODUCER:
#                     node = self.layerStack().hitTestForTypeWithOptions(clickPoint, 'PORTNEW', 'node')
#                     if node and node != basePorts[0].getNode() and not NodegraphAPI.IsNodeLockedByParents(node):
#                         DrawingModule.nodeWorld_setShapeAttr(node, 'hilite', 'PORTNEWHILITE')
#         self.layerStack().idleUpdate()
#         return False
#
#     def processMousePress(self, event):
#         return False
#
#     def __processMousePress(self, event):
#         if self.processMousePress(event):
#             return True
#         basePorts = self.getBasePorts()
#         if not basePorts:
#             self.__exitNoChange()
#             return True
#         if event.button() == QtCore.Qt.LeftButton:
#             clickPoint = self.layerStack().mapFromQTLocalToWorld(event.x(), event.y())
#             if not event.modifiers() & QtCore.Qt.ShiftModifier:
#                 Utils.UndoStack.OpenGroup()
#                 connectPort = None
#                 hitPort = None
#                 result = self.layerStack().hitTestForType(clickPoint, 'PORT')
#                 if result:
#                     hitPort = result[1]['portA']
#                 else:
#                     sourcePortType = basePorts[0].getType()
#                     if sourcePortType == NodegraphAPI.Port.TYPE_PRODUCER:
#                         node = self.layerStack().hitTestForTypeWithOptions(clickPoint, 'PORTNEW', 'node')
#                         if node:
#                             if NodegraphAPI.IsNodeLockedByParents(node):
#                                 return False
#                             try:
#                                 for inputPort in node.getInputPorts():
#                                     if inputPort.getNumConnectedPorts() == 0:
#                                         hitPort = inputPort
#                                         break
#                                 else:
#                                     hitPort = node.addInputPort('i%d' % node.getNumInputPorts())
#
#                             finally:
#                                 DrawingModule.nodeWorld_setShapeAttr(node, 'hilite', '')
#
#                     else:
#                         if sourcePortType == NodegraphAPI.Port.TYPE_CONSUMER:
#                             node = self.layerStack().hitTestForTypeWithOptions(clickPoint, 'PORTMULTIOUT', 'node')
#                             if node:
#                                 if NodegraphAPI.IsNodeLockedByParents(node):
#                                     return False
#                                 mergeLayer = self.layerStack().getLayerByName('Merge Node Interaction')
#                                 mergeLayer.addMultiOutPopupCallback(self.__multiOutPopupCallback)
#                                 return False
#                 if hitPort is None:
#                     self.__dropLinks()
#                     Utils.UndoStack.CloseGroup()
#                 else:
#                     if self.__isConnectionViable(basePorts[0], hitPort):
#                         self.__connectLinks(hitPort)
#                         Utils.UndoStack.CloseGroup()
#                     else:
#                         self.__dropLinks()
#                         Utils.UndoStack.CloseGroup(discard=True)
#                 return True
#             hitLink = None
#             result = self.layerStack().hitTestForType(clickPoint, 'LINK')
#             if result:
#                 portA = result[1]['portA']
#                 portB = result[1]['portB']
#                 hitLink = (portA, portB)
#             if hitLink is None:
#                 return True
#             if type(portA) != NodegraphAPI.Port:
#                 return True
#             nodeA = portA.getNode()
#             if NodegraphAPI.IsNodeLockedByParents(nodeA):
#                 return False
#             nodeB = portB.getNode()
#             if nodeA and nodeB and nodeA.isLocked() and nodeB.isLocked():
#                 return False
#             if basePorts[0].getType() == NodegraphAPI.Port.TYPE_CONSUMER and portB.getType() == NodegraphAPI.Port.TYPE_CONSUMER:
#                 self.__savedLinks.append(hitLink)
#                 self.__basePorts.append(self.__getPortDescription(portB))
#                 portA.disconnect(portB)
#                 self.layerStack().idleUpdate()
#             return True
#         if event.button() == QtCore.Qt.RightButton:
#             clickPoint = self.layerStack().mapFromQTLocalToWorld(event.x(), event.y())
#             result = self.layerStack().hitTestPoint(clickPoint)
#             if result:
#                 node = result[0][1].get('node', None)
#                 if node and not NodegraphAPI.IsNodeLockedByParents(node):
#                     self.__menu.clear()
#                     if basePorts[0].getType() == NodegraphAPI.Port.TYPE_PRODUCER:
#                         for port in node.getInputPorts():
#                             if port.getNumConnectedPorts():
#                                 self.__menu.addAction(QtGui.QIcon(self.__pixmaps['linkArrow']), port.getName())
#                             else:
#                                 self.__menu.addAction(port.getName())
#
#                     else:
#                         for port in node.getOutputPorts():
#                             self.__menu.addAction(port.getName())
#
#                     self.__menuNodeName = node.getName()
#                     globalPos = self.layerStack().mapToGlobal(QtCore.QPoint(event.x(), event.y()))
#                     self.__menu.popup(globalPos)
#                     return True
#         return False
#
#     def __multiOutPopupCallback(self, port):
#         self.__connectLinks(port)
#
#     def __menuCallback(self, mId):
#         index = self.__menu.actions().index(mId)
#         node = NodegraphAPI.GetNode(self.__menuNodeName)
#         if not node:
#             return
#         basePorts = self.getBasePorts()
#         if basePorts and basePorts[0].getType() == NodegraphAPI.Port.TYPE_PRODUCER:
#             port = node.getInputPortByIndex(index)
#         else:
#             port = node.getOutputPortByIndex(index)
#         if not port:
#             return
#         self.__connectLinks(port)
#
#     def __processKeyPress(self, event):
#         if event.modifiers() != QtCore.Qt.NoModifier:
#             return False
#         key = event.key()
#         try:
#             text = str(event.text()).lower()
#         except UnicodeEncodeError:
#             text = None
#
#         if key == QtCore.Qt.Key_Escape:
#             self.__exitNoChange()
#             self.__menu.close()
#             return True
#         if key == QtCore.Qt.Key_Period:
#             if not event.isAutoRepeat():
#                 return self.__create_dot_node()
#             return False
#         if key == QtCore.Qt.Key_QuoteLeft:
#             if event.isAutoRepeat():
#                 return
#             mousePoint = self.layerStack().getMousePos()
#             if not mousePoint:
#                 return False
#             mousePoint = self.layerStack().mapFromQTLocalToWorld(mousePoint.x(), mousePoint.y())
#             result = self.layerStack().hitTestPoint(mousePoint)
#             if result:
#                 useport = None
#                 node = result[0][1].get('node', None)
#                 if node and not DrawingModule.nodeWorld_getShapeAttrAsNumber(node, 'suppressPortKeys'):
#                     if NodegraphAPI.IsNodeLockedByParents(node):
#                         return False
#                     useport = None
#                     for i in xrange(0, node.getNumInputPorts()):
#                         port = node.getInputPortByIndex(i)
#                         if port and not port.getNumConnectedPorts():
#                             useport = port
#                             break
#
#                 if not useport and DrawingModule.nodeWorld_getShapeAttrAsNumber(node, 'inputPortDynamic'):
#                     if node.isLocked(True):
#                         return False
#                     node.addInputPort('i' + str(node.getNumInputPorts()))
#                     useport = node.getInputPortByIndex(node.getNumInputPorts() - 1)
#                 if useport:
#                     self.__connectLinks(useport)
#                     DrawingModule.nodeWorld_setShapeAttr(node, 'hilite', '')
#                     return True
#         if not text.isdigit():
#             return False
#         portNumber = int(text) - 1
#         if portNumber < 0:
#             return False
#         mousePoint = self.layerStack().getMousePos()
#         if not mousePoint:
#             return False
#         mousePoint = self.layerStack().mapFromQTLocalToWorld(mousePoint.x(), mousePoint.y())
#         hitNode = None
#         result = self.layerStack().hitTestPoint(mousePoint)
#         if result:
#             hitNode = result[0][1].get('node', None)
#         else:
#             return False
#         if DrawingModule.nodeWorld_getShapeAttrAsNumber(hitNode, 'suppressPortKeys'):
#             return False
#         connectPort = None
#         basePorts = self.getBasePorts()
#         if basePorts and basePorts[0].getType() == NodegraphAPI.Port.TYPE_PRODUCER:
#             if portNumber >= hitNode.getNumInputPorts():
#                 return False
#             connectPort = hitNode.getInputPorts()[portNumber]
#         else:
#             if portNumber >= hitNode.getNumOutputPorts():
#                 return False
#             connectPort = hitNode.getOutputPorts()[portNumber]
#         self.__connectLinks(connectPort)
#         return True
#
#     def __exitNoChange(self):
#         self.layerStack().idleUpdate()
#         self.layerStack().removeLayer(self)
#         return True
#
#     def __dropLinks(self):
#         if self.__savedLinks:
#             for link in self.__savedLinks:
#                 link[0].disconnect(link[1])
#
#         self.layerStack().idleUpdate()
#         self.layerStack().removeLayer(self)
#         return True
#
#     def __connectLinks(self, targetPort):
#         basePorts = self.getBasePorts()
#         if self.__savedLinks:
#             for ports in self.__savedLinks:
#                 if ports[0] == targetPort:
#                     origBase = ports[1]
#                 else:
#                     if ports[1] == targetPort:
#                         origBase = ports[0]
#                     else:
#                         origBase = None
#                 if origBase and origBase in basePorts:
#                     self.__exitNoChange()
#                     return
#
#             for link in self.__savedLinks:
#                 link[0].disconnect(link[1])
#
#         targetNode = targetPort.getNode()
#         for port in basePorts:
#             consumerPort = port
#             producerPort = targetPort
#             if targetPort.getType() == NodegraphAPI.Port.TYPE_CONSUMER:
#                 consumerPort = targetPort
#                 producerPort = port
#             consumerNode = consumerPort.getNode()
#             producerNode = producerPort.getNode()
#             if consumerPort.getNumConnectedPorts():
#                 connectedPort = consumerPort.getConnectedPort(0)
#                 if connectedPort.getNode().getParent() != consumerNode.getParent():
#                     continue
#             port.connect(targetPort)
#
#         self.layerStack().idleUpdate()
#         self.layerStack().removeLayer(self)
#         return
#
#     def __nodeDeleteHandler(self, eventType, eventID, node, *args, **kwargs):
#         self.__preselectPort = None
#         self.__preselectLink = None
#         self.__savedLinks = []
#         self.__basePorts = []
#         return
#
#     def __create_dot_node(self):
#         Utils.OpenGLTraceMarker.begin()
#         basePorts = self.getBasePorts()
#         if not basePorts:
#             Utils.OpenGLTraceMarker.end()
#             return False
#         if len(basePorts) != 1 and basePorts[0].getType() == NodegraphAPI.Port.TYPE_PRODUCER:
#             Utils.OpenGLTraceMarker.end()
#             return False
#         if NodegraphAPI.IsNodeLockedByParents(basePorts[0].getNode()):
#             Utils.OpenGLTraceMarker.end()
#             return False
#         mousePos = self.layerStack().getMousePos()
#         if not mousePos:
#             return False
#         mousePos = self.layerStack().mapFromQTLocalToWorld(mousePos.x(), mousePos.y())
#         rootview = self.layerStack().getCurrentNodeView()
#         rootviewscale = self.layerStack().getViewScale()[0]
#         parentNode = DrawingModule.nodeWorld_findGroupNodeOfClick(rootview, mousePos[0], mousePos[1], rootviewscale)
#         if parentNode is not None and parentNode.isContentLocked():
#             Utils.OpenGLTraceMarker.end()
#             return False
#         a, r, x, y = DrawingModule.nodeWorld_getGroupNodeRelativeAndAbsoluteChildScales(rootview, parentNode, rootviewscale, mousePos[0], mousePos[1])
#         Utils.UndoStack.OpenGroup('Create Dot Node')
#         try:
#             dot = NodegraphAPI.CreateNode('Dot', parentNode)
#             if KatanaPrefs[PrefNames.NODEGRAPH_GRIDSNAP]:
#                 GRIDSIZEX = 32
#                 GRIDSIZEY = 16
#                 xmod = x % GRIDSIZEX
#                 if xmod > GRIDSIZEX / 2.0:
#                     xmod = (GRIDSIZEX - xmod) * -1
#                 ymod = y % GRIDSIZEY
#                 if ymod > GRIDSIZEY / 2.0:
#                     ymod = (GRIDSIZEY - ymod) * -1
#                 x -= xmod
#                 y -= ymod
#             NodegraphAPI.SetNodePosition(dot, (x, y))
#             if basePorts[0].getType() == NodegraphAPI.Port.TYPE_PRODUCER:
#                 basePorts[0].connect(dot.getInputPortByIndex(0))
#                 outputPort = dot.getOutputPortByIndex(0)
#                 self.__basePorts = [
#                  self.__getPortDescription(outputPort, False)]
#             else:
#                 for port in basePorts:
#                     port.connect(dot.getOutputPortByIndex(0))
#
#                 inputPort = dot.getInputPortByIndex(0)
#                 self.__basePorts = [
#                  self.__getPortDescription(inputPort, False)]
#             return True
#         finally:
#             Utils.UndoStack.CloseGroup()
#
#         Utils.OpenGLTraceMarker.end()
#         return
#
#     def __isConnectionViable(self, portA, portB):
#         """
#         @type portA: C{NodegraphAPI.Port} or C{None}
#         @type portB: C{NodegraphAPI.Port} or C{None}
#         @rtype: C{bool}
#         @param portA: The source port of the connection to check.
#         @param portB: The target port of the connection to check.
#         @return: C{True} if a connection between the given ports is possible
#             and allowed, otherwise C{False}.
#         @note: Does not perform a cyclic node graph check.
#         """
#         if portA is None or portB is None:
#             return False
#         sourcePortType = portA.getType()
#         targetPortType = portB.getType()
#         if sourcePortType == targetPortType:
#             return False
#         targetNode = portB.getNode()
#         if NodegraphAPI.IsNodeLockedByParents(targetNode):
#             return False
#         sourceNode = portA.getNode()
#         if isinstance(sourceNode, NodegraphAPI.GroupNode):
#             sourcePortName = portA.getName()
#             isSourcePortSendPort = sourcePortType == NodegraphAPI.Port.TYPE_PRODUCER and sourceNode is not None and sourceNode.getSendPort(sourcePortName) is not None
#             isSourcePortReturnPort = sourcePortType == NodegraphAPI.Port.TYPE_CONSUMER and sourceNode is not None and sourceNode.getReturnPort(sourcePortName) is not None
#         else:
#             isSourcePortSendPort = False
#             isSourcePortReturnPort = False
#         if isinstance(targetNode, NodegraphAPI.GroupNode):
#             targetPortName = portB.getName()
#             isTargetPortSendPort = targetPortType == NodegraphAPI.Port.TYPE_PRODUCER and targetNode is not None and targetNode.getSendPort(targetPortName) is not None
#             isTargetPortReturnPort = targetPortType == NodegraphAPI.Port.TYPE_CONSUMER and targetNode is not None and targetNode.getReturnPort(targetPortName) is not None
#         else:
#             isTargetPortSendPort = False
#             isTargetPortReturnPort = False
#         if sourceNode == targetNode:
#             return isSourcePortSendPort and isTargetPortReturnPort or isSourcePortReturnPort and isTargetPortSendPort
#         if isSourcePortSendPort or isSourcePortReturnPort:
#             if not isTargetPortSendPort and not isTargetPortReturnPort:
#                 parentNode = targetNode.getParent()
#                 while parentNode is not None:
#                     if parentNode == sourceNode:
#                         return True
#                     parentNode = parentNode.getParent()
#
#             return False
#         if isTargetPortSendPort or isTargetPortReturnPort:
#             if not isSourcePortSendPort and not isSourcePortReturnPort:
#                 parentNode = sourceNode.getParent()
#                 while parentNode is not None:
#                     if parentNode == targetNode:
#                         return True
#                     parentNode = parentNode.getParent()
#
#             return False
#         return True
#
#     def __getPortDescription(self, port, isSendOrReturnPort=None):
#         """
#         @type port: C{NodegraphAPI.Port}
#         @type isSendOrReturnPort: C{bool} or C{None}
#         @rtype: C{PortDescription}
#         @param port: The port for which to return a description.
#         @param isSendOrReturnPort: Flag that indicates whether the given port
#             is a send or return port of a Group or Group-like node. If C{None},
#             the L{__isSendOrReturnPort()} function is used to determine the
#             value of this flag to be returned as part of the resulting port
#             description.
#         @return: A description of the given port, which can be used to obtain
#             the port again.
#         """
#         if isSendOrReturnPort is None:
#             isSendOrReturnPort = self.__isSendOrReturnPort(port)
#         return PortDescription(port.getNode(), port.getType(), port.getName(), isSendOrReturnPort)
#
#     def __isSendOrReturnPort(self, port):
#         """
#         @type port: C{NodegraphAPI.Port}
#         @rtype: C{bool}
#         @param port: The port to check.
#         @return: C{True} if the given port is a send or return port of a Group
#             or Group-like (e.g. LiveGroup, SuperTool) node, otherwise C{False}.
#         @raise ValueError: If the given port is not part of a node, or if the
#             given port cannot be obtained from its node by its name.
#         """
#         node = port.getNode()
#         if node is None:
#             raise ValueError('Given port is not part of a node: %r' % port)
#         if not isinstance(node, NodegraphAPI.GroupNode):
#             return False
#         portType = port.getType()
#         portName = port.getName()
#         if portType == NodegraphAPI.Port.TYPE_PRODUCER:
#             if port == node.getSendPort(portName):
#                 return True
#             if port == node.getOutputPort(portName):
#                 return False
#             raise ValueError('Invalid producer port given: %r' % port)
#         else:
#             if port == node.getReturnPort(portName):
#                 return True
#             if port == node.getInputPort(portName):
#                 return False
#             raise ValueError('Invalid consumer port given: %r' % port)
#         return
    

