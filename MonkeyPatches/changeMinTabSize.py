""" Changes the minimum tab size in Katana from the default to a static amount """

def changeMinTabSize(size):
    from QT4Panels.Edge import EdgeWithInfo

    def minSize(self, other):
        return size

    EdgeWithInfo.minSize = minSize
