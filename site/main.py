#!/usr/bin/python3
# imports
from flask import Response
from flask import Flask, url_for
from flask import render_template
from flask import request
from flask import redirect
from flask import send_file
from imutils.video import VideoStream
from functools import wraps
import threading
import argparse
import datetime
import imutils
import time
import cv2
import sys
import os
import glob
import shutil
from image_processing.motion_detector import MotionDetector
from globals import *
from emailer import *
from utils import *
from csv import *
from timelapse import *

# Globals
# TODO - Make vs_started check work
# vs_started = False
vs_started = True

# initialize the output frame and a lock used to ensure thread-safe
# exchanges of the output frames (useful when multiple browsers/tabs
# are viewing the stream)
output_frame = None
lock = threading.Lock()
# initialize a flask object
app = Flask(__name__, static_url_path="", static_folder="/share/aps/site/static")
# initialize the video stream and allow the camera sensor to
# warmup
# vs = VideoStream(usePiCamera=1).start()
vs = VideoStream(src=0).start()
time.sleep(2.0)


@app.route("/", methods=["GET", "POST"])
def index():
    # return the rendered template
    info_killswitchstatus = read_from_file(KILL_SWITCH_FILE_PATH)
    info_water1 = read_from_file(PUMP_1_FILE_PATH)
    info_water2 = read_from_file(PUMP_2_FILE_PATH)
    info_water3 = read_from_file(PUMP_3_FILE_PATH)
    info_testpumps = read_from_file(TEST_PUMPS_FILE_PATH)
    info_time1 = ""
    info_temp1 = ""
    info_hum1 = ""
    info_ss11 = ""
    info_ss12 = ""
    info_ss13 = ""
    info_p11 = ""
    info_p12 = ""
    info_p13 = ""
    lastVideoFileName = ""

    # Populate fields from latest csv file for webpage
    with open(get_csv_filename(), "rb") as f:
        try:  # catch OSError in case of a one line file
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b"\n":
                f.seek(-2, os.SEEK_CUR)
        except OSError:
            f.seek(0)
        sensor_readings = f.readline().decode()
        sensor_readings = sensor_readings.split(",")
        info_time1 = sensor_readings[0]
        info_temp1 = sensor_readings[2]
        info_hum1 = sensor_readings[3]
        info_ss11 = sensor_readings[4]
        info_ss12 = sensor_readings[5]
        info_ss13 = sensor_readings[6]
        info_p11 = sensor_readings[7]
        info_p12 = sensor_readings[8]
        info_p13 = sensor_readings[9]

    # Populate last timelapse video filename
    lastVideoFileName = os.path.basename(max(all_files_under(TIMELAPSE_VIDEO_PATH)))

    return render_template(
        "index.html",
        info_killswitchstatus=info_killswitchstatus,
        info_water1=info_water1,
        info_water2=info_water2,
        info_water3=info_water3,
        info_testpumps=info_testpumps,
        info_time1=info_time1,
        info_temp1=info_temp1,
        info_hum1=info_hum1,
        info_ss11=info_ss11,
        info_ss12=info_ss12,
        info_ss13=info_ss13,
        info_p11=info_p11,
        info_p12=info_p12,
        info_p13=info_p12,
        lastVideoFileName=lastVideoFileName,
    )


@app.route("/GEN_TIMELAPSE")
def gen_timelapse():
    t = threading.Thread(target=exec_gen_timelapse)
    t.daemon = True
    t.start()

    return index()


@app.route("/DOWNLOAD_TIMELAPSE")
def download_timelapse():
    timelapse_filename = max(all_files_under(TIMELAPSE_VIDEO_PATH))
    print(timelapse_filename)
    return send_file(timelapse_filename, as_attachment=True)


