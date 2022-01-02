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
from globals import *
from emailer import Emailer
from utils import *
from csv import *
from timelapse import *
from aps_video import *

# Start video stream
aps_video = ApsVideo()

# initialize a flask object
app = Flask(__name__, static_url_path="", static_folder="/share/aps/site/static")

# init and start timelapse video generation
timelapse = Timelapse()
timelapse.start_timelapse_video_generation()

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
    lastVideoFileName = timelapse.latest_timelapse_filename

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


@app.route("/DOWNLOAD_TIMELAPSE")
def download_timelapse():
    timelapse_filename = timelapse.TIMELAPSE_VIDEO_PATH + timelapse.latest_timelapse_filename
    print(timelapse_filename)
    return send_file(timelapse_filename, as_attachment=True)


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

    emailer = Emailer()
    recipient = emailer.emails["ToAddress1"]
    subject = "GemmaCam Screenshot"
    emailer.sendmail_attachment(
        recipient=recipient,
        subject=subject,
        content=content,
        filename=os.path.join(path, screenshot_name),
    )

    recipient = emailer.emails["ToAddress2"]
    emailer.sendmail_attachment(
        recipient=recipient,
        subject=subject,
        content=content,
        filename=os.path.join(path, screenshot_name),
    )
    return index()


@app.route("/video_feed")
def video_feed():
    return Response(aps_video.encode_frame(), mimetype="multipart/x-mixed-replace; boundary=frame")


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
    # start the flask app
    app.run(host="0.0.0.0", debug=False, port=5000, threaded=True, use_reloader=False)

# release the video stream pointer
aps_video.stop()
