def GetAnimatedAttribute(node, locationPath, attributeName, startFrame,
    endFrame):
    # Create a GraphState object with a shutter open and shutter close range
    # and the maximum number of time samples matching the frame range between
    # the given start and end frame
    graphState = NodegraphAPI.GetGraphState(0.0) # Graph State for frame 0
    graphStateBuilder = graphState.edit()
    graphStateBuilder.setShutterOpen(startFrame)
    graphStateBuilder.setShutterClose(endFrame)
    graphStateBuilder.setMaxTimeSamples(endFrame - startFrame + 1)
    graphState = graphStateBuilder.build()

    # Create a Geolib3 Client for cooking locations using the Op chain that
    # corresponds to the given node for the Graph State created above
    runtime = FnGeolib.GetRegisteredRuntimeInstance()
    txn = runtime.createTransaction()
    client = txn.createClient()
    op = Nodes3DAPI.GetOp(txn, node, graphState)
    txn.setClientOp(client, op)
    runtime.commit(txn)

    # Use the created Geolib3 Client to cook the location with the given path
    # to obtain and return the attribute of the given name with all of the time
    # samples between the given start and end frame
    locationData = client.cookLocation(locationPath)
    attributes = locationData.getAttrs()
    if attributes is not None:
        return attributes.getChildByName(attributeName)
    else:
        return None

nodeName = NodegraphAPI.GetNode('PrimitiveCreate')

animatedAttribute = GetAnimatedAttribute(
    nodeName,
    '/root/world/geo/primitive',
    'geometry.point.P',
    1, 15)
print(animatedAttribute.getXML())