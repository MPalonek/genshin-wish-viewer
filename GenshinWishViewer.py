from argparse import ArgumentParser
import logging
from datetime import date
import os
from database import WishDatabase
from ImportWishWindow import ImportWishDialog
from StartupWindow import SplashScreen
from SideGrip import SideGrip
from importer import WishImporter
import time
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QIcon, QPalette, QColor, QPixmap, QBitmap, QPainter, QBrush
from PyQt5.QtCore import Qt, QSize, QEvent, QTimer, QRect, QMetaObject, QPoint
from PyQt5.QtWidgets import QApplication, QPushButton, QFrame, QMainWindow, QSplashScreen, QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QSizeGrip, QPushButton, QLabel, QTableWidgetItem
import sys
# potential UI - https://github.com/Wanderson-Magalhaes/Simple_PySide_Base/blob/master/main.py


def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument("-d", "--debug", '--DEBUG', action='store_true', help="set logging to be debug")
    return parser.parse_args()


def init_logger(debug):
    logger = logging.getLogger('GenshinWishViewer')
    if debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    log_filename = "gwv_log_0.log"
    logger.setLevel(log_level)
    # FileHandler sends log records to the log_filename file.
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(log_level)
    # StreamHandler sends log records to a stream. If the stream is not specified, the sys.stderr is used.
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Formatter is an object which configures the final order, structure, and contents of the log record.
    formatter = logging.Formatter(fmt='%(asctime)s.%(msecs)03d %(levelname)s: %(message)s', datefmt='%H:%M:%S')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # add separation to easily differentiate subsequent runs
    if os.path.isfile(log_filename):
        f = open(log_filename, "a")
        f.write("\n-----------------------------------------------------------------\n\n")
        f.close()
    logger.info('Starting Genshin Wish Viewer. Current date is: {}. Log level: {}'.format(date.today(), log_level))


