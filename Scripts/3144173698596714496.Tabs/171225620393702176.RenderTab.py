from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel

render_nodes = NodegraphAPI.GetAllNodesByType("Render")
shots = [child.getValue(0) for child in NodegraphAPI.GetNode('rootNode').getParameter('variables.shot.options').getChildren()]

class SetRenderFlagButton(QLabel):
    def __init__(self, parent, node, pattern, is_renderable=False):
        super(SetRenderFlagButton, self).__init__(parent)
        self.node = node
        self.pattern = pattern
        self.setText(pattern)
        
        # renderable flag
        self._is_renderable = is_renderable
        #print(is_renderable)
        self.setProperty("is_renderable", self._is_renderable)

        # display update
        style_sheet = """
        QLabel[is_renderable=true]{background-color:rgb(64,128,64)}
        """
        self.setStyleSheet(style_sheet)

    def mousePressEvent(self, event):
        self.updateRenderNode()
        return QLabel.mousePressEvent(self, event)

    def updateRenderNode(self):
        # get default parm
        enabled_param = self.node.getParameter('render_me')
        if not enabled_param:
            enabled_param = self.node.getParameters().createChildString("render_me", '')
    
        # flip
        self._is_renderable = not self._is_renderable
        self.setProperty('is_renderable', self._is_renderable)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

        # update param
        if self._is_renderable is True:
            new_value = ', '.join([enabled_param.getValue(0), self.pattern])
            enabled_param.setValue(new_value, 0)
        else:
            new_value = enabled_param.getValue(0).replace(', {pattern}'.format(pattern=self.pattern),'')
            enabled_param.setValue(new_value, 0)
            


def createRenderWidget(node, patterns):
    # create render toggle layout
    render_widget = QWidget()
    layout = QHBoxLayout(render_widget)
    layout.addWidget(QLabel(node.getName()))
    for pattern in patterns:
        # check if enabled
        is_renderable = False
        enabled_param = node.getParameter('render_me')
        if enabled_param:
            print('pattern == %s'%pattern)
            print('value == %s'%enabled_param.getValue(0))
            if pattern in enabled_param.getValue(0):
                is_renderable = True
        
        # Create render toggle buttons
        pattern_button = SetRenderFlagButton(render_widget, node, pattern, is_renderable=is_renderable)
        layout.addWidget(pattern_button)
    return render_widget



main_widget = QWidget()
main_layout = QVBoxLayout(main_widget)
for render_node in render_nodes:
    render_widget = createRenderWidget(render_node, shots)
    main_layout.addWidget(render_widget)

main_widget.show()