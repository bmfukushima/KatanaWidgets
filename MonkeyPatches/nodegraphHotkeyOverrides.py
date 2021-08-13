"""
TODO for some reason I can't monkey patch the Nodegraph... =/


"""



from Katana import time, QtCore, QtGui, cStringIO, sys, os, logging, math, Utils, FnKatImport, QT4Widgets, QT4GLLayerStack, ResourceFiles, QT4FormWidgets, NodegraphAPI, Nodes2DAPI, Nodes3DAPI, GeoAPI, DrawingModule, RenderManager, KatanaPrefs, PrefNames, FarmAPI, NodeDebugOutput, ExpressionMath

from UI4.Manifest import CacheManager, QtWidgets, RenderingAPI
from NodegraphAPI import BypassParameterManager

#from UI4.Tabs.NodeGraphTab.Layers import NodeInteractionLayer, LinkConnectionLayer
from UI4.Tabs.NodeGraphTab.Layers.NodeInteractionLayer import NodeInteractionLayer

def __processKeyPress(self, event):
    print ("=============================== KEY PRESS EVENT")
    key = event.key()
    try:
        text = str(event.text()).lower()
    except UnicodeEncodeError:
        text = ''

    isNoModifierPressed = event.modifiers() == QtCore.Qt.NoModifier
    isAltOnlyModifier = event.modifiers() == QtCore.Qt.AltModifier
    isCtrlOnlyModifier = event.modifiers() == QtCore.Qt.ControlModifier
    isShiftOnlyModifier = event.modifiers() == QtCore.Qt.ShiftModifier
    if isNoModifierPressed and key == QtCore.Qt.Key_Delete:
        if not NodegraphAPI.GetAllFloatingNodes():
            self.__deleteNodes(NodegraphAPI.GetAllSelectedNodes())
        return True
    if isNoModifierPressed and key == QtCore.Qt.Key_Tab:
        self.__launchNodeCreationMenuLayer()
        return True
    else:
        if isAltOnlyModifier and key == QtCore.Qt.Key_Up:
            if event.isAutoRepeat():
                Utils.UndoStack.DisableCapture()
            else:
                Utils.UndoStack.OpenGroup('Nudge Nodes')
            try:
                for node in NodegraphAPI.GetAllSelectedNodes():
                    if node.isLocked(True):
                        continue
                    pos = NodegraphAPI.GetNodePosition(node)
                    NodegraphAPI.SetNodePosition(node, (pos[0], pos[1] + 1))

            finally:
                if event.isAutoRepeat():
                    Utils.UndoStack.EnableCapture()
                else:
                    Utils.UndoStack.CloseGroup()

            return True
        if isAltOnlyModifier and key == QtCore.Qt.Key_Down:
            if event.isAutoRepeat():
                Utils.UndoStack.DisableCapture()
            else:
                Utils.UndoStack.OpenGroup('Nudge Nodes')
            try:
                for node in NodegraphAPI.GetAllSelectedNodes():
                    if node.isLocked(True):
                        continue
                    pos = NodegraphAPI.GetNodePosition(node)
                    NodegraphAPI.SetNodePosition(node, (pos[0], pos[1] - 1))

            finally:
                if event.isAutoRepeat():
                    Utils.UndoStack.EnableCapture()
                else:
                    Utils.UndoStack.CloseGroup()

            return True
        if isAltOnlyModifier and key == QtCore.Qt.Key_Left:
            if event.isAutoRepeat():
                Utils.UndoStack.DisableCapture()
            else:
                Utils.UndoStack.OpenGroup('Nudge Nodes')
            try:
                for node in NodegraphAPI.GetAllSelectedNodes():
                    if node.isLocked(True):
                        continue
                    pos = NodegraphAPI.GetNodePosition(node)
                    NodegraphAPI.SetNodePosition(node, (pos[0] - 1, pos[1]))

            finally:
                if event.isAutoRepeat():
                    Utils.UndoStack.EnableCapture()
                else:
                    Utils.UndoStack.CloseGroup()

            return True
        if isAltOnlyModifier and key == QtCore.Qt.Key_Right:
            if event.isAutoRepeat():
                Utils.UndoStack.DisableCapture()
            else:
                Utils.UndoStack.OpenGroup('Nudge Nodes')
            try:
                for node in NodegraphAPI.GetAllSelectedNodes():
                    if node.isLocked(True):
                        continue
                    pos = NodegraphAPI.GetNodePosition(node)
                    NodegraphAPI.SetNodePosition(node, (pos[0] + 1, pos[1]))

            finally:
                if event.isAutoRepeat():
                    Utils.UndoStack.EnableCapture()
                else:
                    Utils.UndoStack.CloseGroup()

            return True
        if isCtrlOnlyModifier and key == QtCore.Qt.Key_Up:
            nodes = NodegraphAPI.GetAllSelectedNodes()
            inputs = NodegraphAPI.Util.GetAllConnectedInputs(nodes)
            inputs.extend(nodes)
            NodegraphAPI.SetAllSelectedNodes(inputs)
            return True
        if isCtrlOnlyModifier and key == QtCore.Qt.Key_Down:
            nodes = NodegraphAPI.GetAllSelectedNodes()
            outputs = NodegraphAPI.Util.GetAllConnectedOutputs(nodes)
            outputs.extend(nodes)
            NodegraphAPI.SetAllSelectedNodes(outputs)
            return True
        isRenameKeyPressed = isNoModifierPressed and (key == QtCore.Qt.Key_F2 or key == QtCore.Qt.Key_N)
        nodesAreFloating = bool(NodegraphAPI.GetAllFloatingNodes())
        if isRenameKeyPressed and not event.isAutoRepeat() and not nodesAreFloating:
            selectedNodes = NodegraphAPI.GetAllSelectedNodes()
            if len(selectedNodes) == 1:
                if self.__renameNode(selectedNodes[0]):
                    return True
        if isNoModifierPressed and key == QtCore.Qt.Key_N:
            self.layerStack().nodeMenu().exec_(QtGui.QCursor.pos())
            return True
        if isNoModifierPressed and key == QtCore.Qt.Key_F:
            if not event.isAutoRepeat():
                self.frameSelection()
            return True
        if isNoModifierPressed and key == QtCore.Qt.Key_G:
            if not event.isAutoRepeat():
                self.layerStack().collapseSelection()
            return True
        if isAltOnlyModifier and key == QtCore.Qt.Key_G:
            if not event.isAutoRepeat():
                self.layerStack().collapseSelectedToStack()
            return True
        if isNoModifierPressed and key == QtCore.Qt.Key_U:
            if not event.isAutoRepeat():
                self.layerStack().explodeSelection()
            return True
        if isNoModifierPressed and key == QtCore.Qt.Key_Y:
            if not event.isAutoRepeat():
                self.layerStack().alignSelection()
            return True
        if isCtrlOnlyModifier and key == QtCore.Qt.Key_X:
            return False
        if isNoModifierPressed and key == QtCore.Qt.Key_X:
            self.layerStack().extractNodes(NodegraphAPI.GetAllSelectedNodes())
            return True
        if isNoModifierPressed and key == QtCore.Qt.Key_J:
            self.showJumpToBookmark()
            return True
        if isAltOnlyModifier and key == QtCore.Qt.Key_E:
            if not event.isAutoRepeat():
                Utils.UndoStack.OpenGroup('Edit Nodes')
                try:
                    for curnode in NodegraphAPI.GetAllEditedNodes():
                        NodegraphAPI.SetNodeEdited(curnode, False)

                    for node in NodegraphAPI.GetAllSelectedNodes():
                        NodegraphAPI.SetNodeEdited(node, not NodegraphAPI.IsNodeEdited(node))

                finally:
                    Utils.UndoStack.CloseGroup()

            return True
        if isAltOnlyModifier and key == QtCore.Qt.Key_D:
            if not event.isAutoRepeat():
                selectedNodes = NodegraphAPI.GetAllSelectedNodes()
                expressionedNodes = []
                animatedNodes = []
                Utils.UndoStack.OpenGroup('Toggle Disabled State')
                try:
                    for node in selectedNodes:
                        if node.isLocked(True):
                            continue
                        if node.getBaseType() == 'Backdrop':
                            continue
                        if BypassParameterManager.IsBypassedStateControlledByExpression(node):
                            expressionedNodes.append(node)
                            continue
                        if BypassParameterManager.IsBypassedStateAnimated(node):
                            animatedNodes.append(node)
                            continue
                        node.setBypassed(not node.isBypassed())

                finally:
                    Utils.UndoStack.CloseGroup()

                numberOfExpressionedNodes = len(expressionedNodes)
                numberOfAnimatedNodes = len(animatedNodes)
                if numberOfExpressionedNodes == 1 and numberOfAnimatedNodes == 0:
                    if len(selectedNodes) == 1:
                        BypassParameterManager.EditBypassedStateExpression(expressionedNodes[0],
                                                                           parent=self.layerStack().window())
                    else:
                        log.info(
                            'The disabled state of the "%s" node was not toggled, as its state is controlled by a Python expression.' %
                            expressionedNodes[0].getName())
                elif numberOfExpressionedNodes == 0 and numberOfAnimatedNodes == 1:
                    log.info(
                        'The disabled state of the "%s" node was not toggled, as its state is controlled by an animated parameter.' %
                        animatedNodes[0].getName())
                elif expressionedNodes or animatedNodes:
                    log.info(
                        'The disabled states of %d nodes were not toggled, as their states are controlled by Python expressions or animated parameters.' % (
                                    numberOfExpressionedNodes + numberOfAnimatedNodes))
            return True
        if isAltOnlyModifier and key == QtCore.Qt.Key_L:
            if not event.isAutoRepeat():
                mousePos = self.layerStack().getMousePos()
                mousePos = self.layerStack().mapFromQTLocalToWorld(mousePos.x(), mousePos.y())
                hitList = self.layerStack().hitTestPoint(mousePos)
                topMostBackdropNode = _GetTopMostBackdropNodeFromHitList(hitList)
                if topMostBackdropNode:
                    if topMostBackdropNode.isLocked(True):
                        return False
                    lockState = bool(NodegraphAPI.GetNodeShapeAttr(topMostBackdropNode, 'stickyLock'))
                    newLockState = int(not lockState)
                    DrawingModule.nodeWorld_setShapeAttr(topMostBackdropNode, 'stickyLock', newLockState)
                    NodegraphAPI.SetNodeShapeAttr(topMostBackdropNode, 'stickyLock', newLockState)
                    NodegraphAPI.SetNodeSelected(topMostBackdropNode, False)
                    self.layerStack().idleUpdate()
            return True
        if isNoModifierPressed and key == QtCore.Qt.Key_L:
            if not event.isAutoRepeat():
                allSelectedNodes = NodegraphAPI.GetAllSelectedNodes()
                try:
                    DrawingModule.AutoPositionNodes(allSelectedNodes)
                except Exception as exception:
                    log.exception('Auto-position nodes failed.')
                    warningMessage = 'Automatically positioning the selected nodes failed: '
                    errorMessage = str(exception)
                    if errorMessage:
                        warningMessage += errorMessage
                    else:
                        warningMessage += repr(exception)
                    QtWidgets.QMessageBox.warning(None, 'Auto-Position Nodes Failed', warningMessage)

            return True
        if isNoModifierPressed and key == QtCore.Qt.Key_Period:
            if not event.isAutoRepeat():
                return self.__createDotNode()
            return True
        if isAltOnlyModifier and key == QtCore.Qt.Key_Period:
            if not event.isAutoRepeat():
                KatanaPrefs[PrefNames.NODEGRAPH_DIMUNCONNECTEDTOVIEWNODE] = not KatanaPrefs[
                    PrefNames.NODEGRAPH_DIMUNCONNECTEDTOVIEWNODE]
            return True
        if isShiftOnlyModifier and key == QtCore.Qt.Key_Pause:
            if not event.isAutoRepeat():
                return self._createBreakoutNode()
            return True
        if isAltOnlyModifier and key == QtCore.Qt.Key_T:
            if not event.isAutoRepeat():
                self.layerStack().toggleTeleports()
            return True
        if isNoModifierPressed and key == QtCore.Qt.Key_Q:
            print ("pressed Q, you QTPY")
            return True
            # if not event.isAutoRepeat():
            #     KatanaPrefs[PrefNames.NODEGRAPH_SHOWEXPRESSIONLINKS] = not KatanaPrefs[
            #         PrefNames.NODEGRAPH_SHOWEXPRESSIONLINKS]
            # return True
        if isAltOnlyModifier and key == QtCore.Qt.Key_S:
            if not event.isAutoRepeat():
                KatanaPrefs[PrefNames.NODEGRAPH_GRIDSNAP] = not KatanaPrefs[PrefNames.NODEGRAPH_GRIDSNAP]
                self.layerStack().idleUpdate()
            return True
        if isNoModifierPressed and key == QtCore.Qt.Key_M:
            if not event.isAutoRepeat():
                self.layerStack().mergeSelectedNodes()
            return True
        if isAltOnlyModifier and key == QtCore.Qt.Key_M:
            if not event.isAutoRepeat():
                Utils.UndoStack.OpenGroup('Toggle Thumbnails')
                enabledState = None
                try:
                    for node in NodegraphAPI.GetAllSelectedNodes():
                        if node.isLocked(True):
                            continue
                        if not RenderManager.IsRenderNode(node.getType()) and not Nodes2DAPI.IsUpstreamNode2D(node):
                            continue
                        if enabledState is None:
                            enabledState = bool(not NodegraphAPI.IsNodeThumbnailEnabled(node))
                        NodegraphAPI.SetNodeThumbnailEnabled(node, enabledState)

                finally:
                    Utils.UndoStack.CloseGroup()

            return True
        if isNoModifierPressed and key == QtCore.Qt.Key_R:
            if not event.isAutoRepeat():
                selectedNodes = NodegraphAPI.GetAllSelectedNodes()
                if len(selectedNodes) == 1:
                    selectedNode = selectedNodes[0]
                    if selectedNode.isLocked(True):
                        return True
                    nodePickerLayer = self.__launchNodeCreationMenuLayer(replacedNode=selectedNode)
                    if nodePickerLayer:
                        Utils.UndoStack.OpenGroup('Replace Node "%s"' % selectedNode.getName())
                        nodePickerLayer.setReplacedNodeCallback(self.__nodePickerLayerFinished)
            return True
        if isNoModifierPressed and (text == '[' or text == '{'):
            return self.layerStack().sendSelectedBackdropNodesToBack()
        if isNoModifierPressed and (text == ']' or text == '}'):
            return self.layerStack().sendSelectedBackdropNodesToFront()
        mousePos = self.layerStack().getMousePos()
        if not mousePos:
            return False
        mousePos = self.layerStack().mapFromQTLocalToWorld(mousePos.x(), mousePos.y())
        hitList = self.layerStack().hitTestPoint(mousePos)
        if not hitList:
            return False
        isRenameKeyPressed = isNoModifierPressed and key == QtCore.Qt.Key_Return or event.modifiers() == QtCore.Qt.KeypadModifier and key == QtCore.Qt.Key_Enter
        _hitType, hitOptions = hitList[0]
        node = hitOptions['node']
        if (isNoModifierPressed or isShiftOnlyModifier) and key == QtCore.Qt.Key_V:
            if node.getType() in EDIT_VIEW_NODETYPE_EXCLUSIONS:
                return False
            if NodegraphAPI.GetNodeShapeAttr(node, 'notViewable'):
                return False
            exclusive = not isShiftOnlyModifier
            NodegraphAPI.SetNodeViewed(node, exclusive or not NodegraphAPI.IsNodeViewed(node), exclusive=exclusive)
            return True
        if (isNoModifierPressed or isShiftOnlyModifier) and key == QtCore.Qt.Key_E:
            if node.getType() in EDIT_VIEW_NODETYPE_EXCLUSIONS:
                return False
            exclusive = not isShiftOnlyModifier
            NodegraphAPI.SetNodeEdited(node, exclusive or not NodegraphAPI.IsNodeEdited(node), exclusive=exclusive)
            return True
        if isNoModifierPressed and key == QtCore.Qt.Key_D:
            if node.isLocked(True):
                return False
            if node.getBaseType() == 'Backdrop':
                return True
            if BypassParameterManager.IsBypassedStateControlledByExpression(node):
                BypassParameterManager.EditBypassedStateExpression(node, parent=self.layerStack().window())
                return True
            if BypassParameterManager.IsBypassedStateAnimated(node):
                log.info(
                    'The disabled state of the "%s" node was not toggled, as its state is controlled by an animated parameter.' % node.getName())
                return True
            node.setBypassed(not node.isBypassed())
            return True
        if isNoModifierPressed and text.isdigit():
            portNumber = int(text) - 1
            if portNumber < 0:
                return False
            if DrawingModule.nodeWorld_getShapeAttrAsNumber(node, 'suppressPortKeys'):
                return False
            if NodegraphAPI.IsNodeLockedByParents(node):
                return False
            if portNumber >= node.getNumOutputPorts():
                return False
            outputPort = node.getOutputPortByIndex(portNumber)
            if outputPort.getNumConnectedPorts():
                if outputPort.getConnectedPort(0).getNode().getParent() != node.getParent():
                    return False
            self.layerStack().appendLayer(LinkConnectionLayer([node.getOutputPorts()[portNumber]], None, enabled=True))
            return True
        if isNoModifierPressed and key == QtCore.Qt.Key_QuoteLeft:
            if event.isAutoRepeat():
                return False
            if DrawingModule.nodeWorld_getShapeAttrAsNumber(node, 'suppressPortKeys'):
                return False
            if NodegraphAPI.IsNodeLockedByParents(node):
                return False
            useport = None
            for i in xrange(0, node.getNumOutputPorts()):
                port = node.getOutputPortByIndex(i)
                if not port.getNumConnectedPorts():
                    useport = port
                    break

            if not useport and node.getNumOutputPorts():
                useport = node.getOutputPortByIndex(0)
            if useport:
                self.layerStack().appendLayer(LinkConnectionLayer([useport], None, enabled=True))
            return True
        if isShiftOnlyModifier and key == QtCore.Qt.Key_AsciiTilde:
            if event.isAutoRepeat():
                return False
            if node.getNumInputPorts() <= 1:
                return False
            if node.isLocked(True):
                return False
            inputPorts = [node.getInputPortByIndex(i) for i in range(2)]
            connectedPorts = [port.getConnectedPort(0) for port in inputPorts]
            if not filter(bool, connectedPorts):
                return False
            Utils.UndoStack.OpenGroup('Swap Input Ports: %s' % (node.getName(),))
            try:
                if connectedPorts[1]:
                    inputPorts[0].connect(connectedPorts[1])
                else:
                    inputPorts[0].disconnect(connectedPorts[0])
                if connectedPorts[0]:
                    inputPorts[1].connect(connectedPorts[0])
                else:
                    inputPorts[1].disconnect(connectedPorts[1])
            finally:
                Utils.UndoStack.CloseGroup()

            return True
        if isCtrlOnlyModifier and key == QtCore.Qt.Key_Return:
            if event.isAutoRepeat():
                return False
            if isinstance(node, NodegraphAPI.GroupNode):
                self.layerStack().setCurrentNodeView(node)
                return True
        elif isRenameKeyPressed and not nodesAreFloating:
            if event.isAutoRepeat():
                return False
            return self.__renameNode(node)
        return False

def test(self, event):
    print("test???")
    from qtpy.QtCore import Qt
    if event.type() == Qt.KeyPress:
        print ("=============================== KEY PRESS EVENT")
        key = event.key()
        print(key.text())

def installNodegraphHotkeyOverrides():

    print("============================ installing hotkey ovrrides")
    NodeInteractionLayer.processEvent = test
    print("==============FINISHED============== installing hotkey ovrrides")
