import time
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QProgressBar, QSplashScreen
from PyQt5.QtCore import Qt, QSize, QEvent, QTimer, QRect, QMetaObject


class SplashScreen(QSplashScreen):

    background_img = None
    progress_bar = None

    def __init__(self):
        self.get_random_background_image()
        QSplashScreen.__init__(self, self.background_img)
        # self.add_progress_bar()

    def get_random_background_image(self):
        #  TODO roll it
        image_path = "D:/Repo/genshin-wish-viewer/icons/background/002x.jpg"
        self.background_img = QPixmap(image_path).scaled(854, 480)

    def add_progress_bar(self):
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setStyleSheet("QProgressBar { border: 0px solid grey; border-radius: 0px; background-color: rgb(130, 130, 130); text-align: center; }"
                                        "QProgressBar::chunk { background-color: rgb(30, 30, 30); border: 0px }")
        self.progress_bar.setGeometry(0, 470, 854, 10)
        self.progress_bar.setTextVisible(False)

    def set_progress(self, value):
        self.progress_bar.setValue(value)

    def set_min_max_progress(self, min_value, max_value):
        self.progress_bar.setMinimum(min_value)
        self.progress_bar.setMaximum(max_value)
