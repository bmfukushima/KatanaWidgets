import json

from .GSVManager import EventsWidget
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
        events_data = json.loads(EventsWidget.eventsParam().getValue(0))

        # preflight
        if gsv not in list(events_data.keys()): return
        if option not in list(events_data[gsv].keys()): return
        if "script" not in list(events_data[gsv][option].keys()): return

        # setup local variables
        local_variables = {}
        local_variables["gsv"] = gsv
        local_variables["option"] = option

        # execute script
        exec(events_data[gsv][option]["script"], globals(), local_variables)

        # execute file
        # if os.path.exists(script):
        #     with open(script) as script_descriptor:
        #         exec(script_descriptor.read(), globals(), local_variables)

        # execute script
        # else:
            # exec(events_data[option]["script"], globals(), local_variables)

def installGSVManagerEvents(*args, **kwargs):
    from Katana import Utils
    # create default param
    EventsWidget.createGSVEventsParam()

    gsvutils.hideEngineersGSVUI()

    Utils.EventModule.RegisterCollapsedHandler(gsvChangedEvent, 'parameter_finalizeValue', None)