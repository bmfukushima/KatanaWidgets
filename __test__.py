# import sys
#
# from qtpy.QtWidgets import QApplication
#
# from cgwidgets.widgets.userInputWidgets import FloatInputWidget
#
#
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     w = FloatInputWidget()
#     w.show()
#     sys.exit(app.exec_())

a = ['a', 'b']
b = [item for item in a]

print (b)
a.append('c')
print(b)