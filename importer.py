import cv2
import numpy as np
import matplotlib.pyplot as plt
import pytesseract
import logging
import os

logger = logging.getLogger('GenshinWishViewer')
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

    def get_wishes_from_imagev2(self, img_path):
        logger.debug("get_wishes_from_image: img_path: {}". format(img_path))
        img_gray = self.load_image(img_path)

        # binarize image to have only table lines
        # first cut off values above 205, then binarize everything bigger than 185
        # so we end up with binarizing everything in range of (185, 205)
        # then do morphological operations as text has similar values as table lines
        ret, img_tozero = cv2.threshold(img_gray, 210, 255, cv2.THRESH_TOZERO_INV)
        ret, img_binarized = cv2.threshold(img_tozero, 180, 255, cv2.THRESH_BINARY)
        kernel = np.ones((3, 3), np.uint8)
        # open to get rid of text
        img_binarized = cv2.morphologyEx(img_binarized, cv2.MORPH_OPEN, kernel)
        # close to fill small holes in table lines
        img_binarized = cv2.morphologyEx(img_binarized, cv2.MORPH_CLOSE, kernel)
        # self.show_img(img_binarized)

        # calculate how wide and high is the table
        x_start, x_end = self.find_long_line(img_binarized)
        y_start, y_end = self.find_long_line(np.rot90(img_binarized))

        # self.show_img(img_binarized[y_start:y_end, x_start:x_end])

        # get rows coordinates
        rows_coords = []  # x_start, x_end, y_start, y_end
        ver_lines = self.find_separating_lines(np.rot90(img_binarized[y_start:y_end, x_start:x_end]))
        previous_y_start = y_start
        for i in ver_lines:
            rows_coords.append([x_start, x_end, previous_y_start, y_start + i[0]])
            previous_y_start = y_start + i[0]
        if (y_end - previous_y_start) > 30:
            rows_coords.append([x_start, x_end, previous_y_start, y_end])

        # seperate rows to get cells coordinates
        cell_coords = []  # x_start, x_end, y_start, y_end
        for i, crds in enumerate(rows_coords):
            hor_lines = self.find_separating_lines(img_binarized[crds[2]:crds[3], crds[0]:crds[1]])
            cell_coords.append([])
            previous_x_start = x_start
            for j in hor_lines:
                cell_coords[i].append([previous_x_start, x_start + j[0], crds[2], crds[3]])
                previous_x_start = x_start + j[0]
            cell_coords[i].append([previous_x_start, x_end, crds[2], crds[3]])
            if len(cell_coords[i]) == 3 or len(cell_coords[i]) == 4:
                pass
            else:
                raise Exception("Number of detected objects in a row wasn't 3 or 4. Len(cell_coords[{}]: {}".format(i, len(cell_coords[i])))

        # for i in cell_coords:
        #     for cell in i:
        #         self.show_img(img_gray[cell[2]:cell[3], cell[0]:cell[1]])

        # get wish text from cells in rows
        wishes = []
        for row in cell_coords:
            wish = []
            for crdnt in row:
                img_snip = img_gray[crdnt[2]:crdnt[3], crdnt[0]:crdnt[1]]
                wish.append(self.get_text_from_image(img_snip).strip().replace('\n', " "))  # remove whitespaces from string, replace is in case \n will be in the middle of string
            if wish[0] == "Item Type":
                continue
            # remove "wish type" information, if it's new schema
            if len(wish) == 4:
                wish.pop(2)
            wishes.append(self.add_rarity_to_wish(wish))

        # reverse wishes (the ones on bottom are older and they should be inserted first to db)
        wishes = wishes[::-1]

        for item in wishes:
            logger.debug(item)
        logger.debug("--------")
        return wishes

    def find_long_line(self, img, offset=5):
        start = 0
        end = 0
        found_line = False
        for y, row in enumerate(img):
            if found_line:
                break
            for x, cell in enumerate(row):
                if cell == 255:
                    if not found_line:
                        found_line = True
                        start = x
                        end = x

                    if x != 0 and row[x - 1] == 255:
                        end = x
                    elif start == end:
                        # corner case, when we found beginning of line
                        pass
                    else:
                        # we want to have a long line from start to beginning
                        # if there wasn't continuity and line is short - go to next row
                        found_line = False
                        break
                # if we didn't find table within 30 pixels go to next row
                if x == 30 and not found_line:
                    break
            # we found long line
            if (end - start) > 100:
                break
        start = start+offset
        end = end-offset

        # check if start or end is negative
        if any(x < 0 for x in [start, end]):
            raise Exception("find_long_line: either start: {} or end: {} has negative value!".format(start, end))

        logger.debug("find_long_line: start: {}, end: {}".format(start, end))
        return start, end

    def find_separating_lines(self, img):
        # we get image with lines only inside
        # lines around table should be removed when used find_long_line
        # so we can take whatever row
        grouped_lines_coords = []
        line_coords = []
        for x, cell in enumerate(img[10]):
            if cell == 255:
                line_coords.append(x)

        # merge values next to each other
        grouped = self.group_consecutives(line_coords)
        for x in grouped:
            grouped_lines_coords.append([min(x), max(x)])

        return grouped_lines_coords

    def group_consecutives(self, vals, step=1):
        """Return list of consecutive lists of numbers from vals (number list)."""
        run = []
        result = [run]
        expect = None
        for v in vals:
            if (v == expect) or (expect is None):
                run.append(v)
            else:
                run = [v]
                result.append(run)
            expect = v + step
        return result


    def get_text_contours(self, img_gray):
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

        return self.group_and_sort_text_contours(img_gray, coordinates)

    def group_and_sort_text_contours(self, img_gray, contour_crd):
        row_length = 3
        # Check, if image is new or old style (old style - 3 rows, new style - 4 rows)
        # In new style 3rd row is wish type. There can be 4 specific values in there.
        # Because findCounturs is sorted by y you have to get the whole row, sort by x and then you can check.
        if len(contour_crd) <= 3:
            pass
        else:
            single_row_contour_crd = sorted(contour_crd[:4], key=lambda coordinate_x: coordinate_x[0])
            third_row_img_snip = img_gray[single_row_contour_crd[2][1]:single_row_contour_crd[2][1] + single_row_contour_crd[2][3], single_row_contour_crd[2][0]:single_row_contour_crd[2][0] + single_row_contour_crd[2][2]]
            third_row_text = self.get_text_from_image(third_row_img_snip).replace('\n', " ").rstrip()
            # Beginner wish value might be wrong...
            wish_type_text = ["Character Event Wish", "Permanent Wish", "Weapon Event Wish", "Beginners' Wish"]
            if third_row_text in wish_type_text:
                row_length = 4

        # Sorting. findContours sorts by y. if y1 == y2 then it looks at x (basically scans from bottom left to right).
        # Elements in same row may have a few pixels difference between each other which will mess up their order.
        # Also you should have 3 or 4 elements in 1 row, otherwise something wasn't detected!
        if (len(contour_crd) % row_length) == 0:
            grouped_coordinates = []
            wish_coordinates = []
            for count, crd in enumerate(contour_crd, start=1):
                wish_coordinates.append(crd)
                if count % row_length == 0:
                    # sort by x
                    grouped_coordinates.append(sorted(wish_coordinates, key=lambda coordinate_x: coordinate_x[0]))
                    wish_coordinates = []
        else:
            # TODO give some hint on what image we failed, maybe give coordinates values
            raise Exception("Number of detected objects wasn't multiplication of {}. Len(contour_crd): {}".format(row_length, len(contour_crd)))

        # remove wish type, so what this function returns will work with the rest of the code as originally designed
        if row_length == 4:
            for i in range(len(grouped_coordinates)):
                grouped_coordinates[i].pop(2)
        return grouped_coordinates

    def get_text_from_image(self, img, xconfig="-c page_separator=''"):
        text = pytesseract.image_to_string(img, config=xconfig)
        if not text:
            raise Exception("Failed to read text from image.")
        return text

    def import_from_dir(self, dir_path, table_name):
        if table_name not in ["wishCharacter", "wishWeapon", "wishStandard", "wishBeginner"]:
            logger.error("Wrong table name!")
            return
        img_paths = self.get_image_paths_from_dir_path(dir_path)
        for img_path in img_paths:
            wishes = self.get_wishes_from_image(img_path)
            if not self.check_if_wishes_are_already_in_db(wishes):
                self.insert_to_db(wishes, table_name)
            else:
                logger.info("Wishes: {} are already in db!".format(wishes))

    def import_from_list_of_image_paths(self, img_paths, table_name):
        if table_name not in ["wishCharacter", "wishWeapon", "wishStandard", "wishBeginner"]:
            logger.error("Wrong table name!")
            return
        for img_path in img_paths:
            wishes = self.get_wishes_from_imagev2(img_path)
            if not self.check_if_wishes_are_already_in_db(wishes):
                self.insert_to_db(wishes, table_name)
            else:
                logger.info("Wishes: {} are already in db!".format(wishes))

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
        coordinates = self.get_text_contours(img_gray)
        wishes = []
        # pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
        # pytesseract.get_tesseract_version()
        for item in coordinates:
            wish = []
            for crdnt in item:
                img_snip = img_gray[crdnt[1]:crdnt[1] + crdnt[3], crdnt[0]:crdnt[0] + crdnt[2]]
                wish.append(self.get_text_from_image(img_snip).replace('\n', " ").rstrip())  # remove whitespaces from string, replace is in case \n will be in the middle of string
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
            logger.info("No wishes to insert to database...")



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