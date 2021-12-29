#!/usr/bin/python3
# imports
from image_processing.motion_detector import MotionDetector
from imutils.video import VideoStream
from flask import Response
from flask import Flask, url_for
from flask import render_template
from flask import request
from flask import redirect
from flask import send_file
from functools import wraps
import threading
import argparse
import datetime
import imutils
import time
import cv2
import sys
import smtplib, ssl
import json
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from email.utils import *
import os
import glob
from pathlib import Path
import shutil

# Globals
# TODO - Make vs_started check work
# vs_started = False
vs_started = True

# CSV stuff
def all_files_under(path):
    for cur_path, dirnames, filenames in os.walk(path):
        for filename in filenames:
            yield os.path.join(cur_path, filename)


def get_csv_filename():
    return max(all_files_under("/share/aps/csrc/data/"))


# Emailer
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
with open("/share/aps/CamMonitor_Debug/data.json") as jsonfile:
    emails = json.load(jsonfile)

killswitchFilePath = "/share/aps/csrc/pumps/killswitch.txt"
testpumpsFilePath = "/share/aps/csrc/pumps/testpumps.txt"
pump1FilePath = "/share/aps/csrc/pumps/pump1.txt"
pump2FilePath = "/share/aps/csrc/pumps/pump2.txt"
pump3FilePath = "/share/aps/csrc/pumps/pump3.txt"


def writeToFile(filepath, str):
    f = open(filepath, "w")
    f.write(str)
    f.close()


def readFromFile(filepath):
    f = open(filepath, "r")
    text = f.read()
    f.close()
    return text


