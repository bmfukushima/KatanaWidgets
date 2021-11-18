from UI4.App import Tabs
b = Tabs._LoadedTabPluginsByTabTypeName
parent = None
c = b["Node Graph"].data(parent)
c.show()

print(b["Parameters"])