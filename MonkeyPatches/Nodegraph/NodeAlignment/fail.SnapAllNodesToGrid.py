from Utils2.nodealignutils import AlignUtils
import NodegraphAPI

nodes = NodegraphAPI.GetAllNodes()
AlignUtils().snapNodesToGrid(nodes)