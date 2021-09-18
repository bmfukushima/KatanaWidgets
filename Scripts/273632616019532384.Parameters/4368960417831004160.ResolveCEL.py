rootProducer = Nodes3DAPI.GetGeometryProducer(NodegraphAPI.GetNode('VrayObjectSettings4'))
celResults = GeoAPI.Util.CollectPathsFromCELStatement(rootProducer,(pathList))
window = UI4.Widgets.CelResultsWindow(celResults) 