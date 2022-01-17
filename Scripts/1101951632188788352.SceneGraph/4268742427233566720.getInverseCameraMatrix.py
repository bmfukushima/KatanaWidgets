""" All functions "borrowed" from
https://stackoverflow.com/questions/32114054/matrix-inversion-without-numpy
"""

def transposeMatrix(m):
    return map(list,zip(*m))

def getMatrixMinor(m,i,j):
    return [row[:j] + row[j+1:] for row in (m[:i]+m[i+1:])]

def getMatrixDeternminant(m):
    #base case for 2x2 matrix
    if len(m) == 2:
        return m[0][0]*m[1][1]-m[0][1]*m[1][0]

    determinant = 0
    for c in range(len(m)):
        determinant += ((-1)**c)*m[0][c]*getMatrixDeternminant(getMatrixMinor(m,0,c))
    return determinant

def getMatrixInverse(m):
    determinant = getMatrixDeternminant(m)
    #special case for 2x2 matrix:
    if len(m) == 2:
        return [[m[1][1]/determinant, -1*m[0][1]/determinant],
                [-1*m[1][0]/determinant, m[0][0]/determinant]]

    #find matrix of cofactors
    cofactors = []
    for r in range(len(m)):
        cofactorRow = []
        for c in range(len(m)):
            minor = getMatrixMinor(m,r,c)
            cofactorRow.append(((-1)**(r+c)) * getMatrixDeternminant(minor))
        cofactors.append(cofactorRow)
    cofactors = transposeMatrix(cofactors)
    for r in range(len(cofactors)):
        for c in range(len(cofactors)):
            cofactors[r][c] = cofactors[r][c]/determinant
    return cofactors

runtime = FnGeolib.GetRegisteredRuntimeInstance()
txn = runtime.createTransaction()
client = txn.createClient()
op = Nodes3DAPI.GetRenderOp(txn, NodegraphAPI.GetViewNode())
txn.setClientOp(client,op)
runtime.commit(txn)
data = client.cookLocation('/root/world/cam/camera')
attrs = data.getAttrs()
xform_attr = attrs.getChildByName("xform.interactive")


matrix = FnGeolibServices.XFormUtil.CalcTransformMatrixAtTime(xform_attr, 0.0)[0].getData()

inverse = getMatrixInverse([
    list(matrix[0:4]),
    list(matrix[4:8]),
    list(matrix[8:12]),
    list(matrix[12:16])
])

node = NodegraphAPI.GetNode('AttributeSet')
inverse_matrix = []
for im in inverse:
    inverse_matrix += im

for i in range(16):
    parameter = node.getParameter('groupValue.newParameter1.i{index}'.format(index=i))
    parameter.setValue(inverse_matrix[i], 0)
    
print("==================")
print(inverse_matrix)

























