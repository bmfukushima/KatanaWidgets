nodes = NodegraphAPI.GetAllSelectedNodes()

element = NodegraphAPI.BuildNodesXmlIO(nodes, forcePersistant=True)
nodeText = NodegraphAPI.WriteKatanaString(element, compress=False, archive=False)
clipboard = QtWidgets.QApplication.clipboard()
clipboard.setText(nodeText, QtGui.QClipboard.Selection)
clipboard.setText(nodeText, QtGui.QClipboard.Clipboard)

print(nodeText)



node = NodegraphAPI.GetRootNode()
clipboard = QtWidgets.QApplication.clipboard()
sourceText = str(clipboard.text(QtGui.QClipboard.Clipboard) or clipboard.text(QtGui.QClipboard.Selection))
print(sourceText)
loadedNodes = KatanaFile.Paste(sourceText, node)
for loadedNode in loadedNodes:
    loadedNode.setParent(node)
