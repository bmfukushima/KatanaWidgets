scene = ScenegraphManager.getActiveScenegraph()

path = scene.getSelectedLocations()



gaffer = NodegraphAPI.CreateNode('GafferThree', NodegraphAPI.GetRootNode())

gaffer.setName('meshLightGaffer')

sgLocation = '/root/world/lgt/%s' % gaffer.getName()



# Set the current root location for the new gaffer node

gaffer.setRootLocation(sgLocation)

rootPackage = gaffer.getRootPackage()



nameCount = 0

for mesh in path:



    meshLightPackage = rootPackage.createChildPackage("ArnoldMeshLightPackage", "meshLight_" + str(nameCount))

    material_node = meshLightPackage.getMaterialNode()

    material_node.checkDynamicParameters()

    meshLightPackage.getMaterialNode().getParameter('shaders.arnoldLightParams.mesh.value').setValue(mesh, 0) 

    meshLightPackage.getMaterialNode().getParameter('shaders.arnoldLightParams.mesh.enable').setValue(1, 0) 

    nameCount = nameCount + 1