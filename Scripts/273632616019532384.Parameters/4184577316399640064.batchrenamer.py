
def getAllParameters(param,param_list=None):
    for child in param.getChildren():
        if child.getType() == 'group':
            return getAllParameters(child, param_list)
        else:
            param_list.append(child)
    return param_list
    pass

new_val = 'hiyaIzzy! Watcha doing!??!?!'
old_val = 'primitive'
nodes_list = NodegraphAPI.GetAllSelectedNodes()
for node in nodes_list:
    params = node.getParameters()
    param_list = getAllParameters(param = params, param_list=[])
    for param in param_list:
        if param.getType() == 'string':
            if param.isExpression() is True:
                old_exp = param.getExpression()
                new_exp = old_exp.replace(old_val, new_val)
                param.setExpression(new_exp)
            else:
                old_value = param.getValue(0)
                new_value = old_value.replace(old_val, new_val)
                param.setValue(new_value,0)
            