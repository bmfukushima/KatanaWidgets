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
#########                IMPORT SUPER TOOLS                ##############
#############################################################

import Katana
from MultiTools import VariableManager

if VariableManager:
    PluginRegistry = [(
        "SuperTool", 2, "VariableManager",
        (
            VariableManager.VariableManagerNode,
            VariableManager.GetEditor
        )
    ), ]


