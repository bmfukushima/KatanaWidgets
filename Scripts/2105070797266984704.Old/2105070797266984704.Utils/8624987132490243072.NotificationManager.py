import UI4.Util.NotificationManager
def callback(notificationRecord, actionName):
    print(notificationRecord, actionName)
notificationRecord = UI4.Util.NotificationManager.NotificationRecord('title', 'text')
notificationRecord.addAction('action name', 'action text')
notificationRecord.action.connect(callback)
UI4.Util.NotificationManager.AddRecord(notificationRecord)