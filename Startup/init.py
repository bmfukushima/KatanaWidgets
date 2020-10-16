from Katana import Utils

# initialize bebop menu
from ParameterMenu import installCustomParametersMenu
installCustomParametersMenu()

# setup backdrop group
print('a')
from MultiTools.BackdropGroupNode import installBackdropGroupNode
print ('b')
installBackdropGroupNode()
print('2')


# def test(*args):
#     for arg in args:
#         arg = arg[0]
#         if arg[0] == 'node_create':
#             node = arg[2]['node']
#             if node.getType() == 'RenderLayerGenerator':
#                 print ('do stuff here')
#
#
# Utils.EventModule.RegisterCollapsedHandler(test, 'node_create')
