""" Every file in Plugins will automatically be run when Katana is opened """
# todo why does __register_python_path__ automatically get called?
# for some reason I don't need to register this here... and it auto runs the __register_python_path__.py
"""
import os
import inspect

# REGISTER PYTHON PATH
CURRENT_DIR = (
    os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
)
#print('==>    1')
__register_python_path__ = CURRENT_DIR + '/__register_python_path__.py'

with open(__register_python_path__, "rb") as source_file:
    code = compile(source_file.read(), __register_python_path__, "exec")
exec(code)

#print('==>    2')
"""
