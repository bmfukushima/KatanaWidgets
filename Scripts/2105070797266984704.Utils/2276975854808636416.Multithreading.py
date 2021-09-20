import threading

# initialize widget
progressWidget = UI4.Widgets.ProgressWidget()
progressWidget.resize(200, 8)
progressWidget.setFraction(0)
progressWidget.setState(UI4.Widgets.ProgressWidget.STATE_IN_PROGRESS)
progressWidget.show()


def working_task():
    #simulate doing something
    for i in range(0,100):
        time.sleep(.01)
        progressWidget.setFraction(i*.01)
        Utils.EventModule.ProcessAllEvents()

# start worker
worker = threading.Thread(target=working_task)
worker.start()