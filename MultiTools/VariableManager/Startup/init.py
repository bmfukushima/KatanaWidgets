from Katana import Utils

def onGSVChange(args):
    #import NodegraphAPI

    # get arguments from event
    print('yolo')
    if args[0][2]:
        node = args[0][2]['node']
        if node.getType() == 'VariableManager':
            print (node.getName())

def createNewPatternEvent():
    print('start')
    Utils.EventModule.RegisterCollapsedHandler(onGSVChange, 'parameter_setValue')
    print('end register')