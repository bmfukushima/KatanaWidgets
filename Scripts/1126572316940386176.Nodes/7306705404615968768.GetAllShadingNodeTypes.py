""" Returns a list of all of the potential shading node types """

rendererName = "arnold"
RI = RenderingAPI.RendererInfo
RP = RenderingAPI.RenderPlugins
rendererInfoPlugin = RP.GetInfoPlugin(rendererName)
shaderType = RI.kRendererObjectTypeShader
shaderNames = rendererInfoPlugin.getRendererObjectNames(shaderType)

for shaderName in shaderNames:
    print(shaderName)