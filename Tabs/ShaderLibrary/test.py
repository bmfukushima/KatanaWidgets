import sys
print(sys.path)
import os

from qtpy.QtWidgets import *

#from cgqtpy.ImageLibrary.Main import Library 

from cgqtpy.widgets import LibraryWidget as Library
#from cgqtpy import ColorWidget
print (Library)

if __name__ == '__main__':

    app = QApplication(sys.argv)
    os.environ['LIBRARY_DIR'] = '/media/ssd01/library/library:/media/ssd01/library/library'
    #print(ImageLibrary)
    cw = Library()
    cw.show()
    #main_widget = ImageLibrary()
    #main_widget.show()
    sys.exit(app.exec_())