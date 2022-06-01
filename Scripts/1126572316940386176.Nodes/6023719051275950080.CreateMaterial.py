material_node = NodegraphAPI.CreateNode("Material", NodegraphAPI.GetRootNode())

material_node.addShaderType("prmanBxdf")
material_node.getParameter('shaders.prmanBxdfShader.enable').setValue(1, 0)
material_node.getParameter('shaders.prmanBxdfShader.value').setValue('PxrSurface', 0)