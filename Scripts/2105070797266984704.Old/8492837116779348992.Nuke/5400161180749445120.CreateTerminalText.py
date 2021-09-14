# settings
text = 'scriptEditor.show()'
num_blinks = 20
pre_blinks = 3
blink_length = 10
frames_per_letter = 1
start_typing_frame = pre_blinks * 2 * blink_length
text_size = 90
global_text_size = .9

# global attrs
keys = []
# Create letter per frame
dot = nuke.nodes.Dot()
dot.setXYpos(0, 0)

switch = nuke.nodes.Switch()
switch.setXYpos(0, 300)
switch['which'].setExpression('(frame - %s)// %s'%(start_typing_frame, frames_per_letter))

blanktext = nuke.nodes.Text2()
blanktext.setXYpos(0, 200)
blanktext.setInput(0, dot)
switch.setInput(0, blanktext)
blanktext['box'].setValue([0, 50, 2000, 100])
blanktext['font_size_toolbar'].setValue(text_size)

# create terminal cursor
rectangle = nuke.nodes.Rectangle()
rectangle.setXYpos(200, 350)
rectangle['area'].setValue([0,(text_size*1.5) - text_size,text_size*.5,text_size*1.5])

transform = nuke.nodes.Transform()
transform.setXYpos(200, 400)
transform.setInput(0, rectangle)
transform['translate'].setAnimated(0)
transanim = transform['translate'].animations()[0]
transform['translate'].setAnimated(1)
transanimy = transform['translate'].animations()[1]
keys.append(transanim.setKey(-1,-200))
keys.append(transanim.setKey(0,0))
transanimy.setKey(0,0)


#keys.append(transanim.setKey(0,0))
merge = nuke.nodes.Merge()
merge.setXYpos(0, 400)
merge.setInput(0, switch) # B, A, MASK
merge.setInput(1, transform)

# set up color
constant = nuke.nodes.Constant()
constant.setXYpos(200, 600)
constant['color'].setValue([0,1,0,1])

constant_merge = nuke.nodes.Merge()
constant_merge.setXYpos(0,600)
constant_merge.setInput(1, constant)
constant_merge.setInput(2, merge)

# set up pre blinks
for x in range(pre_blinks*2):
    frame = x * blink_length
    if x % 2 == 1:
        value = 0
    else:
        value = -200
    keys.append(transanimy.setKey(frame, value))

for index in range(len(text)):
    # set text
    node = nuke.nodes.Text2()
    node.setXYpos((index+1)*100, 200)
    node.setInput(0, dot)
    switch.setInput(index+1, node)
    node['font'].setValue('Arial', 'Regular')
    node['message'].setValue(text[0:index+1])
    node['autofit_bbox'].setValue(True)
    node['global_font_scale'].setValue(global_text_size)
    width = node.bbox().w()
    node['box'].setValue([0, text_size, width, text_size*1.5])


    # cursor
    frame = start_typing_frame + (index+1) * frames_per_letter
    keys.append(transanim.setKey(frame, width))

last_typed_frame = frame + (index+2) * frames_per_letter
transanim.setKey(last_typed_frame, width)

# setup blinking cursor

for x in range(num_blinks*2):
    frame = last_typed_frame + x * blink_length
    if x % 2 == 1:
        value = 0
    else:
        value = -200
    keys.append(transanimy.setKey(frame, value))

# set all keys to constant
#for key in keys:
fml = transform.knobs()['translate'].animations()[0]

transanim.changeInterpolation(transanim.keys(), nuke.CONSTANT)
transanimy.changeInterpolation(transanimy.keys(), nuke.CONSTANT)

'''
set up offsets for changing sizes
'''


