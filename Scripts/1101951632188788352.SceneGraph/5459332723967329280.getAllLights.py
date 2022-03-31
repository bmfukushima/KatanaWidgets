node = NodegraphAPI.GetNode('GafferThree')

runtime = FnGeolib.GetRegisteredRuntimeInstance()
txn = runtime.createTransaction()
client = txn.createClient()
op = Nodes3DAPI.GetOp(txn, node)
txn.setClientOp(client, op)
runtime.commit(txn)

location = client.cookLocation('/root/world')
location.getAttrs()
location.getPotentialChildren()
# ['geo', 'cam', 'lgt']

def walk(client, path, light_list=None):
    if not light_list:
        light_list = []

    location = client.cookLocation(path)
    location_type = location.getAttrs().getChildByName("type").getValue()
    if location_type == "light":
        light_list.append(path)
    for child in location.getPotentialChildren():
        light_list += walk(client, "{path}/{child}".format(path=path, child=child), light_list)

    return list(set(light_list))
light_list = walk(client, '/root/world')
print(light_list)
# Collect Material assignments




