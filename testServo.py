from adafruit_servokit import ServoKit
import time
kit = ServoKit(channels=16)

kit.servo[1].angle = 120



