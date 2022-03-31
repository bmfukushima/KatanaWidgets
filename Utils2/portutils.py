def isPortConnected(port):
    """ Determines if a port is connected

    Args:
        port (port): port to be checked
    """
    if 0 < len(port.getConnectedPorts()):
        return True
    else:
        return False