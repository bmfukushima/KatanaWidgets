sgmanager = ScenegraphManager.getActiveScenegraph()
locations = ['/root/world/geo/asset/group010000/primitive', '/root/world/geo/asset/group010001']
#
    #a.setLocationOpen(loc, True, sender=None)

b = '/root/world/geo/asset/group010000/primitive'
b_list = b.split('/')

for loc in locations:
    parent_list = []
    for count, item in enumerate(loc.split('/')):
        #need to check to see if location exists...
        parent_list.append('/'.join(b_list[:count]))
    sgmanager.ensureLocationVisible(loc, sender=None)
    print parent_list
    sgmanager.openLocations([loc], sender=None)
    sgmanager.setLocationSelected(loc, selected=True, sender=None)
