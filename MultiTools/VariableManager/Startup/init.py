from Katana import Utils

def onGSVChange(args):
    #import NodegraphAPI

    # get arguments from event
    if args[0][2]:
        node = args[0][2]['node']
        if node.getType() == 'VariableManager':
            pass
            #print (node.getName())

def createNewPatternEvent():
    #print('start')
    Utils.EventModule.RegisterCollapsedHandler(onGSVChange, 'parameter_setValue')
    #print('end register')