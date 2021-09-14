p = UI4.App.Tabs.FindTopTab('Parameters')
sa = p._ParameterPanel__panelScrollArea


w = sa.widget()
print(w)
l = w.layout()
print(l.count())
test_w = QtWidgets.QSplitter()
new_l = QtWidgets.QHBoxLayout(test_w)
test_w.setLayout(new_l)

for index in reversed(range(l.count())):
    param_widget = l.itemAt(index).widget()
    
    if param_widget:
        print(param_widget.height())
        policy = param_widget.sizePolicy()
        h = param_widget.height()
        
        new_l.addWidget(param_widget)
        #param_widget.setFixedHeight(h)
        print (param_widget)
        print(param_widget.layout().count())
        #param_widget.layout().itemAt(0).setAlignment(QtCore.Qt.AlignTop)
        #param_widget.layout().itemAt(1).widget().setFixedHeight(200)
        #for index in range(param_widget.layout().count()):

        param_widget.setSizePolicy(policy)
        #param_widget._FormWidget__topAreaLayout.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
    #param_widget.setParent(None)
    #new_l.addWidget(param_widget)
sa.setWidget(test_w)

test_w.setSizePolicy(w.sizePolicy())
#test_w.show()