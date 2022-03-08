from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QIcon, QPalette, QColor, QPixmap, QBitmap, QPainter
from PyQt5.QtCore import Qt, QSize, QEvent, QTimer, QRect, QMetaObject, QPoint, pyqtSignal
from PyQt5.QtWidgets import QApplication, QPushButton, QFrame, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QSizeGrip, QPushButton, QLabel, QDialog, QFileDialog
from PyQt5.QtWidgets import QProgressBar
from importer import WishImporter
from database import WishDatabase
import threading
import logging
import sys

logger = logging.getLogger('GenshinWishViewer')


class ImportWishDialog(QDialog):
    banner_type = ""
    selected_files = []

    number_label = None
    select_button = None
    accept_button = None
    exit_button = None
    progress_label = None
    progress_bar = None

    reload_memory_wishes = pyqtSignal()
    insert_wishes_to_memory = pyqtSignal(list, str)

    def __init__(self, banner_type):
        QDialog.__init__(self)
        self.banner_type = banner_type
        self.setup_ui()
        self.setup_ui_logic()

    def setup_ui(self):
        self.setMinimumSize(250, 255)
        # self.setMaximumSize(300, 300)
        # self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setWindowTitle("Adding {}...".format(self.banner_type))
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("QDialog { background-color: rgb(75,75,75); border: 2px solid rgb(10,10,10); }"
                           "QLabel { color: white; }"
                           "QPushButton { color: white; background-color: transparent; border-style: solid; border-width: 2px; border-radius: 5px; border-color: rgb(130, 130, 130);}"
                           "QPushButton:hover { background-color: rgba(255, 255, 255, 20); border-color: rgba(255, 255, 255, 255); }"
                           "QPushButton:pressed { background-color: rgba(255, 255, 255, 60); border-color: rgba(255, 255, 255, 255); }"
                           "QPushButton:disabled { background-color: rgba(255, 255, 255, 5); border-color: rgb(130, 130, 130); color: rgb(130, 130, 130) }"
                           )

        # create layout for whole QDialog
        v_layout = QVBoxLayout()
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(0)

        # create custom title bar with label and exit button
        title_bar = self.create_title_bar_frame()

        # create content with labels and buttons
        content_frame = self.create_content_frame()

        # add title and content frames to main QDialog layout
        v_layout.addWidget(title_bar)
        v_layout.addWidget(content_frame)
        self.setLayout(v_layout)

    def create_title_bar_frame(self):
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(5, 2, 2, 0)
        h_layout.setSpacing(0)

        name_label = QLabel()
        name_label.setStyleSheet("color: white; font-size: 10pt;")
        name_label.setText("Adding {}...".format(self.banner_type))
        h_layout.addWidget(name_label)

        self.exit_button = QPushButton()
        self.exit_button.setFixedSize(50, 25)
        self.exit_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.exit_button.setIcon(QIcon("icons/exit_white.png"))
        self.exit_button.setStyleSheet("QPushButton { background-color: transparent; border: 0px; border-radius: 0px }"
                                       "QPushButton:hover{ background-color: rgba(255, 0, 0, 255) }"
                                       "QPushButton:pressed{ background-color: rgba(255, 100, 100, 255) }"
                                       "QPushButton:disabled{ background-color: rgb(75,75,75) }")
        h_layout.addWidget(self.exit_button)

        title_bar = QFrame()
        title_bar.setMinimumSize(0, 25)
        title_bar.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        title_bar.setStyleSheet("QFrame { background-color: rgb(10,10,10); }")
        title_bar.setLayout(h_layout)
        return title_bar

    def create_content_frame(self):
        content_layout = QVBoxLayout()

        description_label = QLabel()
        description_label.setWordWrap(True)
        description_label.setText(
            "Please screenshot your wish history in Genshin Impact.\nSelect one or multiple images and click Accept to add them to database.")
        content_layout.addWidget(description_label)

        self.number_label = QLabel()
        self.number_label.setText("Selected 0 images")
        content_layout.addWidget(self.number_label)

        self.select_button = QPushButton("Select images", self)
        self.select_button.setMinimumSize(50, 50)
        content_layout.addWidget(self.select_button)

        self.accept_button = QPushButton("Accept", self)
        self.accept_button.setMinimumSize(50, 50)
        content_layout.addWidget(self.accept_button)

        progress_layout = QHBoxLayout()
        self.progress_label = QLabel()
        self.progress_label.setText("0/0")
        progress_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setStyleSheet(
            "QProgressBar { border: 0px solid grey; border-radius: 0px; background-color: rgb(130, 130, 130); text-align: center; }"
            "QProgressBar::chunk { background-color: rgb(30, 30, 30); border: 0px }")
        self.progress_bar.setGeometry(0, 250, 250, 5)
        self.progress_bar.setTextVisible(False)
        progress_layout.addWidget(self.progress_bar)
        content_layout.addLayout(progress_layout)

        content_frame = QFrame()
        content_frame.setLayout(content_layout)
        return content_frame

    def setup_ui_logic(self):
        self.select_button.clicked.connect(self.on_click_select_button)
        self.accept_button.clicked.connect(self.on_click_accept_button)
        self.exit_button.clicked.connect(self.on_click_exit_button)

    def on_click_select_button(self):
        files = QFileDialog.getOpenFileNames(self, "Select one or more files to open", "C:", "Images (*.png *.jpg)")
        self.selected_files = files[0]
        self.number_label.setText("Selected {} images".format(len(self.selected_files)))
        self.progress_label.setText("0/{}".format(len(self.selected_files)))

    def on_click_accept_button(self):
        # insert wishes to db using importer
        import_thread = threading.Thread(target=self.import_images_thread)
        import_thread.start()
        # lock ui
        # progress bar
        # if successful then emit signal
        # self.inserted_new_wishes.emit()
        # import_thread.join()
        # self.close()

    def on_click_exit_button(self):
        # self.reload_memory_wishes.emit()
        # handle closing while we are still doing work...
        self.close()

    def set_round_edges(self):
        # in case you want to have round corners and transparency on corner edges (instead of black)
        self.show()

        rect = QRect(QPoint(0, 0), self.geometry().size())
        bitmap = QBitmap(rect.size())
        bitmap.fill(QColor(Qt.color0))
        painter = QPainter(bitmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.color1)
        # radius must match QDialog border-radius!
        radius = 10
        painter.drawRoundedRect(rect, radius, radius, Qt.AbsoluteSize)
        painter.end()
        self.setMask(bitmap)

    def import_images_thread(self):
        wi = WishImporter(WishDatabase("db.db"))
        self.lock_ui()
        self.progress_bar.setRange(0, len(self.selected_files))

        if self.banner_type not in ["wishCharacter", "wishWeapon", "wishStandard", "wishBeginner"]:
            logger.error("Wrong table name!")
            return
        for count, img_path in enumerate(self.selected_files):
            wishes = wi.get_wishes_from_imagev2(img_path)
            wi.insert_to_db(wishes, self.banner_type)
            self.insert_wishes_to_memory.emit(wishes, self.banner_type)
            self.progress_bar.setValue(count+1)
            self.progress_label.setText("{}/{}".format(count+1, len(self.selected_files)))
        self.unlock_ui()

    def lock_ui(self):
        self.select_button.setDisabled(True)
        self.accept_button.setDisabled(True)

    def unlock_ui(self):
        self.select_button.setDisabled(False)
        self.accept_button.setDisabled(False)
