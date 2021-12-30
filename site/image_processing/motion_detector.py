# imports
import numpy as np
import imutils
import cv2


class MotionDetector:
    def __init__(self, accum_weight=0.5):
        # store the accumulated weight factor
        self.accum_weight = accum_weight

        # initialize the background model
        self.background = None

    def update(self, image):
        # if the background model is None, initialize it
        if self.background is None:
            self.background = image.copy().astype("float")
            return
        # update the background model by accumulating the weighted
        # average
        cv2.accumulateWeighted(image, self.background, self.accum_weight)

    def detect(self, image, thresh_val=25):
        # compute the absolute difference between the background model
        # and the image passed in, then threshold the delta image
        delta = cv2.absdiff(self.background.astype("uint8"), image)
        thresh = cv2.threshold(delta, thresh_val, 255, cv2.THRESH_BINARY)[1]

        # perform a series of erosions and dilations to remove small
        # blobs
        thresh = cv2.erode(thresh, None, iterations=2)
        thresh = cv2.dilate(thresh, None, iterations=2)

        # find contours in the thresholded image and initialize the
        # minimum and maximum bounding box regions for motion
        cnts = cv2.findContours(
            thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        cnts = imutils.grab_contours(cnts)
        (min_x, min_y) = (np.inf, np.inf)
        (max_x, max_y) = (-np.inf, -np.inf)

        # if no contours were found, return None
        if len(cnts) == 0:
            return None

        # otherwise, loop over the contours
        for contour in cnts:
            # compute the bounding box of the contour and use it to
            # update the minimum and maximum bounding box regions
            (x_coord, y_coord, width, height) = cv2.boundingRect(contour)
            (min_x, min_y) = (min(min_x, x_coord), min(min_y, y_coord))
            (max_x, max_y) = (max(max_x, x_coord + width), max(max_y, y_coord + height))

        # otherwise, return a tuple of the thresholded image along
        # with bounding box
        return (thresh, (min_x, min_y, max_x, max_y))
