ngw = UI4.App.Tabs.FindTopTab('Node Graph').getNodeGraphWidget()
clickSpot = ngw.mapFromQTLocalToWorld(ngw.getMousePos().x(), ngw.getMousePos().y())
hitList = ngw.hitTestPoint(clickSpot)

hitTypes = set((x[0] for x in hitList))

print(hitList)
print(hitTypes)
