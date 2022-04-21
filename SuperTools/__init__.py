# REGISTER SUPER TOOLS
"""
Register a new sooperdooper tool...
1.) Add to import super tools
2.) Add superdooper_tools_list
"""
from Utils2 import isLicenseValid

if isLicenseValid():

    # import super tools
    from . import (
        Constraint,
        IsolateCEL,
        NodeTree
    )
    # from . import IsolateCEL
    # from . import NodeTree
    from . import SuperToolTemplate
    from . import SuperToolBasicTemplate


    from MultiTools import VariableManager, SimpleTool

    # compile list of super tools
    superdooper_tools_list = [
        Constraint,
        IsolateCEL,
        NodeTree,
        SimpleTool.SuperTool,
        VariableManager.SuperTool,
        # SuperToolBasicTemplate
        # SuperToolTemplate
    ]

    # register all super tools
    PluginRegistry = []
    for superdooper_tool in superdooper_tools_list:
        PluginRegistry.append((
                "SuperTool", 2, superdooper_tool.NAME,
                (
                    superdooper_tool.NODE,
                    superdooper_tool.EDITOR
                )
            ))

    # LOG
    print("""\t|____  SUPERTOOLS""")
    for superdooper_tool in superdooper_tools_list:
        print("\t|\t|__  {supertool_name}".format(supertool_name=superdooper_tool.NAME))
    print("""\t|""")