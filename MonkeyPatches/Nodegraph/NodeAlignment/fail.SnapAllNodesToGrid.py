from Utils2 import nodealignutils
import NodegraphAPI

nodes = NodegraphAPI.GetAllNodes()
nodealignutils.snapNodesToGrid(nodes)