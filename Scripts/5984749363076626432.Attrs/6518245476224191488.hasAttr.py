node = NodegraphAPI.GetNode('AOVManager1')
location = '/root/world/geo/primitive'
for port in node.getOutputPorts():
    print(port.getName())
print(node)
node = NodegraphAPI.GetNode('MaterialResolve')

runtime = FnGeolib.GetRegisteredRuntimeInstance()
txn = runtime.createTransaction()
client = txn.createClient()
op = Nodes3DAPI.GetOp(txn, node)
txn.setClientOp(client, op)
runtime.commit(txn)

location = client.cookLocation(location)
attrs = location.getAttrs()
attrs.childList()
attr = attrs.getChildByName("material")
if attr:
    print('true')
    True
else:
    print('false')
    False