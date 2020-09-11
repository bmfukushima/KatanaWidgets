import os

""" GIFS """
__base_dir = '/'.join(os.path.dirname(__file__).split('/')[:-1])
print('base dir')
__icons_dir = '{directory}/Icons'.format(
    directory=__base_dir
)
ACCEPT_GIF = __icons_dir + '/accept.gif'
CANCEL_GIF = __icons_dir + '/cancel.gif'