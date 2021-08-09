import json
import os

from Katana import NodegraphAPI

from .GSVManager import EventWidget
from Utils2 import gsvutils


def gsvChangedEvent(args):
    """
    Runs a user script when a GSV is changed

    Args:
        arg (arg): from Katana Callbacks/Events (parameter_finalizeValue)

    """
    for arg in args:
        # preflight
        if not gsvutils.isGSVEvent(arg): return
        # get param
        param = arg[2]['param']
        param_name = param.getName()

        # check param type
        if param_name != "value": return

        # get attrs
        gsv = param.getParent().getName()
        option = param.getValue(0)
        event_data = json.loads(EventWidget.paramDataStatic())

        # preflight
        if gsv not in list(event_data.keys()): return

        # user defined disable on GSV
        if not event_data[gsv]["enabled"]: return
        if option not in list(event_data[gsv]["data"].keys()): return

        # option does not exist
        if not event_data[gsv]["data"][option]["enabled"]: return

        # user defined option disable
        # script does not exist
        # if "script" not in list(event_data[gsv]["data"][option].keys()): return

        # setup local variables
        local_variables = {}
        local_variables["gsv"] = gsv
        local_variables["option"] = option

        # get data
        user_data = event_data[gsv]["data"][option]

        # execute script
        if user_data["is_script"]:
            script = EventWidget.paramScriptsStatic().getChild(user_data["script"]).getValue(0)
            exec(script, globals(), local_variables)
        elif not user_data["is_script"]:
            if os.path.exists(user_data["filepath"]):
                with open(user_data["filepath"]) as script_descriptor:
                    exec(script_descriptor.read(), local_variables)


def installGSVManagerEvents(*args, **kwargs):
    from Katana import Utils
    # create default param
    # EventWidget.createGSVEventsParam()

    gsvutils.hideEngineersGSVUI()

    Utils.EventModule.RegisterCollapsedHandler(gsvChangedEvent, 'parameter_finalizeValue', None)