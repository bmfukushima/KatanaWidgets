from Nodes3DAPI.PrimitiveCreate import PrimitiveCreate
print (PrimitiveCreate)

class WakaWaka(PrimitiveCreate):
    def __init__(self):
        super(Wakawaka, self).__init__()

        WakaWaka.__init__(self, primitiveType='teapot')
        self.setType('PrimitiveCreate')


NodegraphAPI.RegisterPythonNodeType('WakaWaka', WakaWaka)