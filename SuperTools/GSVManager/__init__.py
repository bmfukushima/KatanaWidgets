import Katana
import v00 as GSVManager

if GSVManager:
    PluginRegistry = [(
        "SuperTool", 2, "VariableManager",
        (
            GSVManager.VariableManagerNode,
            GSVManager.GetEditor
        )
    ), ]
