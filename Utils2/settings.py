import os

""" GIFS """
__base_dir = '/'.join(os.path.dirname(__file__).split('/')[:-1])
__icons_dir = '{directory}/Icons'.format(
    directory=__base_dir
)

BEBOP_JPG = __icons_dir + '/bebop.jpg'
BEBOP_ON_JPG = __icons_dir + '/bebop_on.jpg'
BEBOP_OFF_JPG = __icons_dir + '/bebop_off.jpg'
ACCEPT_GIF = __icons_dir + '/accept.gif'
CANCEL_GIF = __icons_dir + '/cancel.gif'
