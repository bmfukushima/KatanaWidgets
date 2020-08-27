import os

from PyQt5.QtWidgets import (
    QComboBox, QLineEdit, QCompleter, QWidget,
    QHBoxLayout, QPushButton, QSizePolicy,
    QLabel, QVBoxLayout
)

from PyQt5.QtGui import (
    QMovie
)

from PyQt5.QtCore import (
    QEvent, Qt, QByteArray, QSize, QSortFilterProxyModel
)

from Settings import (
    ACCEPT_GIF,
    CANCEL_GIF,
    MAYBE_COLOR_RGBA,
    ACCEPT_COLOR_RGBA,
    CANCEL_COLOR_RGBA
)
from PyQt5.Qt import QApplication


class GifPlayer(QWidget):
    def __init__(
        self,
        gifFile,
        hover_color,
        parent=None
    ):
        super(GifPlayer, self).__init__(parent)

        QVBoxLayout(self)
        self.layout().setAlignment(Qt.AlignTop)
        self.hover_color = repr(hover_color)
        self.style_sheet = self.styleSheet()

        # create movie widget
        self.movie_widget = QLabel()
        self.layout().addWidget(self.movie_widget)

        self.movie_widget.movie = QMovie(gifFile, QByteArray(), self.movie_widget)
        self.movie_widget.movie.setScaledSize(QSize(100, 300))
        self.movie_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.movie_widget.setAlignment(Qt.AlignTop)
        # start movie
        self.movie_widget.movie.setCacheMode(QMovie.CacheAll)
        self.movie_widget.setMovie(self.movie_widget.movie)
        self.movie_widget.movie.start()
        self.movie_widget.movie.loopCount()

    def updateStyleSheet(self):
        """
        Updates the color on the style sheet, as it appears
        this is caching the values into the stylesheet.  Rather
        than dynamically calling them =\
        """
        self.movie.setStyleSheet(
            """
            QLabel::hover{
                border-color: rgba%s;
            }
            """ % (
                    self.hover_color
                )
            )

    """ EVENTS """
    def setMousePressAction(self, action):
        self._action = action

    def mousePressEvent(self, *args, **kwargs):
        self._action()
        return QWidget.mousePressEvent(self, *args, **kwargs)

    def resizeEvent(self, *args, **kwargs):
        height = self.movie_widget.movie.scaledSize().height()
        self.movie_widget.setFixedHeight(height)
        return QWidget.resizeEvent(self, *args, **kwargs)

    def enterEvent(self, *args, **kwargs):
        self.setStyleSheet(
            """
            border: 5px solid;
            border-color: rgba%s;
            """ % (
                    self.hover_color
                )
            )
        return QWidget.enterEvent(self, *args, **kwargs)

    def leaveEvent(self, *args, **kwargs):
        self.setStyleSheet(self.style_sheet)
        return QWidget.leaveEvent(self, *args, **kwargs)

    """ PROPERTIES """
    @property
    def hover_color(self):
        return self._hover_color

    @hover_color.setter
    def hover_color(self, hover_color):
        self._hover_color = hover_color
