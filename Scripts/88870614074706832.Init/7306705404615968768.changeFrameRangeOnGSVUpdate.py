from Katana import Utils


def gsvChangedEvent(args):
    """
    Runs a user script when a GSV is changed

    Args:
        arg (arg): from Katana Callbacks/Events (parameter_finalizeValue)

    """
    from Katana import NodegraphAPI

    for arg in args:
        # preflight
        """ Preflight
        Test different conditions to determine if this is indeed a GSV change"""
        root_node = NodegraphAPI.GetRootNode()
        if arg[2]['node'] != root_node: return False
        if "param" not in list(arg[2].keys()): return False
        if not arg[2]['param'].getParent(): return False
        if not arg[2]['param'].getParent().getParent(): return False
        if arg[2]['param'].getParent().getParent() != NodegraphAPI.GetRootNode().getParameter('variables'): return False

        # get param
        param = arg[2]['param']
        param_name = param.getName()

        # check param type
        if param_name != "value": return

        # get GSV/Option changed
        gsv = param.getParent().getName()
        option = param.getValue(0)

        if gsv == "shot" and option == "010":
            # TODO
            # get START / END frame (call pipeline for this)
            start_frame = 10
            end_frame = 50

            # Update Project Settings
            root_node.getParameter('inTime').setValue(start_frame, 0)
            root_node.getParameter('outTime').setValue(end_frame, 0)
            root_node.getParameter('currentTime').setValue(start_frame, 0)

            # Update render nodes frame range
            """Finds all of the render nodes, and then runs through
            each one and sets the active frame range to be rendered.  Note that
            this is only one place that the active frame range is rendered.  You
            can also consider setting this during the batch submission instead.
            Which is probably a better idea."""
            render_nodes = NodegraphAPI.GetAllNodesByType("Render")

            for node in render_nodes:
                param = node.getParameter('farmSettings.setActiveFrameRange')
                param.setValue("Yes", 0)

                param.setUseNodeDefault(False)


                node.getParameter('farmSettings.activeFrameRange.start').setValue(start_frame, 0)
                node.getParameter('farmSettings.activeFrameRange.end').setValue(end_frame, 0)


Utils.EventModule.RegisterCollapsedHandler(gsvChangedEvent, 'parameter_finalizeValue', None)