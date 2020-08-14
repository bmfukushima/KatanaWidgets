import Katana
import v00 as VariableManager

if VariableManager:
    PluginRegistry = [(
        "SuperTool", 2, "VariableManager",
        (
            VariableManager.VariableManagerNode,
            VariableManager.GetEditor
        )
    ), ]
