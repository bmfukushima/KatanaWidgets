"""
Module that defines an L{ImportRig()} function for importing a GafferThree rig
file into a target GafferThree node.
"""

# import imp
import os.path
import sys

from Katana import NodegraphAPI
from Katana import Plugins
from Katana import PyXmlIO
from Katana import Utils


def ImportRig(filename, gafferThreeNode):
    """
    Imports the rig file with the given name into the given GafferThree node.

    @type filename: C{str}
    @type gafferThreeNode: C{NodegraphAPI.Node}
    @rtype: C{list} of C{PackageSuperToolAPI.Packages.Package}
    @param filename: The name of the rig file to import.
    @param gafferThreeNode: The GafferThree node into which to import the rig.
    @return: A list of packages that were created in the given GafferThree node
        as a result of the import.
    @raise TypeError: If the given objects don't match the expected types.
    @raise ValueError: If the file with the given name doesn't exist, or if the
        given node is not a GafferThree node.
    @raise RuntimeError: If the rig file with the given name cannot be parsed,
        if the root XML element in it doesn't provide a C{packageType}
        attribute, if the C{RigImportExport} Python module that's required for
        importing the rig cannot be loaded, or if importing the rig failed.
    """
    # Sanity-check the types of the given objects
    if not isinstance(filename, str):
        raise TypeError('Given filename is not a string: %s' % repr(filename))
    if not isinstance(gafferThreeNode, NodegraphAPI.Node):
        raise TypeError('Given object is not a GafferThree node: %s'
                        % repr(gafferThreeNode))

    # Sanity-check the values of the given objects
    if not os.path.exists(filename):
        raise ValueError('Rig file not found: %s' % filename)
    if not gafferThreeNode.getType() == 'GafferThree':
        raise ValueError('Given node is not a GafferThree node: %s'
                         % gafferThreeNode.getName())

    # Parse the rig file with the given name
    xmlParser = PyXmlIO.Parser()
    try:
        rootElement = xmlParser.parse(filename)
    except Exception as exception:
       raise RuntimeError('Error occurred parsing rig file "%s": %s'
                          % (filename, Utils.GetExceptionMessage(exception)))

    # Check if the required `packageType` root attribute is present
    if not rootElement.hasAttr('packageType'):
       raise RuntimeError('Root element in specified rig file "%s" does not '
                          'provide a "packageType" attribute.' % filename)

    # Derive the name of the RigImportExport module file from the name of the
    # GafferThreeAPI module file
    GafferThreeAPI = Plugins.GafferThreeAPI
    moduleFilename = GafferThreeAPI.__file__.replace('GafferThreeAPI.pyc',
                                                     'RigImportExport.pyc')
    if not os.path.exists(moduleFilename):
        raise RuntimeError('Python module file not found: %s' % moduleFilename)

    # Get the description of compiled Python files required for loading the
    # RigImportExport module
    for suffix, mode, fileType in imp.get_suffixes():
        if fileType == imp.PY_COMPILED:
            pycDescription = suffix, mode, fileType
            break
    else:
        raise RuntimeError('Could not determine description of compiled '
                           'Python files required for loading the '
                           'RigImportExport module.')

    # Load the RigImportExport module, temporarily making the `Node` module
    # from the GafferThreeAPI available via `sys.modules`
    moduleFile = open(moduleFilename, mode)
    PreviousNodeModule = sys.modules.get('Node')
    sys.modules['Node'] = GafferThreeAPI.Node
    try:
        RigImportExport = imp.load_module('RigImportExport', moduleFile,
                                          moduleFilename, pycDescription)
    finally:
        moduleFile.close()
        if PreviousNodeModule is not None:
            sys.modules['Node'] = PreviousNodeModule
        else:
            del sys.modules['Node']

    def resolveNamingCollisions(packageNames):
        """
        @type packageNames: C{list} of C{str}
        @rtype: C{int}
        @param packageNames: A list of names of packages whose names collide.
        @return: An integer value indicating the strategy to use for resolving
            naming collisions in the packages with the given names.
        """
        RenameUponCollision = 0
        ReplaceUponCollision = 1
        CancelOperation = 2

        return ReplaceUponCollision

    # Import the rig
    result = []
    Utils.UndoStack.OpenGroup('Import Rig')
    try:
        packageTypeName = rootElement.getAttr('packageType')
        print('Importing %s from "%s" into "%s"...'
              % (packageTypeName, filename, gafferThreeNode.getName()))
        result = RigImportExport.__parsePackageXmlIOAtPath(
            gafferThreeNode, gafferThreeNode.getRootPackage(), rootElement,
            resolveNamingCollisions)
    except Exception as exception:
       raise RuntimeError('Error occurred importing package: %s'
                          % Utils.GetExceptionMessage(exception))
    finally:
        Utils.UndoStack.CloseGroup()

    return result
