# We first need to get a hold of the runtime the UI is using
runtime = FnGeolib.GetRegisteredRuntimeInstance()
 
# Transactions are used to batch together actions
txn = runtime.createTransaction()
 
# Make a client, and attach it to an Op in the tree,
# We get the Op from a reference to a Node. 'node' is
# available automatically in a script attached to a button,
# otherwise you would need to use NodegraphAPI.GetNode('MyNodeName')
# or similar to get the node you're interested in.
# The client will see the Scenegraph as it *leaves* this node.
client = txn.createClient()
op = Nodes3DAPI.GetOp(txn, node)
txn.setClientOp(client, op)
 
# Tell the runtime to do its thing, if we don't the client will
# exist, but won't yet be pointing to an Op
runtime.commit(txn)
#Cooking a Location
'''
Once we have a client, we can ask it for data from any particular location. To keep this example simple, were going to use the synchronous cook call, that blocks the UI until it is done. There other ways of doing this, but well save those for another day.
'''
location = client.cookLocation('/root/world')
print(location)
# We now have a location, there are a could of useful things we can do:

location.getAttrs()
# <PyFnAttribute.GroupAttribute object at 0xb253888>

location.getPotentialChildren()
# ['geo', 'cam', 'lgt']

def walk(client, path):
  print(path)
  location = client.cookLocation(path)
  for child in location.getPotentialChildren():
    walk(client, '%s/%s' % (path, child))
 
walk(client, '/root/world/geo')
# Collect Material assignments

def collectAttrValues(client, path, attrName, attrMap):
 
  location = client.cookLocation(path)
  attrs = location.getAttrs()
 
  targetAttr = None
  if attrs: # Sometimes this may be None
    targetAttr = attrs.getChildByName(attrName)
 
  if targetAttr:
    attrMap[path] = targetAttr.getValue()
 
  for child in location.getPotentialChildren():
    collectAttrValues(client, '%s/%s' % (path, child), attrName, attrMap)
  
  
materials = {}
collectAttrValues(client, '/root/world/geo', 'materialAssign', materials)
print(materials)
'''
Its worth noting, that location.getAttrs() only returns local attributes. If you want to get an inherited attribute, there are a couple of ways, but a simple one for now is to go and look at the parents (theyll most likely be in cache anyway).
'''

def getGlobalAttr(client, path, attrName):

    if not path:
        return None

    location = client.cookLocation(path)

    # This should really check getAttrs() returns something
    attr = location.getAttrs().getChildByName(attrName)

    if attr:
        return attr
    else:
        parent = '/'.join(path.split('/')[:-1])
        return getGlobalAttr(client, parent, attrName)

  
lightList = getGlobalAttr(client, '/root/world/geo', 'lightList')
