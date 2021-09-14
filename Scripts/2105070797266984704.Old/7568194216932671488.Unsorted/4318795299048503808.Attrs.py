def GetCameraName(node):
    runtime = FnGeolib.GetRegisteredRuntimeInstance()
    txn = runtime.createTransaction()
    client = txn.createClient()
    op = Nodes3DAPI.GetRenderOp(txn, node)
    txn.setClientOp(client, op)
    runtime.commit(txn)


    locationData = client.cookLocation('/root')
    if locationData is not None:
        rootAttributes = locationData.getAttrs()
        if rootAttributes is not None:
            cameraNameAttribute = rootAttributes.getChildByName(
                'renderSettings.cameraName')
            if cameraNameAttribute is not None:
                return cameraNameAttribute.getValue()

    return None


node = NodegraphAPI.GetViewNode()
cameraName = GetCameraName(node)
print(cameraName)
