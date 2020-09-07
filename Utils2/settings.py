import os

""" GIFS """
__gif_dir = '{directory}/gif'.format(
    directory=os.path.dirname(__file__)
)
ACCEPT_GIF = __gif_dir + '/accept.gif'
CANCEL_GIF = __gif_dir + '/cancel.gif'