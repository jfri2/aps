from imutils.video import VideoStream
import threading
import time
import datetime
import cv2
import collections
from timelapse import Timelapse
from utils import *

class ApsVideo:
    def __init__(self):
        self.vs_started = True
        self.frame_lock = threading.Lock()
        self.frame_queue = Queue(max_size=10)
        
        # Init video stream, allow camera to warmup
        self.vs = VideoStream(src=0).start()
        time.sleep(2.0)
        
        # Init timelapse object
        self.timelapse = Timelapse()
        
        # Start thread to generate frames
        generate_frame_thread = threading.Thread(target=self.generate_frame)
        generate_frame_thread.daemon = True
        generate_frame_thread.start()
        
        
    def generate_frame(self):
        timelapseDelay = 60 * 2  # Seconds
        lastUpdatedTime = 0
        frame = []
        frame_updated = False
    
        while True:
            # Delay to limit framerate
            time.sleep(0.05)
            with self.frame_lock:
                # Get frame from camera
                frame = self.vs.read()
                
                # Write timestamp on top of frame
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
                
                # Insert frame into frame queue
                self.frame_queue.enqueue(frame)
                frame_updated = True                
                # print('Enqueued frame, current count is {} frames'.format(len(self.frame_queue._queue)))
            if frame_updated:                
                # Save frame for timelapse
                if time.time() > (lastUpdatedTime + timelapseDelay):
                    self.timelapse.save_frame(frame)
                    lastUpdatedTime = time.time()
                
    def encode_frame(self):
        frame_updated = False
        last_encoded_image = None
        while True:
            time.sleep(0.05)
            with self.frame_lock:
                try:
                    frame = self.frame_queue.dequeue()
                    frame_updated = True
                    # print('Dequeued frame, current count is {} frames'.format(len(self.frame_queue._queue)))
                except: 
                    frame_updated = False
                    print('No data in frame_queue')
            if frame_updated:
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
                # encode the frame in JPEG format
                (flag, encoded_image) = cv2.imencode(".jpg", frame, encode_param)

                # ensure the frame was successfully encoded
                if not flag:
                    continue
                # Copy new encoded image to last encoded image
                last_encoded_image = encoded_image
                
            # yield the output frame in the byte format
            if last_encoded_image is not None:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + bytearray(last_encoded_image) + b"\r\n"
                )
            else:
                continue
            
    def stop(self):
        # Release video stream pointer
        self.vs.stop()