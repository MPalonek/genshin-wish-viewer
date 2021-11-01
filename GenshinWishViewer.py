from argparse import ArgumentParser
import logging
from datetime import date
import os
from database import WishDatabase
from ImportWishWindow import ImportWishDialog
from importer import WishImporter
import time
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QIcon, QPalette, QColor, QPixmap, QBitmap, QPainter
from PyQt5.QtCore import Qt, QSize, QEvent, QTimer, QRect, QMetaObject, QPoint
from PyQt5.QtWidgets import QApplication, QPushButton, QFrame, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QSizeGrip, QPushButton, QLabel
import sys
# potential UI - https://github.com/Wanderson-Magalhaes/Simple_PySide_Base/blob/master/main.py


def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument("-d", "--debug", '--DEBUG', action='store_true', help="set logging to be debug")
    return parser.parse_args()


def init_logger(debug):
    if debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    log_filename = "gwv_log_0.log"
    logging.basicConfig(filename=log_filename, format='%(asctime)s.%(msecs)03d %(levelname)s: %(message)s',
                        datefmt='%H:%M:%S', level=log_level)
    if os.path.isfile(log_filename):
        f = open(log_filename, "a")
        f.write("\n-----------------------------------------------------------------\n\n")
        f.close()
    logging.info('Starting Genshin Wish Viewer. Current date is: {}. Log level: {}'.format(date.today(), log_level))


