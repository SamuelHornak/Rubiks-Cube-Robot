# Import I2C pins.
import board
import busio

# Needed for file I/O functions
import os

from time import sleep

# Library to control the PCA9685 PWM board that drives the servos
from adafruit_pca9685 import PCA9685

# Button detection class
from rubik_buttons import RubikButtons, UP_BUTTON, DOWN_BUTTON, ENTER_BUTTON


# Set this to 0 to disable debug logging, 1 to enable.
DEBUG = 0


# Delay to allow servos to move (seconds)
# This time is probably conservative but I would rather be a litle slow
# than have errors caused by moving the servos too fast.
SERVO_MOVE_DELAY = 1.0

# Current servo positions
# These are used to optimize the servo move functions by keeping track
# of the current servo positions. This avoids having to move the servos
# back to a "home" position between movements. It does however make
# the servo logic more cpmplex.
# The actual values aren't important, they just need to be unique.
#
# Turn servos
T_POS_M90    = 0    # Counterclockwise 90 degree position
T_POS_0      = 1    # Center (horizontal) position
T_POS_P90    = 2    # Clockwise 90 degree position
# Grip servos
G_POS_OPEN   = 0    # Grip fully open position
G_POS_LOAD   = 1    # Grip in the load cube position
G_POS_CLOSED = 2    # Grip closed position


