import cv2
import numpy as np
import matplotlib.pyplot as plt
import pytesseract
import logging
import os

# https://medium.com/analytics-vidhya/how-to-detect-tables-in-images-using-opencv-and-python-6a0f15e560c3
# https://docs.opencv.org/master/d9/d61/tutorial_py_morphological_ops.html


# import wishes from jpg files of wish history in genshin.
# give option to download wish history using genshin web page url.
class WishImporter:
    db = None

    def __init__(self, database):
        self.db = database

    def load_image(self, img_path):
        # img = cv2.imread(img_path)
        img_gray = cv2.imread(img_path, 0)
        return img_gray

    def save_image(self, img, save_path):
        cv2.imwrite(save_path, img)

    def binarization(self, img, threshold, otsu=False):
        thresholding_type = cv2.THRESH_BINARY_INV
        if otsu:
            # Otsu method will automatically compute the optimal value of threshold and ignore the one that was provided
            thresholding_type = thresholding_type | cv2.THRESH_OTSU
        ret, img_bin = cv2.threshold(img, threshold, 255, thresholding_type)

    def get_text_countours(self, img_gray):
        ret, img_binarized = cv2.threshold(img_gray, 241, 255, cv2.THRESH_BINARY)

        kernel_30 = np.ones((30, 30), np.uint8)
        img_dilated = cv2.dilate(img_binarized, kernel_30, iterations=1)

        contours, hierarchy = cv2.findContours(img_dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        coordinates = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            x = x-5
            w = w+10
            # discard artifacts or table lines, only append wish values coordinates
            if w > 75:
                coordinates.append((x, y, w, h))
                # draw rectangles over original img
                # cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 1)

        # Sorting. findContours sorts by y. if y1 == y2 then it looks at x (basically scans from bottom left to right).
        # Elements in same row may have a few pixels difference between each other which will mess up their order.
        # Also you should have 3 elements in 1 row, otherwise something wasn't detected!
        if (len(coordinates) % 3) == 0:
            grouped_coordinates = []
            wish_coordinates = []
            for count, crd in enumerate(coordinates, start=1):
                wish_coordinates.append(crd)
                if count % 3 == 0:
                    # sort by x
                    grouped_coordinates.append(sorted(wish_coordinates, key=lambda coordinate_x: coordinate_x[0]))
                    wish_coordinates = []
        else:
            # TODO give some hint on what image we failed, maybe give coordinates values
            raise Exception("Number of detected objects wasn't multiplication of 3")
        return grouped_coordinates

    def get_text_from_image(self, img, xconfig="-c page_separator=''"):
        text = pytesseract.image_to_string(img, config=xconfig)
        if not text:
            raise Exception("Failed to read text from image.")
        return text

    # def get_wishes_from_image(self, img, coordinates):
    #     text = []
    #     # pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
    #     # pytesseract.get_tesseract_version()
    #     for item in coordinates:
    #         wish = []
    #         for crdnt in item:
    #             img_snip = img[crdnt[1]:crdnt[1] + crdnt[3], crdnt[0]:crdnt[0] + crdnt[2]]
    #             wish.append(self.get_text_from_image(img_snip)[:-1])  # remove end of line char at the end
    #         text.append(wish)
    #     return text

    def import_from_dir(self, dir_path, table_name):
        if table_name not in ["wishCharacter", "wishWeapon", "wishStandard", "wishBeginner"]:
            logging.error("Wrong table name!")
            return
        img_paths = self.get_image_paths_from_dir_path(dir_path)
        for img_path in img_paths:
            wishes = self.get_wishes_from_image(img_path)
            if not self.check_if_wishes_are_already_in_db(wishes):
                self.insert_to_db(wishes, table_name)
            else:
                logging.info("Wishes: {} are already in db!".format(wishes))

    def import_from_list_of_image_paths(self, img_paths, table_name):
        if table_name not in ["wishCharacter", "wishWeapon", "wishStandard", "wishBeginner"]:
            logging.error("Wrong table name!")
            return
        for img_path in img_paths:
            wishes = self.get_wishes_from_image(img_path)
            if not self.check_if_wishes_are_already_in_db(wishes):
                self.insert_to_db(wishes, table_name)
            else:
                logging.info("Wishes: {} are already in db!".format(wishes))

    def get_image_paths_from_dir_path(self, dir_path):
        if dir_path == "":
            raise Exception("Got empty string of directory path!")
        img_paths = []
        for file in os.listdir(dir_path):
            if file.endswith(".jpg") or file.endswith(".JPG"):
                img_paths.append(dir_path + "/" + file)
        return img_paths

    def add_rarity_to_wish(self, wish):
        position = wish[1].find("(")
        if position == -1:
            wish.append(3)
        else:
            # add rarity (4 or 5) and trim item name
            wish.append(wish[1][position+1])
            wish[1] = wish[1][:position-1]
        return wish

    def get_wishes_from_image(self, img_path):
        img_gray = self.load_image(img_path)
        coordinates = self.get_text_countours(img_gray)
        wishes = []
        # pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
        # pytesseract.get_tesseract_version()
        for item in coordinates:
            wish = []
            for crdnt in item:
                img_snip = img_gray[crdnt[1]:crdnt[1] + crdnt[3], crdnt[0]:crdnt[0] + crdnt[2]]
                wish.append(self.get_text_from_image(img_snip)[:-1])  # remove end of line char at the end
            wishes.append(self.add_rarity_to_wish(wish))
        return wishes

    def check_if_wishes_are_already_in_db(self, wishes):
        # TODO implement!
        return False

    def insert_to_db(self, wishes, table_name):
        # TODO check if connection is alive?
        if len(wishes) == 1:
            self.db.insert_wish_entry(table_name, wishes[0])
        elif len(wishes) > 1:
            self.db.insert_multiple_wish_entries(table_name, wishes)
        else:
            # no wishes - suspicious
            logging.info("No wishes to insert to database...")



    def show_img(self, img_path):
        plt.imshow(img_path, cmap='gray', interpolation='bicubic')
        plt.xticks([]), plt.yticks([])  # to hide tick values on X and Y axis
        plt.show()



#
# # We apply a inverse binary threshold to the image. In this method we set minimum threshold value as 180 and max
# # being 255. Binary threshold converts any pixel value above 180 to 255 and below 180 to 0. THRESH_BINARY_INV
# # is the inverse of binary threshold.
# ret, thresh_value = cv2.threshold(im1, 180, 255, cv2.THRESH_BINARY_INV)
#
# # Then we will set a kernel of size (5,5) and perform image dilation with it. We can tweak the kernel size and number
# # of iteration as per our need and requirements.
# kernel = np.ones((5, 5), np.uint8)
# dilated_value = cv2.dilate(thresh_value, kernel, iterations=1)
#
# # We will find the contours around the using OpenCV using findContours.
# contours, hierarchy = cv2.findContours(dilated_value, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
#
# # After the contours are detected and saved in contours variable we draw the contours on our image. Note that
# # we are drawing the contours on our original image im which has been untouched till now and no manipulations
# # has been applied on it.
# cordinates = []
# for cnt in contours:
#     x, y, w, h = cv2.boundingRect(cnt)
#     cordinates.append((x, y, w, h))
#     # bounding the images
#     if y < 50:
#         cv2.rectangle(im, (x, y), (x + w, y + h), (0, 0, 255), 1)
#
#
# thresh = np.vstack([thresh1, thresh250])
# reta,thresha = cv2.threshold(im1,240,255,cv2.THRESH_BINARY_INV)
# kernel = np.ones((9, 9), np.uint8)
# dilated_value = cv2.erode(thresha, kernel, iterations=1)
# opening = cv2.morphologyEx(dilated_value, cv2.MORPH_OPEN, kernel)
# closing = cv2.morphologyEx(dilated_value, cv2.MORPH_CLOSE, kernel)
# # open 30, close 15