""" Sets the pivot on a transform 3D to the center of the current object

Note:
    This currently only works if no parameters have been entered into the Transform3D.
    This needs to be updated to remove the final item in the xform stack
"""
# get flattened xform
node = NodegraphAPI.GetNode('Transform3D')
cel_location = NodegraphAPI.GetNode('Transform3D').getParameter('path').getValue(0)
root_geometry_producer = Nodes3DAPI.GetGeometryProducer(node,0,0)
local_geometry_producer = root_geometry_producer.getProducerByPath(cel_location)
flattened_matrix = local_geometry_producer.getFlattenedGlobalXform()

# set attrs
pivot_param = NodegraphAPI.GetNode('Transform3D').getParameter('pivot')
pivot_param.getChild("i0").setValue(flattened_matrix[12], 0)
pivot_param.getChild("i1").setValue(flattened_matrix[13], 0)
pivot_param.getChild("i2").setValue(flattened_matrix[14], 0)