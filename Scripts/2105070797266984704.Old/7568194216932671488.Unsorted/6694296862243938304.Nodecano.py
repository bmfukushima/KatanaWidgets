""" Animated nodes... in case you needed that..."""

spawn_pos = (0,0)
root_node = NodegraphAPI.GetRootNode()
import time

class Dot(object):
    def __init__(self):
        self.node = NodegraphAPI.CreateNode('Group', NodegraphAPI.GetRootNode())
        self.setOrigPos((1,1))
        self.node.setName("THISISAREALLYLONGNAME")
        self.birthday = time.time()

    def getAge(self):
        return time.time() - self.birthday 

    def setOrigPos(self, orig_pos):
        self.orig_pos = orig_pos

    def getOrigPos(self):
        return self.orig_pos
        
start = time.time()
print("hello")
dot_list = []

for x in range(5):
    dot_node = Dot()
    dot_list.append(dot_node)
    for dot_obj in dot_list:
        node = dot_obj.node
        #pos = NodegraphAPI.GetNodePosition(node)
        age = dot_obj.getAge()
        pos = dot_obj.getOrigPos()
        print (age)
        NodegraphAPI.SetNodePosition(node,
            (
                (pos[0] + 1) * age * 100,
                (pos[1] + 1) * age * 100
            )
        )
        #print(pos[1] * age * 1000, node)
        NodegraphAPI.SetNeedsRedraw(True)
        Utils.EventModule.ProcessAllEvents()
    time.sleep(.5)

