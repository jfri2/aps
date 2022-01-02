# timelapse
import datetime
import time
import os
import cv2
import shutil
import threading
import traceback
from pathlib import Path


class Timelapse:
    def __init__(self):
        self.timelapse_generation_in_process = False
        self.TIMELAPSE_IMAGE_PATH = "/share/aps/timelapse/images/"
        self.TIMELAPSE_VIDEO_PATH = "/share/aps/timelapse/videos/"
        self.latest_timelapse_filename = "No timelapse video generated yet"

    def start_timelapse_video_generation(self):
        # Start video generation
        gen_timelapse_thread = threading.Thread(
            target=self._generate_timelapse,
            kwargs={"debug_print": True},
        )
        gen_timelapse_thread.daemon = True
        gen_timelapse_thread.start()

    def save_frame(self, frame):
        # Only save images between 5:00am and 11:00pm local time
        current_time = datetime.datetime.now()
        # override limit on time to save frames
        override = True
        if (
            (int(current_time.hour) < 23)
            and ((int(current_time.hour) >= 5))
            or override
        ):
            # Save images
            existing_files = os.listdir(self.TIMELAPSE_IMAGE_PATH)
            if len(existing_files) == 0:
                image_number = 0
            else:
                image_number = len(existing_files)
            filename = (
                self.TIMELAPSE_IMAGE_PATH + "{:010d}".format(image_number) + ".jpg"
            )
            cv2.imwrite(filename, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
            # print('File written: {}'.format(filename))
            image_number = image_number + 1
        else:
            pass
        return

    def _order_frames(self):
        # Check files to see if they are in sequential order, rename any that are not in order
        file_list = []
        for filename in os.listdir(self.TIMELAPSE_IMAGE_PATH):
            if filename.endswith(".jpg"):
                file_list.append(os.path.join(self.TIMELAPSE_IMAGE_PATH, filename))
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
            new_filename = (
                self.TIMELAPSE_IMAGE_PATH + "{:010d}".format(filename) + ".jpg"
            )
            filename_to_copy = (
                self.TIMELAPSE_IMAGE_PATH + "{:010d}".format(filename + 1) + ".jpg"
            )
            shutil.copyfile(filename_to_copy, new_filename)
            print("Missing file detected. Created new file {}".format(filename_to_copy))

    def _generate_timelapse(self, debug_print=True):
        return
        old_timelapse_video_filename = ""
        while True:
            # Check if timelapse is currently being generated
            if self.timelapse_generation_in_process == False:
                self.timelapse_generation_in_process = True

                # Order frames and fix gaps
                self._order_frames()

                print("Timelapse video generation started")
                num_frames = len(os.listdir(self.TIMELAPSE_IMAGE_PATH))
                print(
                    "{0:d} Frames to process, expected to take {1:.2f} seconds".format(
                        num_frames, num_frames * 0.10723
                    )
                )

                start_time = time.time()
                timestamp = datetime.datetime.now()
                time_string = timestamp.strftime("%Y-%m-%d_%H-%M-%S")
                temp_timelapse_filename = time_string + ".mp4"
                fps = 20
                ffmpeg_command = (
                    "ffmpeg -f image2 -r {} -i ".format(fps)
                    + self.TIMELAPSE_IMAGE_PATH
                    + "%10d.jpg -vcodec libx264 -crf 18 -pix_fmt yuv420p -y "
                    + self.TIMELAPSE_VIDEO_PATH
                    + temp_timelapse_filename
                )
                if debug_print:
                    ffmpeg_command = ffmpeg_command + " > /dev/null 2>&1"
                os.system(ffmpeg_command)
                generationTime = time.time() - start_time
                print(
                    "Timelapse video generation complete, took {0:.2f} seconds".format(
                        generationTime
                    )
                )
                old_timelapse_video_filename = self.latest_timelapse_filename
                self.timelapse_generation_in_process = False
                self.latest_timelapse_filename = temp_timelapse_filename

                # Remove old timelapse file
                old_timelapse_video_full_path = (
                    self.TIMELAPSE_VIDEO_PATH + old_timelapse_video_filename
                )
                if os.path.exists(old_timelapse_video_full_path):
                    try:
                        os.remove(old_timelapse_video_full_path)
                        print("Removed {}".format(old_timelapse_video_filename))
                    except Exception:
                        traceback.print_exc()
                else:
                    print("Cannot delete file as it does not exist")

                # Wait 30 minutes between generating timelapse videos
                time.sleep(60 * 30)
            else:
                pass
