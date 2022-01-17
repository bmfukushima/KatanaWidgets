def resolveCELPaths(node, cel_statement, start_location):
    """ Resolves the users CEL statement to absolute paths
    Args:
        node (Node): node to search for CEL Locations at
        cel_statement (string): value from CEL Parameter
        start_location (string): absolute path to location to start searching from"""

    collector = Widgets.CollectAndSelectInScenegraph(cel_statement, start_location)
    resolved_cel_locations = collector.collectAndSelect(select=False, node=node)
    return resolved_cel_locations

# get CEL Statement
node = NodegraphAPI.GetNode('GafferThree')
cel_statement = NodegraphAPI.GetNode('locations_CEL').getParameter('cel').getValue(0)
start_location = "/root"

paths = resolveCELPaths(node, cel_statement, start_location)

# generate mesh lights
rootPackage = node.getRootPackage()
nameCount = 0
for path in paths:
    meshLightPackage = rootPackage.createChildPackage("ArnoldMeshLightPackage", "meshLight_" + str(nameCount))
    material_node = meshLightPackage.getMaterialNode()
    material_node.checkDynamicParameters()
    meshLightPackage.getMaterialNode().getParameter('shaders.arnoldLightParams.mesh.value').setValue(path, 0) 
    meshLightPackage.getMaterialNode().getParameter('shaders.arnoldLightParams.mesh.enable').setValue(1, 0) 
    nameCount = nameCount + 1
