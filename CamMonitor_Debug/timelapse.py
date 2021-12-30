# timelapse
import datetime, time, os, cv2
from globals import *

timelapseGenerationInProgress = False

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
    fps = 20
    ffmpeg_command = (
        "ffmpeg -f image2 -r {} -i ".format(fps)
        + timelapseImagePath
        + "%10d.jpg -vcodec libx264 -crf 18 -pix_fmt yuv420p -y "
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