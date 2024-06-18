import sys
import os

from time import sleep

from queue import Queue

# Button press detection class
from rubik_buttons import RubikButtons, UP_BUTTON, DOWN_BUTTON, ENTER_BUTTON

# Servo control class
from rubik_servos import RubikServo

# Cube color scanner class
from rubik_scan import RubikScan

# This library provieds the moves needed to solve the cube.
import twophase.solver as solver


# Create the queue used to get button events
btn_q = Queue(maxsize = 8)

# Create the button class
#button = RubikButtons(btn_q)
#button.start()

# Create the servo controller class
try:
    servos = RubikServo(btn_q)
except:
    display.write_body("File Error")
    raise

# Create the cube scanner class
scanner = RubikScan(servos)

# Solve the cube
#
def solve():
    global display

    # Initialize the camera
    scanner.camera_init()

    # Set the grippers to the load cube position
    #servos.cube_load(display, btn_q)
    servos.cube_load(btn_q)
    
    try:
        # Read the cube faces to get the current color arrangement
        result = scanner.scan_cube()
        success = result[0]
        cube_string = result[1]
        # Flush any output messages
        sys.stdout.flush()
        if (success != True):
            #display.write_body("Scan Error")
            print("Pokazilo sa skenovanie")
            # Wait for a button press
            button_press = btn_q.get()
        else:
            print("Nepokazilo sa skenovanie")
            # Get the moves needed to solve the cube.
            # Search a full 5 seconds for the best solution.
            solve_string = solver.solve(cube_string, 100, 5)
            print("toto je solve string:")
            print(solve_string)
            print("toto je cube string:")
            print(cube_string)
            # Flush any output messages
            sys.stdout.flush()


            print(solve_string)
            #there would be solution mechanism
            # Release the cube so it can be removed
            servos.cube_release()
            # Flush any output messages
            sys.stdout.flush()

            # Wait for a button press
            button_press = btn_q.get()
    except KeyboardInterrupt:
        servos.cube_release()


# Calibrate the servos

def calibrate_servos():
    servos.calibration(btn_q)





# Flush any startup output messages
sys.stdout.flush()

# Display the main menu header
#display.write_header("Main menu")

# Main menu prompt and function array
main_menu = [("Solve",solve), \
             ("Quit", quit), \
             ("Calibrate", calibrate_servos)]
main_menu_size = len(main_menu)

# Start menu at position 0
menu_index = 0
#display.write_body(main_menu[0][0])


# The DOWN button advances to the next function
# The UP button goes back to the previous function
# The ENTER button executes the current function

while (1):
    # Wait for a button press
    button_press = ENTER_BUTTON
    if (button_press == UP_BUTTON):
        if (menu_index > 0):
            menu_index -= 1
        else:
            menu_index = 0
        display.write_body(main_menu[menu_index][0])
    elif(button_press == DOWN_BUTTON):
        if (menu_index < (main_menu_size - 1)):
            menu_index += 1
        else:
            menu_index = main_menu_size - 1
        display.write_body(main_menu[menu_index][0])
    elif(button_press == ENTER_BUTTON):
        main_menu[menu_index][1]()
        menu_index = 0
        #display.write_header("Main menu")
        #display.write_body(main_menu[0][0])
