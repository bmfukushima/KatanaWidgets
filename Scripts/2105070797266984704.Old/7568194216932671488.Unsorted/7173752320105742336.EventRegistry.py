
def handler(obj, event, *args, **kwargs):
    print(obj)
    print(event)
    print (args)
    print (kwargs)

# register handler
Utils.EventModule.RegisterEventHandler(handler, eventType='parameter_setValue')

# get some param
p = NodegraphAPI.GetNode('LightLinkSetup').getParameter('light')

# queue event
Utils.EventModule.QueueEvent('parameter_setValue', 0, param=param, node=param.getNode())

Utils.EventModule.UnregisterEventHandler(handler, eventType='parameter_setValue')