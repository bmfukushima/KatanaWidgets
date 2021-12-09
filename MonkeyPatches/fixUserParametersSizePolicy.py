from qtpy.QtWidgets import QSizePolicy
from UI4.FormMaster.KatanaFactory import ParameterWidgetFactoryClass

def installUserParametersPolicyOverride():
    def buildWidget(self, parent, policy):
        w = ParameterWidgetFactoryClass.buildWidgetOrig(self, parent, policy)
        if parent:
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return w

    ParameterWidgetFactoryClass.buildWidgetOrig = ParameterWidgetFactoryClass.buildWidget
    ParameterWidgetFactoryClass.buildWidget = buildWidget