class Ui(QtWidgets.QMainWindow):

    db = None
    wish_entries = {
        "wishCharacter": [],
        "wishWeapon": [],
        "wishStandard": [],
        "wishBeginner": []
    }

    sideGrips = None
    cornerGrips = None
    _gripSize = 2
    maximized = False
    drag_pos = None

    def __init__(self):
        super(Ui, self).__init__()

        w = SplashScreen()
        w.show()
        uic.loadUi('mainwindow.ui', self)

        self.db = WishDatabase('db.db')
        self.db.initialize_database()
        self.load_wishes_to_memory_from_db()

        self.setup_ui()
        w.close()
        self.show()

    def setup_ui(self):
        self.setWindowTitle("Genshin Wish Viewer")
        self.setWindowIcon(QIcon('icons/wish_icon_white_blur.png'))
        self.titleLabel.setText("Genshin Wish Viewer")
        self.iconLabel.setPixmap(QPixmap("icons/wish_icon_white_blur.png").scaled(20, 20, Qt.KeepAspectRatio))
        self.resize(1326, 556)

        self.make_window_frameless()

        # self.set_dark_mode_theme()

        self.minimizeButton.setIcon(QIcon("icons/minimize_white.png"))
        self.maximizeRestoreButton.setIcon(QIcon("icons/maximize_white.png"))
        self.closeButton.setIcon(QIcon("icons/exit_white.png"))

        # ----------SETTING TABLES----------
        self.characterBannerTableWidget.setColumnWidth(0, 120)  # was 130 without scrollbar
        self.characterBannerTableWidget.setColumnWidth(1, 118)  # 118
        self.characterBannerTableWidget.setColumnWidth(2, 30)
        self.characterBannerTableWidget.setColumnHidden(3, True)
        for i in range(3):
            self.characterBannerTableWidget.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Fixed)
        self.characterBannerTableWidget.verticalScrollBar().setStyleSheet("QScrollBar:vertical { border: none; background: rgb(75, 75, 75); width: 5px; margin: 5 0 0 0; border-radius: 2px; }"
                                                                          "QScrollBar::handle:vertical { background-color:  rgb(130, 130, 130); min-height: 30px; border-radius: 2px; }"
                                                                          "QScrollBar::handle:vertical:hover { background-color: rgb(200, 200, 200); }"
                                                                          "QScrollBar::handle:vertical:pressed { background-color: rgb(255, 255, 255); }" 
                                                                          "QScrollBar::sub-page:vertical, QScrollBar::sub-line:vertical, QScrollBar::add-page:vertical, QScrollBar::add-line:vertical { background: none; }"
                                                                          )

        self.weaponBannerTableWidget.setColumnWidth(0, 120)  # was 130 without scrollbar
        self.weaponBannerTableWidget.setColumnWidth(1, 118)  # 118
        self.weaponBannerTableWidget.setColumnWidth(2, 30)
        self.weaponBannerTableWidget.setColumnHidden(3, True)
        for i in range(3):
            self.weaponBannerTableWidget.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Fixed)
        self.weaponBannerTableWidget.verticalScrollBar().setStyleSheet("QScrollBar:vertical { border: none; background: rgb(75, 75, 75); width: 5px; margin: 5 0 0 0; border-radius: 2px; }"
                                                                          "QScrollBar::handle:vertical { background-color:  rgb(130, 130, 130); min-height: 30px; border-radius: 2px; }"
                                                                          "QScrollBar::handle:vertical:hover { background-color: rgb(200, 200, 200); }"
                                                                          "QScrollBar::handle:vertical:pressed { background-color: rgb(255, 255, 255); }" 
                                                                          "QScrollBar::sub-page:vertical, QScrollBar::sub-line:vertical, QScrollBar::add-page:vertical, QScrollBar::add-line:vertical { background: none; }"
                                                                          )

        self.standardBannerTableWidget.setColumnWidth(0, 120)  # was 130 without scrollbar
        self.standardBannerTableWidget.setColumnWidth(1, 118)  # 118
        self.standardBannerTableWidget.setColumnWidth(2, 30)
        self.standardBannerTableWidget.setColumnHidden(3, True)
        for i in range(3):
            self.standardBannerTableWidget.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Fixed)
        self.standardBannerTableWidget.verticalScrollBar().setStyleSheet("QScrollBar:vertical { border: none; background: rgb(75, 75, 75); width: 5px; margin: 5 0 0 0; border-radius: 2px; }"
                                                                          "QScrollBar::handle:vertical { background-color:  rgb(130, 130, 130); min-height: 30px; border-radius: 2px; }"
                                                                          "QScrollBar::handle:vertical:hover { background-color: rgb(200, 200, 200); }"
                                                                          "QScrollBar::handle:vertical:pressed { background-color: rgb(255, 255, 255); }" 
                                                                          "QScrollBar::sub-page:vertical, QScrollBar::sub-line:vertical, QScrollBar::add-page:vertical, QScrollBar::add-line:vertical { background: none; }"
                                                                          )

        self.beginnerBannerTableWidget.setColumnWidth(0, 120)  # was 130 without scrollbar
        self.beginnerBannerTableWidget.setColumnWidth(1, 118)  # 118
        self.beginnerBannerTableWidget.setColumnWidth(2, 30)
        self.beginnerBannerTableWidget.setColumnHidden(3, True)
        for i in range(3):
            self.beginnerBannerTableWidget.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Fixed)
        self.beginnerBannerTableWidget.verticalScrollBar().setStyleSheet("QScrollBar:vertical { border: none; background: rgb(75, 75, 75); width: 5px; margin: 5 0 0 0; border-radius: 2px; }"
                                                                          "QScrollBar::handle:vertical { background-color:  rgb(130, 130, 130); min-height: 30px; border-radius: 2px; }"
                                                                          "QScrollBar::handle:vertical:hover { background-color: rgb(200, 200, 200); }"
                                                                          "QScrollBar::handle:vertical:pressed { background-color: rgb(255, 255, 255); }" 
                                                                          "QScrollBar::sub-page:vertical, QScrollBar::sub-line:vertical, QScrollBar::add-page:vertical, QScrollBar::add-line:vertical { background: none; }"
                                                                          )
        # ----------DONE WITH SETTING TABLES----------

        self.menuBarVLayout.setAlignment(Qt.AlignTop)

        self.minimizeButton.clicked.connect(self.showMinimized)
        self.maximizeRestoreButton.clicked.connect(self.maximize_restore)
        self.closeButton.clicked.connect(self.on_click_close_button)

        self.characterBannerTableButton.clicked.connect(self.on_click_character_banner_table_button)
        self.characterBannerAddButton.clicked.connect(lambda: self.on_click_banner_add_button("wishCharacter"))
        self.weaponBannerTableButton.clicked.connect(self.on_click_weapon_banner_table_button)
        self.weaponBannerAddButton.clicked.connect(lambda: self.on_click_banner_add_button("wishWeapon"))
        self.standardBannerTableButton.clicked.connect(self.on_click_standard_banner_table_button)
        self.standardBannerAddButton.clicked.connect(lambda: self.on_click_banner_add_button("wishStandard"))
        self.beginnerBannerTableButton.clicked.connect(self.on_click_beginner_banner_table_button)
        self.beginnerBannerAddButton.clicked.connect(lambda: self.on_click_banner_add_button("wishBeginner"))

        self.characterBannerFiveStarButton.clicked.connect(self.update_character_wish_table)
        self.characterBannerFourStarButton.clicked.connect(self.update_character_wish_table)

        self.weaponBannerFiveStarButton.clicked.connect(self.update_weapon_wish_table)
        self.weaponBannerFourStarButton.clicked.connect(self.update_weapon_wish_table)

        self.standardBannerFiveStarButton.clicked.connect(self.update_standard_wish_table)
        self.standardBannerFourStarButton.clicked.connect(self.update_standard_wish_table)

        self.beginnerBannerFiveStarButton.clicked.connect(self.update_beginner_wish_table)
        self.beginnerBannerFourStarButton.clicked.connect(self.update_beginner_wish_table)

        self.update_wish_ui()

    def on_click_close_button(self):
        self.close()

    def on_click_character_banner_table_button(self):
        if self.characterBannerTableButton.text() == "^":
            self.characterBannerFrame_Bottom.setVisible(False)
            self.characterBannerTableButton.setText("v")
            print("Banner Frame geometry: {}".format(self.characterBannerFrame.geometry()))
            print("Banner Frame Top geometry: {}".format(self.characterBannerFrame_Top.geometry()))
            print("Banner Frame Bottom geometry: {}".format(self.characterBannerFrame_Bottom.geometry()))
            print("Banner Table Widget geometry: {}".format(self.characterBannerTableWidget.geometry()))
            print("-----------")
            # self.characterBannerFrame.updateGeometry()
            z = self.characterBannerFrame.sizeHint()
            # self.characterBannerFrame.resize(self.characterBannerFrame.sizeHint())
            self.characterBannerFrame_Bottom.updateGeometry()
            self.characterBannerFrame.adjustSize()
        else:
            self.characterBannerFrame_Bottom.setVisible(True)
            self.characterBannerTableButton.setText("^")
            print("Banner Frame geometry: {}".format(self.characterBannerFrame.geometry()))
            print("Banner Frame Top geometry: {}".format(self.characterBannerFrame_Top.geometry()))
            print("Banner Frame Bottom geometry: {}".format(self.characterBannerFrame_Bottom.geometry()))
            print("Banner Table Widget geometry: {}".format(self.characterBannerTableWidget.geometry()))
            print("-----------")
            # self.characterBannerFrame.updateGeometry()
            # self.characterBannerFrame.resize(self.characterBannerFrame.sizeHint())
            self.characterBannerFrame_Bottom.updateGeometry()
            self.characterBannerFrame.adjustSize()

    def on_click_weapon_banner_table_button(self):
        if self.weaponBannerTableButton.text() == "^":
            self.weaponBannerFrame_Bottom.setVisible(False)
            self.weaponBannerTableButton.setText("v")
            self.weaponBannerFrame_Bottom.updateGeometry()
            self.weaponBannerFrame.adjustSize()
        else:
            self.weaponBannerFrame_Bottom.setVisible(True)
            self.weaponBannerTableButton.setText("^")
            self.weaponBannerFrame_Bottom.updateGeometry()
            self.weaponBannerFrame.adjustSize()

    def on_click_standard_banner_table_button(self):
        if self.standardBannerTableButton.text() == "^":
            self.standardBannerFrame_Bottom.setVisible(False)
            self.standardBannerTableButton.setText("v")
            self.standardBannerFrame_Bottom.updateGeometry()
            self.standardBannerFrame.adjustSize()
        else:
            self.standardBannerFrame_Bottom.setVisible(True)
            self.standardBannerTableButton.setText("^")
            self.standardBannerFrame_Bottom.updateGeometry()
            self.standardBannerFrame.adjustSize()

    def on_click_beginner_banner_table_button(self):
        if self.beginnerBannerTableButton.text() == "^":
            self.beginnerBannerFrame_Bottom.setVisible(False)
            self.beginnerBannerTableButton.setText("v")
            self.beginnerBannerFrame_Bottom.updateGeometry()
            self.beginnerBannerFrame.adjustSize()
        else:
            self.beginnerBannerFrame_Bottom.setVisible(True)
            self.beginnerBannerTableButton.setText("^")
            self.beginnerBannerFrame_Bottom.updateGeometry()
            self.beginnerBannerFrame.adjustSize()

    def update_character_wish_table(self):
        # TODO rethink how to implement this
        # maybe add hidden column with rarity and remove from end?
        # clear table and sort by id
        self.characterBannerTableWidget.setRowCount(0)
        self.characterBannerTableWidget.sortItems(3, Qt.AscendingOrder)

        if self.characterBannerFiveStarButton.isChecked():
            pity_number_5_star = 0
            for wish in self.wish_entries['wishCharacter']:
                pity_number_5_star = pity_number_5_star + 1
                if wish[3] == 5:
                    self.characterBannerTableWidget.insertRow(self.characterBannerTableWidget.rowCount())

                    self.characterBannerTableWidget.setItem(self.characterBannerTableWidget.rowCount() - 1, 0, QTableWidgetItem(wish[1]))  # name
                    self.characterBannerTableWidget.setItem(self.characterBannerTableWidget.rowCount() - 1, 1, QTableWidgetItem(wish[2]))  # date
                    self.characterBannerTableWidget.setItem(self.characterBannerTableWidget.rowCount() - 1, 2, QTableWidgetItem((' ' + str(pity_number_5_star))[-2:]))  # pity
                    self.characterBannerTableWidget.setItem(self.characterBannerTableWidget.rowCount() - 1, 3, QTableWidgetItem("{:03d}".format(self.characterBannerTableWidget.rowCount() - 1)))  # id

                    # color item to gold
                    for column in range(3):
                        self.characterBannerTableWidget.item(self.characterBannerTableWidget.rowCount() - 1, column).setForeground(QBrush(QColor(255, 215, 0)))
                    pity_number_5_star = 0

        if self.characterBannerFourStarButton.isChecked():
            pity_number_4_star = 0
            for wish in self.wish_entries['wishCharacter']:
                pity_number_4_star = pity_number_4_star + 1
                if wish[3] == 4:
                    self.characterBannerTableWidget.insertRow(self.characterBannerTableWidget.rowCount())

                    self.characterBannerTableWidget.setItem(self.characterBannerTableWidget.rowCount() - 1, 0, QTableWidgetItem(wish[1]))  # name
                    self.characterBannerTableWidget.setItem(self.characterBannerTableWidget.rowCount() - 1, 1, QTableWidgetItem(wish[2]))  # date
                    self.characterBannerTableWidget.setItem(self.characterBannerTableWidget.rowCount() - 1, 2, QTableWidgetItem((' ' + str(pity_number_4_star))[-2:])) # pity
                    self.characterBannerTableWidget.setItem(self.characterBannerTableWidget.rowCount() - 1, 3, QTableWidgetItem("{:03d}".format(self.characterBannerTableWidget.rowCount() - 1)))  # id

                    # color item to violet
                    for column in range(3):
                        self.characterBannerTableWidget.item(self.characterBannerTableWidget.rowCount() - 1, column).setForeground(QBrush(QColor(238, 130, 238)))
                    pity_number_4_star = 0

    def update_weapon_wish_table(self):
        # TODO rethink how to implement this
        # clear table and sort by id
        self.weaponBannerTableWidget.setRowCount(0)
        self.weaponBannerTableWidget.sortItems(3, Qt.AscendingOrder)

        if self.weaponBannerFiveStarButton.isChecked():
            pity_number_5_star = 0
            for wish in self.wish_entries['wishWeapon']:
                pity_number_5_star = pity_number_5_star + 1
                if wish[3] == 5:
                    self.weaponBannerTableWidget.insertRow(self.weaponBannerTableWidget.rowCount())

                    self.weaponBannerTableWidget.setItem(self.weaponBannerTableWidget.rowCount() - 1, 0, QTableWidgetItem(wish[1]))  # name
                    self.weaponBannerTableWidget.setItem(self.weaponBannerTableWidget.rowCount() - 1, 1, QTableWidgetItem(wish[2]))  # date
                    self.weaponBannerTableWidget.setItem(self.weaponBannerTableWidget.rowCount() - 1, 2, QTableWidgetItem((' ' + str(pity_number_5_star))[-2:]))   # pity
                    self.weaponBannerTableWidget.setItem(self.weaponBannerTableWidget.rowCount() - 1, 3, QTableWidgetItem("{:03d}".format(self.weaponBannerTableWidget.rowCount() - 1)))  # id

                    # color item to gold
                    for column in range(3):
                        self.weaponBannerTableWidget.item(self.weaponBannerTableWidget.rowCount() - 1, column).setForeground(QBrush(QColor(255, 215, 0)))
                    pity_number_5_star = 0

        if self.weaponBannerFourStarButton.isChecked():
            pity_number_4_star = 0
            for wish in self.wish_entries['wishWeapon']:
                pity_number_4_star = pity_number_4_star + 1
                if wish[3] == 4:
                    self.weaponBannerTableWidget.insertRow(self.weaponBannerTableWidget.rowCount())

                    self.weaponBannerTableWidget.setItem(self.weaponBannerTableWidget.rowCount() - 1, 0, QTableWidgetItem(wish[1]))  # name
                    self.weaponBannerTableWidget.setItem(self.weaponBannerTableWidget.rowCount() - 1, 1, QTableWidgetItem(wish[2]))  # date
                    self.weaponBannerTableWidget.setItem(self.weaponBannerTableWidget.rowCount() - 1, 2, QTableWidgetItem((' ' + str(pity_number_4_star))[-2:]))  # pity
                    self.weaponBannerTableWidget.setItem(self.weaponBannerTableWidget.rowCount() - 1, 3, QTableWidgetItem("{:03d}".format(self.weaponBannerTableWidget.rowCount() - 1)))  # id

                    # color item to violet
                    for column in range(3):
                        self.weaponBannerTableWidget.item(self.weaponBannerTableWidget.rowCount() - 1, column).setForeground(QBrush(QColor(238, 130, 238)))
                    pity_number_4_star = 0

    def update_standard_wish_table(self):
        # TODO rethink how to implement this
        # clear table and sort by id
        self.standardBannerTableWidget.setRowCount(0)
        self.standardBannerTableWidget.sortItems(3, Qt.AscendingOrder)

        if self.standardBannerFiveStarButton.isChecked():
            pity_number_5_star = 0
            for wish in self.wish_entries['wishStandard']:
                pity_number_5_star = pity_number_5_star + 1
                if wish[3] == 5:
                    self.standardBannerTableWidget.insertRow(self.standardBannerTableWidget.rowCount())

                    self.standardBannerTableWidget.setItem(self.standardBannerTableWidget.rowCount() - 1, 0, QTableWidgetItem(wish[1]))  # name
                    self.standardBannerTableWidget.setItem(self.standardBannerTableWidget.rowCount() - 1, 1, QTableWidgetItem(wish[2]))  # date
                    self.standardBannerTableWidget.setItem(self.standardBannerTableWidget.rowCount() - 1, 2, QTableWidgetItem((' ' + str(pity_number_5_star))[-2:]))  # pity
                    self.standardBannerTableWidget.setItem(self.standardBannerTableWidget.rowCount() - 1, 3, QTableWidgetItem("{:03d}".format(self.standardBannerTableWidget.rowCount() - 1)))  # id
                    # color item to gold
                    for column in range(3):
                        self.standardBannerTableWidget.item(self.standardBannerTableWidget.rowCount() - 1, column).setForeground(QBrush(QColor(255, 215, 0)))
                    pity_number_5_star = 0

        if self.standardBannerFourStarButton.isChecked():
            pity_number_4_star = 0
            for wish in self.wish_entries['wishStandard']:
                pity_number_4_star = pity_number_4_star + 1
                if wish[3] == 4:
                    self.standardBannerTableWidget.insertRow(self.standardBannerTableWidget.rowCount())

                    self.standardBannerTableWidget.setItem(self.standardBannerTableWidget.rowCount() - 1, 0, QTableWidgetItem(wish[1]))  # name
                    self.standardBannerTableWidget.setItem(self.standardBannerTableWidget.rowCount() - 1, 1, QTableWidgetItem(wish[2]))  # date
                    self.standardBannerTableWidget.setItem(self.standardBannerTableWidget.rowCount() - 1, 2, QTableWidgetItem((' ' + str(pity_number_4_star))[-2:]))  # pity
                    self.standardBannerTableWidget.setItem(self.standardBannerTableWidget.rowCount() - 1, 3, QTableWidgetItem("{:03d}".format(self.standardBannerTableWidget.rowCount() - 1)))  # id

                    # color item to violet
                    for column in range(3):
                        self.standardBannerTableWidget.item(self.standardBannerTableWidget.rowCount() - 1, column).setForeground(QBrush(QColor(238, 130, 238)))
                    pity_number_4_star = 0

    def update_beginner_wish_table(self):
        # TODO rethink how to implement this
        # clear table and sort by id
        self.beginnerBannerTableWidget.setRowCount(0)
        self.beginnerBannerTableWidget.sortItems(3, Qt.AscendingOrder)

        if self.beginnerBannerFiveStarButton.isChecked():
            pity_number_5_star = 0
            for wish in self.wish_entries['wishBeginner']:
                pity_number_5_star = pity_number_5_star + 1
                if wish[3] == 5:
                    self.beginnerBannerTableWidget.insertRow(self.beginnerBannerTableWidget.rowCount())

                    self.beginnerBannerTableWidget.setItem(self.beginnerBannerTableWidget.rowCount() - 1, 0, QTableWidgetItem(wish[1]))  # name
                    self.beginnerBannerTableWidget.setItem(self.beginnerBannerTableWidget.rowCount() - 1, 1, QTableWidgetItem(wish[2]))  # date
                    self.beginnerBannerTableWidget.setItem(self.beginnerBannerTableWidget.rowCount() - 1, 2, QTableWidgetItem((' ' + str(pity_number_5_star))[-2:]))   # pity
                    self.beginnerBannerTableWidget.setItem(self.beginnerBannerTableWidget.rowCount() - 1, 3, QTableWidgetItem("{:03d}".format(self.beginnerBannerTableWidget.rowCount() - 1)))  # id

                    # color item to gold
                    for column in range(3):
                        self.beginnerBannerTableWidget.item(self.beginnerBannerTableWidget.rowCount() - 1, column).setForeground(QBrush(QColor(255, 215, 0)))
                    pity_number_5_star = 0

        if self.beginnerBannerFourStarButton.isChecked():
            pity_number_4_star = 0
            for wish in self.wish_entries['wishBeginner']:
                pity_number_4_star = pity_number_4_star + 1
                if wish[3] == 4:
                    self.beginnerBannerTableWidget.insertRow(self.beginnerBannerTableWidget.rowCount())

                    self.beginnerBannerTableWidget.setItem(self.beginnerBannerTableWidget.rowCount() - 1, 0, QTableWidgetItem(wish[1]))  # name
                    self.beginnerBannerTableWidget.setItem(self.beginnerBannerTableWidget.rowCount() - 1, 1, QTableWidgetItem(wish[2]))  # date
                    self.beginnerBannerTableWidget.setItem(self.beginnerBannerTableWidget.rowCount() - 1, 2, QTableWidgetItem((' ' + str(pity_number_4_star))[-2:]))  # pity
                    self.beginnerBannerTableWidget.setItem(self.beginnerBannerTableWidget.rowCount() - 1, 3, QTableWidgetItem("{:03d}".format(self.beginnerBannerTableWidget.rowCount() - 1)))  # id

                    # color item to violet
                    for column in range(3):
                        self.beginnerBannerTableWidget.item(self.beginnerBannerTableWidget.rowCount() - 1, column).setForeground(QBrush(QColor(238, 130, 238)))
                    pity_number_4_star = 0

    def on_click_banner_add_button(self, banner_type):
        dialog = ImportWishDialog(banner_type)
        dialog.reload_memory_wishes.connect(self.load_wishes_to_memory_from_db)
        dialog.insert_wishes_to_memory.connect(self.add_wishes_to_memory)
        dialog.exec_()

    def load_wishes_to_memory_from_db(self):
        for key in self.wish_entries:
            self.wish_entries[key] = self.db.get_wishes_from_table(key)
        self.update_wish_ui()

    def add_wishes_to_memory(self, wishes, banner_type):
        # someone could give wrong banner_type
        for wish in wishes:
            self.wish_entries[banner_type].append(wish)
        self.update_wish_ui()

    def update_wish_ui(self):
        # TODO dont update ui, if it wasn't changed
        self.characterBannerLabel_2_3.setText("{}".format(len(self.wish_entries['wishCharacter'])))  # lifetime pulls
        self.characterBannerLabel_2_1_2.setText("{:,}".format(len(self.wish_entries['wishCharacter']) * 160).replace(',', ' '))  # primo
        self.characterBannerLabel_3_3.setText("{}".format(self.get_pity_number(self.wish_entries['wishCharacter'], 5)))  # 5* pity
        self.characterBannerLabel_4_3.setText("{}".format(self.get_pity_number(self.wish_entries['wishCharacter'], 4)))  # 4* pity

        self.weaponBannerLabel_2_3.setText("{}".format(len(self.wish_entries['wishWeapon'])))  # lifetime pulls
        self.weaponBannerLabel_2_1_2.setText("{:,}".format(len(self.wish_entries['wishWeapon']) * 160).replace(',', ' '))  # primo
        self.weaponBannerLabel_3_3.setText("{}".format(self.get_pity_number(self.wish_entries['wishWeapon'], 5)))  # 5* pity
        self.weaponBannerLabel_4_3.setText("{}".format(self.get_pity_number(self.wish_entries['wishWeapon'], 4)))  # 4* pity

        self.standardBannerLabel_2_3.setText("{}".format(len(self.wish_entries['wishStandard'])))  # lifetime pulls
        self.standardBannerLabel_2_1_2.setText("{:,}".format(len(self.wish_entries['wishStandard']) * 160).replace(',', ' '))  # primo
        self.standardBannerLabel_3_3.setText("{}".format(self.get_pity_number(self.wish_entries['wishStandard'], 5)))  # 5* pity
        self.standardBannerLabel_4_3.setText("{}".format(self.get_pity_number(self.wish_entries['wishStandard'], 4)))  # 4* pity

        self.beginnerBannerLabel_2_3.setText("{}".format(len(self.wish_entries['wishBeginner'])))  # lifetime pulls
        self.beginnerBannerLabel_2_1_2.setText("{:,}".format(len(self.wish_entries['wishBeginner']) * 160).replace(',', ' '))  # primo
        self.beginnerBannerLabel_3_3.setText("{}".format(self.get_pity_number(self.wish_entries['wishBeginner'], 5)))  # 5* pity
        self.beginnerBannerLabel_4_3.setText("{}".format(self.get_pity_number(self.wish_entries['wishBeginner'], 4)))  # 4* pity

    def get_pity_number(self, wish_list, rarity):
        # if wish_list is empty
        if not wish_list:
            return 0
        for idx, wish in enumerate(reversed(wish_list)):
            if wish[3] == rarity:
                return idx
        # there are entries, but none with sought rarity
        return len(wish_list)

    def make_window_frameless(self):
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.sideGrips = [
            SideGrip(self, Qt.LeftEdge),
            SideGrip(self, Qt.TopEdge),
            SideGrip(self, Qt.RightEdge),
            SideGrip(self, Qt.BottomEdge),
        ]
        # corner grips should be "on top" of everything, otherwise the side grips
        # will take precedence on mouse events, so we are adding them *after*;
        # alternatively, widget.raise_() can be used
        self.cornerGrips = [QSizeGrip(self) for i in range(4)]

        self.titleBarFrame_1.mouseDoubleClickEvent = self.double_click_to_maximize
        self.titleBarFrame_1.mousePressEvent = self.press_window
        self.titleBarFrame_1.mouseMoveEvent = self.move_window

    @property
    def gripSize(self):
        return self._gripSize

    def setGripSize(self, size):
        if size == self._gripSize:
            return
        self._gripSize = max(2, size)
        self.updateGrips()

    def updateGrips(self):
        self.setContentsMargins(*[self.gripSize] * 4)

        outRect = self.rect()
        # an "inner" rect used for reference to set the geometries of size grips
        inRect = outRect.adjusted(self.gripSize, self.gripSize,
                                  -self.gripSize, -self.gripSize)

        # top left
        self.cornerGrips[0].setGeometry(
            QRect(outRect.topLeft(), inRect.topLeft()))
        # top right
        self.cornerGrips[1].setGeometry(
            QRect(outRect.topRight(), inRect.topRight()).normalized())
        # bottom right
        self.cornerGrips[2].setGeometry(
            QRect(inRect.bottomRight(), outRect.bottomRight()))
        # bottom left
        self.cornerGrips[3].setGeometry(
            QRect(outRect.bottomLeft(), inRect.bottomLeft()).normalized())

        # left edge
        self.sideGrips[0].setGeometry(
            0, inRect.top(), self.gripSize, inRect.height())
        # top edge
        self.sideGrips[1].setGeometry(
            inRect.left(), 0, inRect.width(), self.gripSize)
        # right edge
        self.sideGrips[2].setGeometry(
            inRect.left() + inRect.width(),
            inRect.top(), self.gripSize, inRect.height())
        # bottom edge
        self.sideGrips[3].setGeometry(
            self.gripSize, inRect.top() + inRect.height(),
            inRect.width(), self.gripSize)

    def resizeEvent(self, event):
        QMainWindow.resizeEvent(self, event)
        self.updateGrips()

    def maximize_restore(self):
        print(self.maximized)
        if self.maximized:
            self.showNormal()
            self.maximized = False
            self.maximizeRestoreButton.setIcon(QIcon("icons/maximize_white.png"))
        else:
            self.showMaximized()
            self.maximized = True
            self.maximizeRestoreButton.setIcon(QIcon("icons/restore_white.png"))

    def double_click_to_maximize(self, event):
        if event.type() == QEvent.MouseButtonDblClick:
            QTimer.singleShot(250, lambda: self.maximize_restore())

    def press_window(self, event):
        if event.buttons() == Qt.LeftButton:
            self.drag_pos = event.globalPos()
            print("press_window - {}".format(event.globalPos()))
            event.accept()

    def move_window(self, event):
        if self.maximized:
            self.maximize_restore()

        if event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.globalPos() - self.drag_pos)
            self.drag_pos = event.globalPos()
            print("move_window - {} {} {}".format(self.pos(), event.globalPos(), self.drag_pos))
            event.accept()

    def set_dark_mode_theme(self):
        # https://stackoverflow.com/questions/48256772/dark-theme-for-qt-widgets
        palette = QPalette()
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.ButtonText, Qt.black)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.black)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        self.setPalette(palette)


def main():
    args = parse_arguments()
    init_logger(args.debug)

    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()

    # wi = WishImporter('db')
    # for i in range(22):
    #     img_path = "D:/Repo/genshin-wish-viewer/wishCharacterTest/{:02}.JPG".format(i)
    #     wishes = wi.get_wishes_from_imagev2(img_path)
    #     print("***")

    # wi = WishImporter()
    # for i in range(54):
    #     img_path = "D:/Repo/genshin-wish-viewer/img/CW-0{:02}.JPG".format(i+1)
    #     img, img_gray = wi.load_image(img_path)
    #     coordinates = wi.get_text_countours(img_gray)
    #     wishes = wi.get_wishes_from_image(img_gray, coordinates)
    #     for item in wishes:
    #         print(item)
    #     print("--------")

    print("bla")


if __name__ == "__main__":
    main()
