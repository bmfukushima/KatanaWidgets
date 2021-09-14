from UI4.App import Tabs

tabPluginSearchPaths = Tabs.GetTabPluginSearchPaths()
tabTypeNamesByPath = {}
for tabTypeName in sorted(Tabs.GetAvailableTabTypeNames()):
    tabPluginPath = Tabs.GetTabPluginPath(tabTypeName)
    for tabPluginSearchPath in tabPluginSearchPaths:
        if tabPluginPath.startswith(tabPluginSearchPath):
            tabTypeNamesByPath.setdefault(tabPluginSearchPath, []).append(tabTypeName)

for tabPluginSearchPath in tabPluginSearchPaths:
    tabTypeNames = tabTypeNamesByPath.get(tabPluginSearchPath)
    if not tabTypeNames:
        continue
    print("================")
    #separator = self.addSeparator()
    filename = os.path.join(tabPluginSearchPath, 'separatorTitle.txt')
    if os.path.isfile(filename):
        with open(filename) as (textFile):
            lines = textFile.readlines()


    print(tabTypeNames)
    # self.__addTabMenuItems(tabTypeNames)

a = Tabs.CreateTab('Monitor', None)
a.show()