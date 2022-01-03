# aps
#### APS (Automated Plant System) is a project that came out of the need to make sure indoor plants had enough water when nobody was home. The APS consists two software applications, one for a webserver and backend and another for data logging and automatic watering operations. The webserver/backend is written in python and located in the aps/site directory. The data logging and automatic watering application is written primarily in C and the source is located in the aps/csrc directory. These applications run on a raspberry Pi in the following hardware setup:
![alt text](https://github.com/jfri2/aps/blob/main/system_config.png)

#### The APS webpage currently looks like this:
![alt text](https://github.com/jfri2/aps/blob/main/webpage.png)

##### The APS currently does the following: 
- Continuously monitors and logs the following parameters: 
    - Soil Moisture (three separate sensors)
    - Temperature
    - Relative Humidity
    - Any watering events
- Runs a webserver that implements the following: 
    - Latest status on all above parameters
    - Real time video feed from two cameras
    - Buttons that allow the user to manually water any plant group
    - Buttons that act as a killswitch to stop or start all automatic watering operations
    - Button that allows the user to screenshot the current video feed and send it to email addresses provided in another file
    - Button that allows the user to download a .csv file containing all logged data
    - Automatic timelapse video generation from camera feeds
    - Button that allows the user to download a timelapse video file from the camera feeds
