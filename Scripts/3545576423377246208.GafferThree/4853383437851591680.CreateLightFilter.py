
gaffer_three = NodegraphAPI.GetNode('GafferThree')
root_packge = gaffer_three.getRootPackage()
name = "test"

# Creates aiBlocker
BlockerLightFilterPackage = root_packge.createChildPackage("LightFilterPackage", str(name))
createNode = BlockerLightFilterPackage.getCreateNode()
# Checks for dynamic parameters
materialNode = BlockerLightFilterPackage.getMaterialNode()
materialNode.addShaderType('lightFilter')
materialNode.getParameter('shaders.lightFilterShader.enable').setValue(1, 0)
materialNode.getParameter('shaders.lightFilterShader.value').setValue('light_blocker', 0)
materialNode.checkDynamicParameters()
