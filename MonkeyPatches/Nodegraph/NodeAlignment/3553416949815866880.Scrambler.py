import random
import NodegraphAPI

randrange = 1000

for node in NodegraphAPI.GetAllSelectedNodes():
    x, y = random.randint(-randrange, randrange), random.randint(-randrange, randrange)
    NodegraphAPI.SetNodePosition(node, (x, y))