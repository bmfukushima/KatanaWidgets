# get node/params
node = NodegraphAPI.GetNode('ramp_rgb')
positions = node.getParameter('parameters.position.value')
colors = node.getParameter('parameters.color.value')
values = node.getParameter('parameters.ramp.value')

# resize the number of knots
"""
note that this will always be two greater than the actual number
of knots that are visible to the user.  This is due to the fact
that Katana requires these two invisible place holders.
"""
num_values = 7
positions.resizeArray(num_values)
colors.resizeArray(num_values*3)
values.setValue(num_values, 0)

# set position / color of individual knots
"""
Simple runs through all of the knots and sets the position and color
of them relative to their position on the ramp.
"""

for x in range(1, num_values-1):
    value = x/(num_values-1)

    # set position
    positions.getChildByIndex(x).setValue(value, 0)

    # set color
    for i in range(3):
        colors.getChildByIndex((x*3)+i).setValue(value, 0)
    
# update display
node.checkDynamicParameters()

