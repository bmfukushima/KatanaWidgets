def resolveCELPaths(node, cel_statement, start_location):
    """ Resolves the users CEL statement to absolute paths
    Args:
        node (Node): node to search for CEL Locations at
        cel_statement (string): value from CEL Parameter
        start_location (string): absolute path to location to start searching from"""

    collector = Widgets.CollectAndSelectInScenegraph(cel_statement, start_location)
    resolved_cel_locations = collector.collectAndSelect(select=False, node=node)
    return resolved_cel_locations

node = NodegraphAPI.GetNode('GafferThree')
cel_statement = NodegraphAPI.GetNode('Prune').getParameter('cel').getValue(0)
start_location = "/root"

paths = resolveCELPaths(node, cel_statement, start_location)