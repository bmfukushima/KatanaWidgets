import sys
import os
import inspect
#############################################################
#########              REGISTER PYTHON PATH              ##############
#############################################################
CURRENT_DIR = (
    os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
)
__register_python_path = '/'.join(CURRENT_DIR.split('/')[:-1]) + '/__register_python_path.py'

with open(__register_python_path, "rb") as source_file:
    code = compile(source_file.read(), __register_python_path, "exec")
exec(code)

#############################################################
########                REGISTER SUPER TOOLS                #############
#############################################################
"""
Register a new sooperdooper tool...
1.) Add to import super tools
2.) Add superdooper_tools_list
"""
import Katana

# import super tools
import SimpleTool
import NodeTree
import SuperToolTemplate

from MultiTools import VariableManager

# compile list of super tools
superdooper_tools_list = [
    SimpleTool,
    NodeTree,
    VariableManager,
    SuperToolTemplate
]

# register all super tools
PluginRegistry = []
for superdooper_tool in superdooper_tools_list:
    print(superdooper_tool)
    PluginRegistry.append((
            "SuperTool", 2, superdooper_tool.NAME,
            (
                superdooper_tool.NODE,
                superdooper_tool.EDITOR
            )
        ))
