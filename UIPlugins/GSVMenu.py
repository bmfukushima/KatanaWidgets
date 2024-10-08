from Katana import NodegraphAPI, RenderingAPI, LayeredMenuAPI, UI4, Utils
from Utils2 import widgetutils, isLicenseValid


def GSVMenuPopulateCallback(layeredMenu):
    """
    The populate call back is given to the layeredMenu as an argument.  This
    function will determine what options are displayed to the user when the user
    displays the layered menu.
    """
    display_flag = getGSVDisplayFlag()
    gsv_parm = NodegraphAPI.GetNode('rootNode').getParameter('variables')

    # populate options
    if display_flag is False:
        gsv_name = getGSV()
        gsv_entry = gsv_parm.getChild('%s.options'%gsv_name)
        for child in gsv_entry.getChildren():
            layeredMenu.addEntry(str(child.getValue(0)), text=str(child.getValue(0)), color=(128, 0, 128))

    # populate GSVs
    else:
        for child in gsv_parm.getChildren():
            layeredMenu.addEntry(str(child.getName()), text=str(child.getName()), color=(0, 128, 128))


def GSVMenuActionCallback(value):
    """
    The ActionCallback is given to the LayeredMenu as an argument.  This function
    will determine what should happen when the user selects an option in the
    LayeredMenu.
    """
    # flip display flag
    display_flag = getGSVDisplayFlag()
    nodegraph_widget = widgetutils.isCursorOverNodeGraphWidget()
    # frist menu | display options menu
    if display_flag:
        # set flags to allow recursion through menus
        setGSV(value)
        setGSVDisplayFlag(False)
        """ Hacky update used to clear the last layer of the layer stack, as if
        this is not done for some reason the node graph will become unresponsive.
        
        A custom attr is added to the main window which is called in a monkey patch
        to block an error that occurs using this technique (MonkeyPatches.nodegraph.menuLayerOverride)
        """

        if nodegraph_widget:
            widgetutils.katanaMainWindow()._is_recursive_layered_menu_event = True
            # nodegraph_widget = nodeutils.isCursorOverNodeGraphWidget()
            # nodegraph_widget.removeLayer(nodegraph_widget.getLayers()[-1])
            nodegraph_widget.getLayers()[-1]._MenuLayer__close()
            GSVMenu = LayeredMenuAPI.LayeredMenu(
                GSVMenuPopulateCallback,
                GSVMenuActionCallback,
                None,
                alwaysPopulate=True,
                onlyMatchWordStart=False)
            nodegraph_widget.showLayeredMenu(GSVMenu)

        #return

    # second menu | set GSV Option
    else:
        setGSVDisplayFlag(True)
        gsv_parm = NodegraphAPI.GetNode('rootNode').getParameter('variables')
        gsv_name = getGSV()
        gsv_parm = gsv_parm.getChild(f'{gsv_name}.value')
        gsv_parm.setValue(value, 0)

        # disable cursor selection cursor display
        if nodegraph_widget:
            nodegraph_widget.getLayerByName("_selection").resetAttrs()

    return ""


def getGSVDisplayFlag():
    """ The GSV Display flag determines what display should be shown.

    This is needed as the LayeredMenu by default is only designed to hold one layer.
    And we need it to hold multiple layers

    False = display options for a specific GSV
    True = display all GSVs
    """
    katana_main = UI4.App.MainWindow.CurrentMainWindow()
    if not hasattr(katana_main, '_layered_menu_gsv_display_flag'):
        katana_main._layered_menu_gsv_display_flag = True
    display_flag = katana_main._layered_menu_gsv_display_flag
    return display_flag


def setGSVDisplayFlag(flag):
    katana_main = UI4.App.MainWindow.CurrentMainWindow()
    katana_main._layered_menu_gsv_display_flag = flag


def getGSV():
    """ stores the current GSV name as a string """
    katana_main = UI4.App.MainWindow.CurrentMainWindow()
    layered_menu_gsv = katana_main._layered_menu_gsv
    return layered_menu_gsv


def setGSV(gsv):
    katana_main = UI4.App.MainWindow.CurrentMainWindow()
    katana_main._layered_menu_gsv = gsv


# if isLicenseValid():
#     GSVMenu = LayeredMenuAPI.LayeredMenu(
#         GSVMenuPopulateCallback,
#         GSVMenuActionCallback,
#         None,
#         alwaysPopulate=True,
#         onlyMatchWordStart=False
    # )
    #
    # LayeredMenuAPI.RegisterLayeredMenu(GSVMenu, 'GSV')

