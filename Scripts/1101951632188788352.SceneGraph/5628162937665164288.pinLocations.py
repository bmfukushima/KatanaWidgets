# find scenegraph tab
scenegraph = UI4.App.Tabs.FindTopTab('Scene Graph')

# collect and select CEL
cel = "((/root/world//*panels*))"
collector = Widgets.CollectAndSelectInScenegraph(cel, "/root")
collector.collectAndSelect(select=True, replace=True, node=None)

# pin locations in the active scenegraph
activeSceneGraph = ScenegraphManager.getActiveScenegraph()
selectedLocations = set(activeSceneGraph.getSelectedLocations())
activeSceneGraph.addPinnedLocations(selectedLocations, replace=False, sender=scenegraph)