class Ui(QtWidgets.QMainWindow):

    db = None
    wish_entries = {
        "wishCharacter": [],
        "wishWeapon": [],
        "wishStandard": [],
        "wishBeginner": []
    }

    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('mainwindow.ui', self)

        self.db = WishDatabase('db.db')
        self.db.initialize_database()

        self.setup_ui()
        self.show()

    def setup_ui(self):
        self.setWindowTitle("Genshin Wish Viewer")
        self.setWindowIcon(QIcon('icons/wish_icon_white_blur.png'))
        self.titleLabel.setText("Genshin Wish Viewer")
        self.iconLabel.setPixmap(QPixmap("icons/wish_icon_white_blur.png").scaled(20, 20, Qt.KeepAspectRatio))
        self.resize(1326, 556)
        # self.setWindowFlags(Qt.FramelessWindowHint)
        # self.set_dark_mode_theme()

        self.minimizeButton.setIcon(QIcon("icons/minimize_white.png"))
        self.maximizeRestoreButton.setIcon(QIcon("icons/maximize_white.png"))
        self.closeButton.setIcon(QIcon("icons/exit_white.png"))

        self.characterBannerTableWidget.setColumnWidth(0, 120)  # was 130 without scrollbar
        self.characterBannerTableWidget.setColumnWidth(1, 118)
        self.characterBannerTableWidget.setColumnWidth(2, 30)
        self.characterBannerTableWidget.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        self.characterBannerTableWidget.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        self.characterBannerTableWidget.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Fixed)

        self.characterBannerTableWidget.verticalScrollBar().setStyleSheet("QScrollBar:vertical { border: none; background: rgb(75, 75, 75); width: 5px; margin: 5 0 0 0; border-radius: 2px; }"
                                                                          "QScrollBar::handle:vertical { background-color:  rgb(130, 130, 130); min-height: 30px; border-radius: 2px; }"
                                                                          "QScrollBar::handle:vertical:hover { background-color: rgb(200, 200, 200); }"
                                                                          "QScrollBar::handle:vertical:pressed { background-color: rgb(255, 255, 255); }" 
                                                                          "QScrollBar::sub-page:vertical, QScrollBar::sub-line:vertical, QScrollBar::add-page:vertical, QScrollBar::add-line:vertical { background: none; }"
                                                                          )
        self.menuBarVLayout.setAlignment(Qt.AlignTop)

        self.characterBannerTableButton.clicked.connect(self.on_click_character_banner_table_button)
        self.characterBannerAddButton.clicked.connect(lambda: self.on_click_banner_add_button("wishCharacter"))
        self.weaponBannerTableButton.clicked.connect(self.on_click_weapon_banner_table_button)
        self.weaponBannerAddButton.clicked.connect(lambda: self.on_click_banner_add_button("wishWeapon"))
        self.standardBannerTableButton.clicked.connect(self.on_click_standard_banner_table_button)
        self.standardBannerAddButton.clicked.connect(lambda: self.on_click_banner_add_button("wishStandard"))
        self.beginnerBannerTableButton.clicked.connect(self.on_click_beginner_banner_table_button)
        self.beginnerBannerAddButton.clicked.connect(lambda: self.on_click_banner_add_button("wishBeginner"))

        self.load_wishes_to_memory()
        self.update_wish_ui()

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

    def update_wish_table(self):
        if self.characterBannerFiveStarButton.checked:
            # insert entries from memory to table
            pass
        else:
            # remove certain entries from tables
            pass

    def on_click_character_banner_four_star_button(self):
        pass

    def on_click_banner_add_button(self, banner_type):
        dialog = ImportWishDialog(banner_type)
        dialog.inserted_new_wishes.connect(self.inserted_new_wishes)
        dialog.exec_()

    def inserted_new_wishes(self):
        # new wishes in db?
        # check if there is more entries in db than in memory
        # reload memory
        # redraw ui
        self.load_wishes_to_memory()
        self.update_wish_ui()

    def load_wishes_to_memory(self):
        for key in self.wish_entries:
            self.wish_entries[key] = self.db.get_wishes_from_table(key)

    def update_wish_ui(self):
        # TODO dont update ui, if it wasn't changed
        self.characterBannerLabel_2_3.setText("{}".format(len(self.wish_entries['wishCharacter'])))  # lifetime pulls
        self.characterBannerLabel_2_1_2.setText("{:,}".format(len(self.wish_entries['wishCharacter']) * 160).replace(',', ' '))  # primo
        self.characterBannerLabel_3_3.setText("{}".format(self.get_pity_number(self.wish_entries['wishCharacter'], 5)))  # 5* pity
        self.characterBannerLabel_4_3.setText("{}".format(self.get_pity_number(self.wish_entries['wishCharacter'], 4)))  # 4* pity

        self.weaponBannerLabel_2_3.setText("{}".format(len(self.wish_entries['wishWeapon'])))  # lifetime pulls
        self.weaponBannerLabel_2_1_2.setText("{}".format(len(self.wish_entries['wishWeapon']) * 160).replace(',', ' '))  # primo
        self.weaponBannerLabel_3_3.setText("{}".format(self.get_pity_number(self.wish_entries['wishWeapon'], 5)))  # 5* pity
        self.weaponBannerLabel_4_3.setText("{}".format(self.get_pity_number(self.wish_entries['wishWeapon'], 4)))  # 4* pity

        self.standardBannerLabel_2_3.setText("{}".format(len(self.wish_entries['wishStandard'])))  # lifetime pulls
        self.standardBannerLabel_2_1_2.setText("{}".format(len(self.wish_entries['wishStandard']) * 160).replace(',', ' '))  # primo
        self.standardBannerLabel_3_3.setText("{}".format(self.get_pity_number(self.wish_entries['wishStandard'], 5)))  # 5* pity
        self.standardBannerLabel_4_3.setText("{}".format(self.get_pity_number(self.wish_entries['wishStandard'], 4)))  # 4* pity

        self.beginnerBannerLabel_2_3.setText("{}".format(len(self.wish_entries['wishBeginner'])))  # lifetime pulls
        self.beginnerBannerLabel_2_1_2.setText("{}".format(len(self.wish_entries['wishBeginner']) * 160).replace(',', ' '))  # primo
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

    # wi = WishImporter(db)
    # path = "D:/Repo/genshin-wish-viewer/wishCharacterTest"
    # wi.import_from_dir(path, "wishCharacter")

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
