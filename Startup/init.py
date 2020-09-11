"""
No idea how to add the wrench menu icon =\ oh well

will figure it out later...

final script dumb for now

a = NodegraphAPI.GetNode('Group')
b = NodegraphAPI.GetNode('Render')
newattrs = a.getAttributes()
newattrs.update(ns_badgeText=2)
print(newattrs)
test = dict(a.getAttributes(), ns_drawBadge=1, ns_badgeText='yolohashtagswag')
print(test)


a = NodegraphAPI.GetNode('VariableSet')
a.


newattrs['ns_badgeText'] = 'askldfklasjfaljkf'
newattrs['ns_drawBadge'] = 1
a.setAttributes(newattrs)

a = UI4.App.Tabs.FindTopTab('Parameters')
b = a._ParameterPanel__panelScrollArea
layout = b.widget().layout()
widget = layout.itemAt(0).widget()
print (widget.layout().insertWidget(1, QtWidgets.QLabel("BEBOP")))

rightf = widget.getRightControlFWidgets()
l = widget.getControlLayout()
l.insertWidget(1, QtWidgets.QPushButton("BEBOP"))

rightf.parentWidget().layout().addWidget(QtWidgets.QLabel("BEBOP"))
for x in range(rightf.count()):
    print rightf.itemAt(x).widget()

rightf.addWidget(QtWidgets.QLabel('askdflkajf'))
button = rightf.itemAt(1).widget()

print(button)
def test():
    print ('klajsdkjf')

button.menu().addAction('test', test)
button.menu().update()
print(button.actions())

policy = button.parent().getValuePolicy()

policy._appendToWrenchMenu(button.__menu)
if policy.isLocked():
    for action in self.__menu.actions():
        action.setEnabled(False)


"""