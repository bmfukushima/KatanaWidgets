from Node import SimpleToolsNode

def GetEditor():
    from Editor import SimpleToolsEditor
    return SimpleToolsEditor

# PluginRegistry = [(
#     "SuperTool", 2, "SimpleTools",
#     (
#         SimpleToolsNode,
#         GetEditor
#     )
# ), ]
