node = NodegraphAPI.CreateNode('ArnoldShadingNode', parent=NodegraphAPI.GetRootNode())
node.getParameters().getChild('nodeType').setValue('ramp_float', 0)
node.checkDynamicParameters()


node.setName('ramp_float')

positions = node.getParameter('parameters.ramp_Knots.value')
floats = node.getParameter('parameters.ramp_Floats.value')
values = node.getParameter('parameters.ramp.value')

# enable params
node.getParameter('parameters.ramp_Floats.enable').setValue(1,0)
node.getParameter('parameters.ramp_Knots.enable').setValue(1,0)
node.getParameter('parameters.ramp.enable').setValue(1,0)

pos = [0.0, 0.0, 1.0, 0.98260897398 ,1.0]
flo = [0.0, 0.0, 0.77999997139, 0.939999997616, 1.0]

# resize arrays
num_values = len(pos)
positions.resizeArray(num_values)
floats.resizeArray(num_values)
values.setValue(num_values, 0)

# update positions
for i in range(1, num_values-1):
    positions.getChildByIndex(i).setValue(pos[i], 0)
    floats.getChildByIndex(i).setValue(flo[i], 0)