class Emailer:
    def sendmail(self, recipient, subject, content):

        # Create Headers
        headers = [
            "From: " + emails["FromAddress"],
            "Subject: " + subject,
            "To: " + recipient,
            "MIME-Version: 1.0",
            "Content-Type: text/html",
        ]
        headers = "\r\n".join(headers)

        # Connect to Gmail Server
        session = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        session.ehlo()
        session.starttls()
        session.ehlo()

        # Login to Gmail
        session.login(emails["FromAddress"], emails["FromPassword"])

        # Send Email & Exit
        session.sendmail(
            emails["FromAddress"], recipient, headers + "\r\n\r\n" + content
        )
        session.quit

    def sendmail_attachment(self, recipient, subject, content, filename):
        msg = MIMEMultipart()
        msg["From"] = emails["FromAddress"]
        msg["To"] = recipient
        msg["Date"] = formatdate(localtime=True)
        msg["Subject"] = subject
        msg.attach(MIMEText(content, "plain"))

        # Open file in binary mode
        with open(filename, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        # Encode attachment in ASCII
        encoders.encode_base64(part)

        # Add header as key/value pair to attachment part
        part.add_header("Content-Disposition", "attachment", filename=filename)

        # Add attachment to msg and convert msg to string
        msg.attach(part)
        text = msg.as_string()

        # Log into server and send email
        email_context = ssl.create_default_context()

        # Connect to Gmail Server
        session = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        session.ehlo()
        session.starttls(context=email_context)
        session.ehlo()

        # Login to Gmail
        session.login(emails["FromAddress"], emails["FromPassword"])

        # Send Email & Exit
        session.sendmail(emails["FromAddress"], recipient, text)
        session.quit


# initialize the output frame and a lock used to ensure thread-safe
# exchanges of the output frames (useful when multiple browsers/tabs
# are viewing the stream)
outputFrame = None
lock = threading.Lock()
# initialize a flask object
app = Flask(
    __name__, static_url_path="", static_folder="/share/aps/CamMonitor_Debug/static"
)
# initialize the video stream and allow the camera sensor to
# warmup
# vs = VideoStream(usePiCamera=1).start()
vs = VideoStream(src=0).start()
time.sleep(2.0)

# Timelapse stuff
timelapseImagePath = "/share/aps/timelapse/images/"
timelapseVideoPath = "/share/aps/timelapse/videos/"


@app.route("/", methods=["GET", "POST"])
def index():
    # return the rendered template
    info_killswitchstatus = readFromFile(killswitchFilePath)
    info_water1 = readFromFile(pump1FilePath)
    info_water2 = readFromFile(pump2FilePath)
    info_water3 = readFromFile(pump3FilePath)
    info_testpumps = readFromFile(testpumpsFilePath)
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
    lastVideoFileName = os.path.basename(max(all_files_under(timelapseVideoPath)))

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


def save_frame(frame):
    # Only save images between 5:00am and 11:00pm local time
    currentTime = datetime.datetime.now()
    # override
    override = True
    if ((int(currentTime.hour) < 23) and ((int(currentTime.hour) >= 5)) or override):
        # Save images
        existingFiles = os.listdir(timelapseImagePath)
        if len(existingFiles) == 0:
            imageNumber = 0
        else:
            imageNumber = len(existingFiles)
        filename = timelapseImagePath + "{:010d}".format(imageNumber) + ".jpg"
        cv2.imwrite(filename, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
        # print('File written: {}'.format(filename))
        imageNumber = imageNumber + 1
    else:
        pass
    return


timelapseGenerationInProgress = False


def exec_gen_timelapse():
    timelapseGenerationInProgress = True
    
    # Check files to see if they are in sequential order, rename any that are not in order
    filelist = []
    for filename in os.listdir(timelapseImagePath):
        if filename.endswith('.jpg'):
            filelist.append(os.path.join(timelapseImagePath, filename))
        else:
            continue
    filelist.sort()
    
    missingFiles = []
    lastFilename = '-1'
    for file in filelist:
        filename = Path(os.path.basename(file)).stem
        if (int(filename) - 1 != int(lastFilename)):
            missingFiles.append(int(filename) - 1)
        lastFilename = filename
    
    # Copy filename + 1 to filename and rename
    for filename in missingFiles:
        newFilename = timelapseImagePath + "{:010d}".format(filename) + ".jpg"
        filenameToCopy = timelapseImagePath + "{:010d}".format(filename + 1) + ".jpg"
        shutil.copyfile(filenameToCopy, newFilename)
        print('Missing file detected. Created new file {}'.format(filenameToCopy))
    
    print("Timelapse video generation started")

    numFrames = len(os.listdir(timelapseImagePath))
    print(
        "{0:d} Frames to process, expected to take {1:.2f} seconds".format(
            numFrames, numFrames * 0.05
        )
    )

    startTime = time.time()
    timestamp = datetime.datetime.now()
    fps = 15
    ffmpeg_command = (
        "ffmpeg -r {} -i ".format(fps)
        + timelapseImagePath
        + "%10d.jpg -vcodec mpeg4 -y"
        + timelapseVideoPath
        + timestamp.strftime("%Y-%m-%d_%H-%M-%S")
        + ".mp4"
    )
    # ffmpeg_command = ffmpeg_command + " > /dev/null 2>&1"
    os.system(ffmpeg_command)
    generationTime = time.time() - startTime
    print(
        "Timelapse video generation complete, took {0:.2f} seconds".format(
            generationTime
        )
    )
    timelapseGenerationInProgress = False
    return


@app.route("/GEN_TIMELAPSE")
def gen_timelapse():
    if not timelapseGenerationInProgress:
        t = threading.Thread(target=exec_gen_timelapse)
        t.daemon = True
        t.start()
    else:
        pass

    return index()


@app.route("/DOWNLOAD_TIMELAPSE")
def download_timelapse():
    timelapse_filename = max(all_files_under(timelapseVideoPath))
    print(timelapse_filename)
    return send_file(timelapse_filename, as_attachment=True)


def detect_motion(frameCount):
    # grab global references to the video stream, output frame, and
    # lock variables
    global vs, outputFrame, lock
    # initialize the motion detector and the total number of frames
    # read thus far
    md = MotionDetector(accumWeight=0.1)
    total = 0

    # For timelapse stuff
    timelapseDelay = 60  # Seconds
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
                (thresh, (minX, minY, maxX, maxY)) = motion
                cv2.rectangle(motionFrame, (minX, minY), (maxX, maxY), (0, 0, 0), 3)
                cv2.rectangle(motionFrame, (minX, minY), (maxX, maxY), (0, 0, 255), 2)

        # update the background model and increment the total number
        # of frames read thus far
        md.update(gray)
        total += 1
        # acquire the lock, set the output frame, and release the
        # lock
        with lock:
            outputFrame = motionFrame.copy()
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
    global outputFrame, lock
    # loop over frames from the output stream
    while True:
        # wait until the lock is acquired
        with lock:
            # check if the output frame is available, otherwise skip
            # the iteration of the loop
            if outputFrame is None:
                continue
            # encode the frame in JPEG format
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
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
    writeToFile(killswitchFilePath, "1")
    return index()


@app.route("/KILLSWITCHOFF")
def buttonKILLSWITCHOFF():
    writeToFile(killswitchFilePath, "0")
    return index()


@app.route("/TESTPUMPS")
def buttonTESTPUMPS():
    writeToFile(testpumpsFilePath, "1")
    return index()


@app.route("/WATER_1")
def buttonWATER1():
    writeToFile(pump1FilePath, "1")
    return index()


@app.route("/WATER_2")
def buttonWATER2():
    writeToFile(pump2FilePath, "1")
    return index()


@app.route("/WATER_3")
def buttonWATER3():
    writeToFile(pump3FilePath, "1")
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