def detect_motion(frameCount):
    # grab global references to the video stream, output frame, and
    # lock variables
    global vs, output_frame, lock
    # initialize the motion detector and the total number of frames
    # read thus far
    md = MotionDetector(accum_weight=0.1)
    total = 0

    # For timelapse stuff
    timelapseDelay = 60 * 5  # Seconds
    lastUpdatedTime = 0

    # loop over frames from the video stream
    while True:
        vs_started = True
        # read the next frame from the video stream, resize it,
        # convert the frame to grayscale, and blur it
        frame = vs.read()
        frame = imutils.resize(frame, width=800)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)
        # grab the current timestamp and draw it on the frame
        timestamp = datetime.datetime.now()
        cv2.putText(
            frame,
            timestamp.strftime("%a %d %b %Y %H:%M:%S"),
            (10, frame.shape[0] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 0),
            4,
        )
        cv2.putText(
            frame,
            timestamp.strftime("%a %d %b %Y %H:%M:%S"),
            (10, frame.shape[0] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )
        motionFrame = frame
        # if the total number of frames has reached a sufficient
        # number to construct a reasonable background model, then
        # continue to process the frame
        if total > frameCount:
            # detect motion in the image
            motion = md.detect(gray)

            # check to see if motion was found in the frame
            if motion is not None:
                # unpack the tuple and draw the box surrounding the
                # "motion area" on the output frame
                (thresh, (min_x, min_y, max_x, max_y)) = motion
                cv2.rectangle(motionFrame, (min_x, min_y), (max_x, max_y), (0, 0, 0), 3)
                cv2.rectangle(motionFrame, (min_x, min_y), (max_x, max_y), (0, 0, 255), 2)

        # update the background model and increment the total number
        # of frames read thus far
        md.update(gray)
        total += 1
        # acquire the lock, set the output frame, and release the
        # lock
        with lock:
            output_frame = motionFrame.copy()
            # Save frome to timelapse
            if time.time() > (lastUpdatedTime + timelapseDelay):
                save_frame(frame)
                lastUpdatedTime = time.time()


@app.route("/SCREENSHOT")
def screenshot():
    path = "/tmp/screenshots"
    # Create a screenshots directory if not exist in /tmp/
    if not os.path.exists(path):
        os.mkdir(path)
    if vs_started:
        content = "Hilo! John or Rachel just took a screenshot!"

        # Grab the current screen and save as a PNG with current timestamp in /tmp/
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        screenshot = vs.read()
        screenshot_name = "gemma-" + timestamp + ".png"
        cv2.imwrite(os.path.join(path, screenshot_name), screenshot)
    else:
        content = "Video stream is not started, unable to take screenshot"

    sender = Emailer()
    recipient = emails["ToAddress1"]
    subject = "GemmaCam Screenshot"
    sender.sendmail_attachment(
        recipient=recipient,
        subject=subject,
        content=content,
        filename=os.path.join(path, screenshot_name),
    )

    recipient = emails["ToAddress2"]
    sender.sendmail_attachment(
        recipient=recipient,
        subject=subject,
        content=content,
        filename=os.path.join(path, screenshot_name),
    )
    return index()


def generate():
    # grab global references to the output frame and lock variables
    global output_frame, lock
    # loop over frames from the output stream
    while True:
        # wait until the lock is acquired
        with lock:
            # check if the output frame is available, otherwise skip
            # the iteration of the loop
            if output_frame is None:
                continue
            # encode the frame in JPEG format
            (flag, encodedImage) = cv2.imencode(".jpg", output_frame)
            # ensure the frame was successfully encoded
            if not flag:
                continue
        # yield the output frame in the byte format
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + bytearray(encodedImage) + b"\r\n"
        )


@app.route("/video_feed")
def video_feed():
    # return the response generated along with the specific media
    # type (mime type)
    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/getCSV")
def getCSV():
    sensor_data_filename = os.path.basename(get_csv_filename())
    with open(get_csv_filename()) as csv_fp:
        csv = csv_fp.read()
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=" + sensor_data_filename},
    )


@app.route("/KILLSWITCHON")
def buttonKILLSWITCHON():
    write_to_file(KILL_SWITCH_FILE_PATH, "1")
    return index()


@app.route("/KILLSWITCHOFF")
def buttonKILLSWITCHOFF():
    write_to_file(KILL_SWITCH_FILE_PATH, "0")
    return index()


@app.route("/TESTPUMPS")
def buttonTESTPUMPS():
    write_to_file(TEST_PUMPS_FILE_PATH, "1")
    return index()


@app.route("/WATER_1")
def buttonWATER1():
    write_to_file(PUMP_1_FILE_PATH, "1")
    return index()


@app.route("/WATER_2")
def buttonWATER2():
    write_to_file(PUMP_2_FILE_PATH, "1")
    return index()


@app.route("/WATER_3")
def buttonWATER3():
    write_to_file(PUMP_3_FILE_PATH, "1")
    return index()


# check to see if this is the main thread of execution
if __name__ == "__main__":
    # start a thread that will perform motion detection
    t = threading.Thread(target=detect_motion, args=(32,))
    t.daemon = True
    t.start()

    # start the flask app
    app.run(host="0.0.0.0", debug=False, port=5000, threaded=True, use_reloader=False)

# release the video stream pointer
vs.stop()
