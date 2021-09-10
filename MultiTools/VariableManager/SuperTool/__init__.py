# from Node import VariableManagerNode
#
# def GetEditor():
#     from Editor import VariableManagerEditor
#     return VariableManagerEditor
# try:
#     from Node import VariableManagerNode as NODE
#     def EDITOR():
#         from Editor import VariableManagerEditor
#         return VariableManagerEditor
#     NAME = 'VariableManager'
# except:
#     pass

from .Node import VariableManagerNode as NODE
def EDITOR():
    from .Editor import VariableManagerEditor
    return VariableManagerEditor
NAME = 'VariableManager'