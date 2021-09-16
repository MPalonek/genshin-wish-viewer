from argparse import ArgumentParser
import logging
from datetime import date
import os
from database import WishDatabase
from importer import WishImporter

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


def main():
    args = parse_arguments()
    init_logger(args.debug)

    db = WishDatabase("db.db")
    db.initialize_database()

    wi = WishImporter(db)
    path = "D:/Repo/genshin-wish-viewer/wishCharacterTest"
    wi.import_from_dir(path, "wishCharacter")

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
