"""
KatanaMainWindow --> (QMainWindow)
    |- topToolBar --> (QToolBar)
        |- topWidget --> (QWidget)
                |- self.__topLayout -->  (QHBoxLayout)
                    |- mainMenuLayout -->  (QVBoxLayout)
                       |- self.__menuBar -->  (QMenuBar)
                       |-* All the other widgets/buttons in the menu
"""