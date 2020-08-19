import Katana
import VariableManager

if VariableManager:
    PluginRegistry = [(
        "SuperTool", 2, "VariableManager",
        (
            VariableManager.VariableManagerNode,
            VariableManager.GetEditor
        )
    ), ]
