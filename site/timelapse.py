# timelapse
import datetime
import time
import os
import cv2
import shutil
from site.globals import *

timelapse_generation_in_process = False


def save_frame(frame):
    # Only save images between 5:00am and 11:00pm local time
    current_time = datetime.datetime.now()
    # override
    override = True
    if (int(current_time.hour) < 23) and ((int(current_time.hour) >= 5)) or override:
        # Save images
        existing_files = os.listdir(TIMELAPSE_IMAGE_PATH)
        if len(existing_files) == 0:
            image_number = 0
        else:
            image_number = len(existing_files)
        filename = TIMELAPSE_IMAGE_PATH + "{:010d}".format(image_number) + ".jpg"
        cv2.imwrite(filename, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
        # print('File written: {}'.format(filename))
        image_number = image_number + 1
    else:
        pass
    return


def exec_gen_timelapse():
    if timelapse_generation_in_process == False:
        timelapse_generation_in_process = True

        # Check files to see if they are in sequential order, rename any that are not in order
        file_list = []
        for filename in os.listdir(TIMELAPSE_IMAGE_PATH):
            if filename.endswith(".jpg"):
                file_list.append(os.path.join(TIMELAPSE_IMAGE_PATH, filename))
            else:
                continue
        file_list.sort()

        missing_files = []
        last_filename = "-1"
        for file in file_list:
            filename = Path(os.path.basename(file)).stem
            if int(filename) - 1 != int(last_filename):
                missing_files.append(int(filename) - 1)
            last_filename = filename

        # Copy filename + 1 to filename and rename
        for filename in missing_files:
            new_filename = TIMELAPSE_IMAGE_PATH + "{:010d}".format(filename) + ".jpg"
            filename_to_copy = TIMELAPSE_IMAGE_PATH + "{:010d}".format(filename + 1) + ".jpg"
            shutil.copyfile(filename_to_copy, new_filename)
            print("Missing file detected. Created new file {}".format(filename_to_copy))

        print("Timelapse video generation started")

        num_frames = len(os.listdir(TIMELAPSE_IMAGE_PATH))
        print(
            "{0:d} Frames to process, expected to take {1:.2f} seconds".format(
                num_frames, num_frames * 0.05
            )
        )

        start_time = time.time()
        timestamp = datetime.datetime.now()
        fps = 20
        ffmpeg_command = (
            "ffmpeg -f image2 -r {} -i ".format(fps)
            + TIMELAPSE_IMAGE_PATH
            + "%10d.jpg -vcodec libx264 -crf 18 -pix_fmt yuv420p -y "
            + TIMELAPSE_VIDEO_PATH
            + timestamp.strftime("%Y-%m-%d_%H-%M-%S")
            + ".mp4"
        )
        # ffmpeg_command = ffmpeg_command + " > /dev/null 2>&1"
        os.system(ffmpeg_command)
        generationTime = time.time() - start_time
        print(
            "Timelapse video generation complete, took {0:.2f} seconds".format(
                generationTime
            )
        )
        timelapse_generation_in_process = False
    else:
        pass
