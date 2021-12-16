import RPi.GPIO as GPIO
import time
import threading


class Motor:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        self.DIR = 5
        self.M0 = 6
        self.M1 = 13
        self.nSLEEP = 19
        self.DECAY = 26
        self.STEP = 12
        self.nFAULT = 16
        
        # Init GPIOs
        GPIO.setup(self.DIR, GPIO.OUT)
        GPIO.setup(self.M0, GPIO.OUT)
        GPIO.setup(self.M1, GPIO.OUT)
        GPIO.setup(self.nSLEEP, GPIO.OUT)
        GPIO.setup(self.DECAY, GPIO.OUT)
        GPIO.setup(self.STEP, GPIO.OUT)
        GPIO.setup(self.nFAULT, GPIO.IN)
        
        # Setup PWM
        self.SWITCHING_RATE = 1000
        self.pwm = GPIO.PWM(self.STEP, self.SWITCHING_RATE)   

        # Exit out of sleep mode
        GPIO.output(self.nSLEEP, GPIO.HIGH)

        # Setup microstepping mode with M0 and M1 (1/16 microstepping)
        GPIO.output(self.M0, GPIO.HIGH)
        GPIO.output(self.M1, GPIO.HIGH)
        
    def rotate_15_cw(self):
        self.rotate_cw(15)
        
    def rotate_15_ccw(self):
        self.rotate_ccw(15)
        
    def rotate_cw(self, degrees):
        GPIO.output(self.DIR, GPIO.LOW)
        self.__step_degrees(degrees)
        
    def rotate_ccw(self, degrees):
        GPIO.output(self.DIR, GPIO.HIGH)
        self.__step_degrees(degrees)
        
    def __step_degrees(self, degrees):
        '''
        This motor is driven in 1/16 microstepping mode meaning every "step"
        results in a 1.8 / 16 = 0.1125 degree rotation
        
        The motor steps at a 1 kHz rate, so rotating 1 degree takes:
        8.89 msec
        '''
        
        DUTY_CYCLE = 50 # Percent
        ONE_DEG_TIME = (0.00889 + 0.0011) # Seconds    
        pwm_en_time = time.time()
        pwm_stop_time = pwm_en_time + (ONE_DEG_TIME * degrees)
        self.pwm.start(DUTY_CYCLE)
        while time.time() <= pwm_stop_time:
            pass  
            
        self.pwm.stop()
    