# Rubik solver servo class
#
class RubikServo(object):
    def __init__(self, button_q):
        # Save the button queue class reference
        self.btn_q = button_q

        # Servo calibration file name
        self.cal_file = "servo_tune.txt"

        # I2C bus used to communicate with the PWM hardware
        i2c = busio.I2C(board.SCL, board.SDA)

        # PWM driver
        self.pca = PCA9685(i2c)

        try:
            f=open(self.cal_file, 'r')
            # Read the saved calibration values
            self.pwm_freq = self.read_tune_val(f)
            self.pwm_min = self.read_tune_val(f)
            self.pwm_max = self.read_tune_val(f)
            self.rg = self.read_tune_val(f)
            self.rt = self.read_tune_val(f)
            self.lg = self.read_tune_val(f)
            self.lt = self.read_tune_val(f)
            self.rt_cal_m90 = self.read_tune_val(f)
            self.rt_cal_0   = self.read_tune_val(f)
            self.rt_cal_90  = self.read_tune_val(f)
            self.rg_cal_close = self.read_tune_val(f)
            self.rg_cal_open = self.read_tune_val(f)
            self.rg_cal_load = self.read_tune_val(f)
            self.lt_cal_m90 = self.read_tune_val(f)
            self.lt_cal_0 = self.read_tune_val(f)
            self.lt_cal_90 = self.read_tune_val(f)
            self.lg_cal_close = self.read_tune_val(f)
            self.lg_cal_open = self.read_tune_val(f)
            self.lg_cal_load = self.read_tune_val(f)

            f.close() 
        except:
            f.close() 
            print("Calibration file error")
            raise
        else:
            print("Calibration file found")

        # Set the frequency for all PWM channels
        self.pca.frequency = self.pwm_freq

        # Set the initial PWM value for all ports
        # The shift left is needed to put a 12 bit value into a
        # 16 bit register
        self.set_pwm_value(self.rt, self.rt_cal_0)
        self.rt_pos = T_POS_0
        self.set_pwm_value(self.rg, self.rg_cal_open)
        self.rg_pos = G_POS_OPEN
        self.set_pwm_value(self.lt, self.lt_cal_0)
        self.lt_pos = T_POS_0
        self.set_pwm_value(self.lg, self.lg_cal_open)
        self.lg_pos = G_POS_OPEN


    def read_tune_val(self, fh):
        tune_line  = fh.readline()
        tune_spilt = tune_line.split(" ")
        val = int(tune_spilt[0])
        return val


    def set_pwm_value(self, port, pwm):
        # If the user pressed a button then abort
        if (self.btn_q.qsize() > 0):
            # Discard the button
            self.btn_q.get(False, 0)
            raise KeyboardInterrupt

        self.pca.channels[port].duty_cycle = pwm << 4



    # Set the Right Turn servo to the counterclockwise position
    def set_right_turn_m90(self):
        if (DEBUG == 1):
            print("set_right_turn_m90")
        if (self.rt_pos != T_POS_M90):
            self.set_pwm_value(self.rt, self.rt_cal_m90)
            self.rt_pos = T_POS_M90
            sleep(SERVO_MOVE_DELAY)


    # Set the Right Turn servo to the center (horizontal) position
    #
    def set_right_turn_0(self):
        if (DEBUG == 1):
            print("set_right_turn_0")
        if (self.rt_pos != T_POS_0):
            self.set_pwm_value(self.rt, self.rt_cal_0)
            self.rt_pos = T_POS_0
            sleep(SERVO_MOVE_DELAY)


    # Set the Right Turn servo to the clockwise position
    #
    def set_right_turn_90(self):
        if (DEBUG == 1):
            print("set_right_turn_90")
        if (self.rt_pos != T_POS_P90):
            self.set_pwm_value(self.rt, self.rt_cal_90)
            self.rt_pos = T_POS_P90
            sleep(SERVO_MOVE_DELAY)


    # Set the Right Grip server to the open position
    #
    def set_right_grip_open(self):
        if (DEBUG == 1):
            print("set_right_grip_open")
        if (self.rg_pos != G_POS_OPEN):
            if (self.rg_pos == G_POS_CLOSED):
                # Open just a little first to avoid messing up the cube
                self.set_pwm_value(self.rg, \
                             int((self.rg_cal_close + self.rg_cal_load)/2))
                sleep(SERVO_MOVE_DELAY / 4)
            self.set_pwm_value(self.rg, self.rg_cal_open)
            self.rg_pos = G_POS_OPEN
            sleep(SERVO_MOVE_DELAY)


    # Set the Right Grip server to the cube load position
    #
    def set_right_grip_load(self):
        if (DEBUG == 1):
            print("set_right_grip_load")
        if (self.rg_pos != G_POS_LOAD):
            self.set_pwm_value(self.rg, self.rg_cal_load)
            self.rg_pos = G_POS_LOAD
            sleep(SERVO_MOVE_DELAY)


    # Set the Right Grip server to the closed position
    #
    def set_right_grip_closed(self):
        if (DEBUG == 1):
            print("set_right_grip_closed")
        if (self.rg_pos != G_POS_CLOSED):
            self.set_pwm_value(self.rg, self.rg_cal_close)
            self.rg_pos = G_POS_CLOSED
            sleep(SERVO_MOVE_DELAY)


    # Set the Left Turn servo to the counterclockwise position
    #
    def set_left_turn_m90(self):
        if (DEBUG == 1):
            print("set_left_turn_m90")
        if (self.lt_pos != T_POS_M90):
            self.set_pwm_value(self.lt, self.lt_cal_m90)
            self.lt_pos = T_POS_M90
            sleep(SERVO_MOVE_DELAY)


    # Set the Left Turn servo to the center (horizontal) position
    #
    def set_left_turn_0(self):
        if (DEBUG == 1):
            print("set_left_turn_0")
        if (self.lt_pos != T_POS_0):
            self.set_pwm_value(self.lt, self.lt_cal_0)
            self.lt_pos = T_POS_0
            sleep(SERVO_MOVE_DELAY)


    # Set the Left Turn servo to the clockwise position
    #
    def set_left_turn_90(self):
        if (DEBUG == 1):
            print("set_left_turn_90")
        if (self.lt_pos != T_POS_P90):
            self.set_pwm_value(self.lt, self.lt_cal_90)
            self.lt_pos = T_POS_P90
            sleep(SERVO_MOVE_DELAY)


    # Set the Left Grip server to the open position
    #
    def set_left_grip_open(self):
        if (DEBUG == 1):
            print("set_left_grip_open")
        if (self.lg_pos != G_POS_OPEN):
            if (self.lg_pos == G_POS_CLOSED):
                # Open just a little first to avoid messing up the cube
                self.set_pwm_value(self.lg, \
                             int((self.lg_cal_close + self.lg_cal_load)/2))
                sleep(SERVO_MOVE_DELAY / 4)
            self.set_pwm_value(self.lg, self.lg_cal_open)
            self.lg_pos = G_POS_OPEN
            sleep(SERVO_MOVE_DELAY)


    # Set the Left Grip server to the cube load position
    #
    def set_left_grip_load(self):
        if (DEBUG == 1):
            print("set_left_grip_load")
        if (self.lg_pos != G_POS_LOAD):
            self.set_pwm_value(self.lg, self.lg_cal_load)
            self.lg_pos = G_POS_LOAD
            sleep(SERVO_MOVE_DELAY)


    # Set the Left Grip server to the closed position
    #
    def set_left_grip_closed(self):
        if (DEBUG == 1):
            print("set_left_grip_closed")
        if (self.lg_pos != G_POS_CLOSED):
            self.set_pwm_value(self.lg, self.lg_cal_close)
            self.lg_pos = G_POS_CLOSED
            sleep(SERVO_MOVE_DELAY)


    def cube_load(self, btn_q):
        if(DEBUG == 1):
            print("cube_load")
        # Make sure the turn servos are horizontal
        self.set_right_turn_0()
        self.set_left_turn_0()
        # Put the grippers into the load cube position
        self.set_pwm_value(self.rg, self.rg_cal_load)
        self.rg_pos = G_POS_LOAD
        self.set_pwm_value(self.lg, self.lg_cal_load)
        self.lg_pos = G_POS_LOAD
        sleep(SERVO_MOVE_DELAY)

        while 1:
            # Wait for a button event
            #button_press = btn_q.get()
            button_press = ENTER_BUTTON
            if (button_press == ENTER_BUTTON):
                # Close the grippers
                self.set_pwm_value(self.rg, self.rg_cal_close)
                self.rg_pos = G_POS_CLOSED
                self.set_pwm_value(self.lg, self.lg_cal_close)
                self.lg_pos = G_POS_CLOSED
                sleep(SERVO_MOVE_DELAY)
                break


    # Open both grippers so the cube can be removed
    #
    def cube_release(self):
        if(DEBUG == 1):
            print("cube_release")
        if (self.rt_pos != T_POS_0):
            self.set_right_grip_open()
            self.set_right_turn_0()
            self.set_right_grip_closed()
        if (self.lt_pos != T_POS_0):
            self.set_left_grip_open()
            self.set_left_turn_0()
            self.set_left_grip_closed()
        self.set_pwm_value(self.rg, self.rg_cal_load)
        self.rg_pos = G_POS_LOAD
        self.set_pwm_value(self.lg, self.lg_cal_load)
        self.lg_pos = G_POS_LOAD
        sleep(SERVO_MOVE_DELAY)


    # Make sure the right gripper doesn't block the camera
    def clear_camera(self):
        if(DEBUG == 1):
            print("clear_camera")
        if (self.rt_pos != T_POS_0):
            self.set_right_grip_open()
            self.set_right_turn_0()
            self.set_right_grip_closed()

    # Use the right gripper to rotate the cube 90 degrees clockwise
    def right_rotate_cube_90_cw(self):
        if(DEBUG == 1):
            print("right_rotate_cube_90_cw")
        if (self.lt_pos != T_POS_0):
            self.set_left_grip_open()
            self.set_left_turn_0()
        if (self.rt_pos == T_POS_P90):
            self.set_left_grip_closed()
            self.set_right_grip_open()
            self.set_right_turn_0()
            self.set_right_grip_closed()
        self.set_left_grip_open()
        if (self.rt_pos == T_POS_0):
            self.set_right_turn_90()
        else:
            self.set_right_turn_0()
        self.set_left_grip_closed()


    # Use the right gripper to rotate the cube 90 degrees counterclockwise
    def right_rotate_cube_90_ccw(self):
        if(DEBUG == 1):
            print("right_rotate_cube_90_ccw")
        if (self.lt_pos != T_POS_0):
            self.set_left_grip_open()
            self.set_left_turn_0()
        if (self.rt_pos == T_POS_M90):
            self.set_left_grip_closed()
            self.set_right_grip_open()
            self.set_right_turn_0()
            self.set_right_grip_closed()
        self.set_left_grip_open()
        if (self.rt_pos == T_POS_0):
            self.set_right_turn_m90()
        else:
            self.set_right_turn_0()
        self.set_left_grip_closed()


    # Use the right gripper to rotate the cube 180 degrees
    def right_rotate_cube_180(self):
        if(DEBUG == 1):
            print("right_rotate_cube_180")
        if (self.lt_pos != T_POS_0):
            self.set_left_grip_open()
            self.set_left_turn_0()
        if (self.rt_pos == T_POS_0):
            self.set_left_grip_closed()
            self.set_right_grip_open()
            self.set_right_turn_m90()
            self.set_right_grip_closed()
        self.set_left_grip_open()
        if (self.rt_pos == T_POS_M90):
            self.set_right_turn_90()
        else:
            self.set_right_turn_m90()
        self.set_left_grip_closed()


    # Use the right gripper to rotate a face 90 degrees clockwise
    def right_rotate_face_90_cw(self):
        if(DEBUG == 1):
            print("right_rotate_face_90_cw")
        if (self.lt_pos != T_POS_0):
            self.set_left_grip_open()
            self.set_left_turn_0()
            self.set_left_grip_closed()
        if (self.rt_pos == T_POS_P90):
            self.set_right_grip_open()
            self.set_right_turn_0()
            self.set_right_grip_closed()
        if (self.rt_pos == T_POS_M90):
            self.set_right_turn_0()
        else:
            self.set_right_turn_90()


    # Use the right gripper to rotate a face 90 degrees counterclockwise
    def right_rotate_face_90_ccw(self):
        if(DEBUG == 1):
            print("right_rotate_face_90_ccw")
        if (self.lt_pos != T_POS_0):
            self.set_left_grip_open()
            self.set_left_turn_0()
            self.set_left_grip_closed()
        if (self.rt_pos == T_POS_M90):
            self.set_right_grip_open()
            self.set_right_turn_0()
            self.set_right_grip_closed()
        if (self.rt_pos == T_POS_M90):
            self.set_right_turn_0()
        else:
            self.set_right_turn_m90()


    # Use the right gripper to rotate a face 180 degrees
    def right_rotate_face_180(self):
        if(DEBUG == 1):
            print("right_rotate_face_180")
        if (self.lt_pos != T_POS_0):
            self.set_left_grip_open()
            self.set_left_turn_0()
            self.set_left_grip_closed()
        if (self.rt_pos == T_POS_0):
            self.set_right_grip_open()
            self.set_right_turn_m90()
            self.set_right_grip_closed()
        if (self.rt_pos == T_POS_P90):
            self.set_right_turn_m90()
        else:
            self.set_right_turn_90()


    # Use the left gripper to rotate the cube 90 degrees clockwise
    def left_rotate_cube_90_cw(self):
        if(DEBUG == 1):
            print("left_rotate_cube_90_cw")
        if (self.rt_pos != T_POS_0):
            self.set_right_grip_open()
            self.set_right_turn_0()
        if (self.lt_pos == T_POS_P90):
            self.set_right_grip_closed()
            self.set_left_grip_open()
            self.set_left_turn_0()
            self.set_left_grip_closed()
        self.set_right_grip_open()
        if (self.lt_pos == T_POS_0):
            self.set_left_turn_90()
        else:
            self.set_left_turn_0()
        self.set_right_grip_closed()


    # Use the left gripper to rotate the cube 90 degrees counterclockwise
    def left_rotate_cube_90_ccw(self):
        if(DEBUG == 1):
            print("left_rotate_cube_90_ccw")
        if (self.rt_pos != T_POS_0):
            self.set_right_grip_open()
            self.set_right_turn_0()
        if (self.lt_pos == T_POS_M90):
            self.set_right_grip_closed()
            self.set_left_grip_open()
            self.set_left_turn_0()
            self.set_left_grip_closed()
        self.set_right_grip_open()
        if (self.lt_pos == T_POS_0):
            self.set_left_turn_m90()
        else:
            self.set_left_turn_0()
        self.set_right_grip_closed()


    # Use the left gripper to rotate the cube 180 degrees
    def left_rotate_cube_180(self):
        if(DEBUG == 1):
            print("left_rotate_cube_180")
        # Make sure the right gripper won't be in the way
        if (self.rt_pos != T_POS_0):
            self.set_right_grip_open()
            self.set_right_turn_0()
        if (self.lt_pos == T_POS_0):
            self.set_right_grip_closed()
            self.set_left_grip_open()
            self.set_left_turn_m90()
            self.set_left_grip_closed()
        self.set_right_grip_open()
        if (self.lt_pos == T_POS_M90):
            self.set_left_turn_90()
        else:
            self.set_left_turn_m90()
        self.set_right_grip_closed()


    # Use the left gripper to rotate a face 90 degrees clockwise
    def left_rotate_face_90_cw(self):
        if(DEBUG == 1):
            print("left_rotate_face_90_cw")
        if (self.rt_pos != T_POS_0):
            self.set_right_grip_open()
            self.set_right_turn_0()
            self.set_right_grip_closed()
        if (self.lt_pos == T_POS_P90):
            self.set_left_grip_open()
            self.set_left_turn_0()
            self.set_left_grip_closed()
        if (self.lt_pos == T_POS_M90):
            self.set_left_turn_0()
        else:
            self.set_left_turn_90()


    # Use the left gripper to rotate a face 90 degrees counterclockwise
    def left_rotate_face_90_ccw(self):
        if(DEBUG == 1):
            print("left_rotate_face_90_ccw")
        if (self.rt_pos != T_POS_0):
            self.set_right_grip_open()
            self.set_right_turn_0()
            self.set_right_grip_closed()
        if (self.lt_pos == T_POS_M90):
            self.set_left_grip_open()
            self.set_left_turn_0()
            self.set_left_grip_closed()
        if (self.lt_pos == T_POS_P90):
            self.set_left_turn_0()
        else:
            self.set_left_turn_m90()


    # Use the left gripper to rotate a face 180 degrees 
    def left_rotate_face_180(self):
        if(DEBUG == 1):
            print("left_rotate_face_180")
        if (self.rt_pos != T_POS_0):
            self.set_right_grip_open()
            self.set_right_turn_0()
            self.set_right_grip_closed()
        if (self.lt_pos == T_POS_0):
            self.set_left_grip_open()
            self.set_left_turn_m90()
            self.set_left_grip_closed()
        if (self.lt_pos == T_POS_P90):
            self.set_left_turn_m90()
        else:
            self.set_left_turn_90()


    # Calibrate a single servo
    def servo_cal(self, name, servo, val, btn_q):
        self.set_pwm_value(servo, val)

        while 1:
            # Wait for a button event
            button_press = btn_q.get()

            if (button_press == UP_BUTTON):
                # Increase the PWM value
                val += 1
                if (val > self.pwm_max):
                    val = self.pwm_max
                self.set_pwm_value(servo, val)
            elif (button_press == DOWN_BUTTON):
                # Decrease the PWM value
                val -= 1
                if (val < self.pwm_min):
                    val = self.pwm_min
                self.set_pwm_value(servo, val)
            elif (button_press == ENTER_BUTTON):
                break
        return val

    # Calibrate all servos
    def calibration(self, btn_q):

        # Adjust all the calibration values for the Right Turn servo
        self.rt_cal_m90 = self.servo_cal("RTM90", self.rt, self.rt_cal_m90, \
                                         btn_q)
        self.rt_cal_0 = self.servo_cal("RT0", self.rt, self.rt_cal_0, \
                                        btn_q)
        self.rt_cal_90 = self.servo_cal("RT90", self.rt, self.rt_cal_90, \
                                         btn_q)
        self.set_pwm_value(self.rt, self.rt_cal_0)

        # Adjust all the calibration values for the Right Grip servo
        self.rg_cal_close = self.servo_cal("RGC", self.rg, self.rg_cal_close, \
                                            btn_q)
        self.rg_cal_open = self.servo_cal("RGO", self.rg, self.rg_cal_open, \
                                           btn_q)
        self.rg_cal_load = self.servo_cal("RGR", self.rg, self.rg_cal_load, \
                                           btn_q)
        self.set_pwm_value(self.rg, self.rg_cal_open)

        # Adjust all the calibration values for the Left Turn servo
        self.lt_cal_m90 = self.servo_cal("LTM90", self.lt, self.lt_cal_m90, \
                                          btn_q)
        self.lt_cal_0 = self.servo_cal("LT0", self.lt, self.lt_cal_0, \
                                        btn_q)
        self.lt_cal_90 = self.servo_cal("LT90", self.lt, self.lt_cal_90, \
                                         btn_q)
        self.set_pwm_value(self.lt, self.lt_cal_0)

        # Adjust all the calibration values for the Left Grip servo
        self.lg_cal_close = self.servo_cal("LGC", self.lg, self.lg_cal_close, \
                                            btn_q)
        self.lg_cal_open = self.servo_cal("LGO", self.lg, self.lg_cal_open, \
                                           btn_q)
        self.lg_cal_load = self.servo_cal("LGR", self.lg, self.lg_cal_load, \
                                           btn_q)
        self.set_pwm_value(self.lg, self.lg_cal_open)

        # Save the new calibration values
        f=open(self.cal_file,'w+')
        # Write the new calibration values
        f.write(str(self.pwm_freq) + " PWM frequency\n")
        f.write(str(self.pwm_min) + " PWM count minimum\n")
        f.write(str(self.pwm_max) + " PWM count maximum\n")
        f.write(str(self.rg) + " Right Grip PWM port\n")
        f.write(str(self.rt) + " Right Turn PWM port\n")
        f.write(str(self.lg) + " Left Grip PWM port\n")
        f.write(str(self.lt) + " Left Turn PWM port\n")
        f.write(str(self.rt_cal_m90) + " Right turn minus 90 degrees\n")
        f.write(str(self.rt_cal_0) + " Right turn 0 degrees\n")
        f.write(str(self.rt_cal_90) + " Right turn 90 degrees\n")
        f.write(str(self.rg_cal_close) + " Right grip closed\n")
        f.write(str(self.rg_cal_open) + " Right grip open\n")
        f.write(str(self.rg_cal_load) + " Right grip cube load\n")
        f.write(str(self.lt_cal_m90) + " Left turn minus 90 degrees\n")
        f.write(str(self.lt_cal_0) + " Left turn 0 degrees\n")
        f.write(str(self.lt_cal_90) + " Left turn 90 degrees\n")
        f.write(str(self.lg_cal_close) + " Left grip closed\n")
        f.write(str(self.lg_cal_open) + " Left grip open\n")
        f.write(str(self.lg_cal_load) + " Left grip cube load\n")
        f.close()
