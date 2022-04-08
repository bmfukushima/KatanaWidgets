node = NodegraphAPI.GetNode('Render')
attrs = node.getAttributes()
attrs['ns_drawOutputs'] = 0
attrs['ns_drawBadge'] = 1
attrs['ns_badgeText'] = 'Some Text'
node.setAttributes(attrs)