""" This is registered in MonkeyPatches/Nodegraph/nodeInteractionLayerOverrides (Qt.Key_N)

This is to avoid an initialization conflict that would cause these layered menus to load multiple times
"""
from Katana import NodegraphAPI, RenderingAPI, LayeredMenuAPI, UI4, Utils
from Utils2 import widgetutils


def ExamplePopulateCallback(layeredMenu):
    """
    The populate call back is given to the layeredMenu as an argument.  This
    function will determine what options are displayed to the user when the user
    displays the layered menu.
    """

    for x in range(50):
        offset_per_tick = 255.0 / 50.0
        layeredMenu.addEntry(str(x), text=str(x), color=(offset_per_tick*x, offset_per_tick*x, offset_per_tick*x))


def ExampleActionCallback(value):
    """
    The ActionCallback is given to the LayeredMenu as an argument.  This function
    will determine what should happen when the user selects an option in the
    LayeredMenu.
    """
    #widgetutils.katanaMainWindow()._is_recursive_layered_menu_event = True
    print (value)
    return ""


Example = LayeredMenuAPI.LayeredMenu(
    ExamplePopulateCallback,
    ExampleActionCallback,
    "P",
    alwaysPopulate=True,
    onlyMatchWordStart=False
)

LayeredMenuAPI.RegisterLayeredMenu(Example, 'Example')