import os, math
from time import sleep
from PIL import Image
# Raspberry Pi camera library
from picamera import PiCamera

hasPictures = 1

# The image size for my camera
IMG_WIDTH = 640
IMG_HIGHT = 480


# Pixel locations of the centers of the 9 squares
LEFT_COLUMN  = 180 # X coordinates of the columns
MID_COLUMN   = 310
RIGHT_COLUMN = 430
TOP_ROW      =  45 # Y coordinates of the rows
MID_ROW      = 175
BOTTOM_ROW   = 300

# Rubic cube scanner class
class RubikScan(object):
    def __init__(self, serv):
        # Save the servo info provided by the caller
        self.servos = serv
        # pixel locations
        self.pxl_locs = [(LEFT_COLUMN,  TOP_ROW),
                         (MID_COLUMN,   TOP_ROW),
                         (RIGHT_COLUMN, TOP_ROW),
                         (LEFT_COLUMN,  MID_ROW),
                         (MID_COLUMN,   MID_ROW),
                         (RIGHT_COLUMN, MID_ROW),
                         (LEFT_COLUMN,  BOTTOM_ROW),
                         (MID_COLUMN,   BOTTOM_ROW),
                         (RIGHT_COLUMN, BOTTOM_ROW)]

        # Check if folder exists
        if not os.path.exists("Cube"):
            os.makedirs("Cube")
            os.chmod("Cube", 0o777)


    # Initialize the camera
    def camera_init(self):
        # init camera driver/hardware
        self.camera = PiCamera()
        self.camera.resolution = (IMG_WIDTH, IMG_HIGHT)
        self.camera.start_preview()
        self.camera.iso = 400

    # Read cube faces
    def get_cube(self):
        # Set the camera exposure settings.
        es = self.camera.exposure_speed
        self.camera.exposure_mode = 'off'
        self.camera.shutter_speed = es
        g = self.camera.awb_gains
        self.camera.awb_mode = 'off'
        self.camera.awb_gains = g

        self.camera.saturation = 50
        sleep(2)

        #getting faces
        try:
            self.camera.capture('Cube/face2.jpg')

            self.servos.right_rotate_cube_90_cw()
            self.servos.clear_camera()

            self.camera.capture('Cube/face1.jpg')

            self.servos.right_rotate_cube_90_cw()
            self.servos.clear_camera()

            self.camera.capture('Cube/face5.jpg')

            self.servos.right_rotate_cube_90_cw()
            self.servos.clear_camera()

            self.camera.capture('Cube/face4.jpg')

            self.servos.left_rotate_cube_90_cw()
            self.servos.right_rotate_cube_90_cw()
            self.servos.clear_camera()

            self.camera.capture('Cube/face0.jpg')

            self.servos.right_rotate_cube_180()
            self.servos.clear_camera()

            self.camera.capture('Cube/face3.jpg')

        finally:
            # Release the camera
            self.camera.close()


    def scan_cube(self):
        # Get images for all sides of the cube.
        
        if (hasPictures == 0):
            self.get_cube()
        else:
            self.camera.close()
        # color of each square.
        return self.get_colors() 


    # Average the pixel color in 5x5
    def pix_average(self, im, x, y):
        # Clear values
        r_avg = 0
        g_avg = 0
        b_avg = 0

        # x and y in corner
        x -= 2
        y -= 2

        # Add the RGB values together
        for x_inc in range (0,5):
            for y_inc in range (0,5):
                # Read the RGB values for single pixel
                r_pix, g_pix, b_pix = im.getpixel((x + x_inc, y + y_inc))
                r_avg += r_pix
                g_avg += g_pix
                b_avg += b_pix

        # average of values
        r_avg = r_avg / 25
        g_avg = g_avg / 25
        b_avg = b_avg / 25

        return r_avg, g_avg, b_avg


    #Getting cube string
    def get_center_color(self, text, file):
        im = Image.open(file)
        im = im.convert('RGB')
        #im.save('Cube/debug.jpg')
        r, g, b = self.pix_average(im, \
                                   self.pxl_locs[4][0], \
                                   self.pxl_locs[4][1])
        return r, g, b 

    # Get the color of each square on the cube
    def get_colors(self):
        # get the center colors to identify other squares
        center_colors = []
        print("vypis fareb")
        r, g, b = self.get_center_color("Face 0 - Up", "Cube/face0.jpg")
        center_colors.append((r, g, b, "U"))

        r, g, b = self.get_center_color("Face 1 - Right", "Cube/face1.jpg")
        center_colors.append((r, g, b, "R"))

        r, g, b = self.get_center_color("Face 2 - Front", "Cube/face2.jpg")
        center_colors.append((r, g, b, "F"))

        r, g, b = self.get_center_color("Face 3 - Down", "Cube/face3.jpg")
        center_colors.append((r, g, b, "D"))

        r, g, b = self.get_center_color("Face 4 - Left", "Cube/face4.jpg")
        center_colors.append((r, g, b, "L"))

        r, g, b = self.get_center_color("Face 5 - Back", "Cube/face5.jpg")
        center_colors.append((r, g, b, "B"))

        # for holding cube string
        cube_def_string = ""

        # for counting separate colors
        color_count = [0, 0, 0, 0, 0, 0]

        # Loop through the 6 faces
        for img_iter in range(0, 6):
            img_path = "Cube/face" + str(img_iter) + ".jpg"
            im = Image.open(img_path)
            im = im.convert('RGB')

            # Loop through the 9 squares on a face
            for pix_iter in range(0,9):
                if (img_iter == 3):
                    #Down face image upside down, scan in reverse
                    r, g, b = self.pix_average(im, \
                                              self.pxl_locs[8 - pix_iter][0], \
                                              self.pxl_locs[8 - pix_iter][1])
                else:
                    r, g, b = self.pix_average(im, \
                                              self.pxl_locs[pix_iter][0], \
                                              self.pxl_locs[pix_iter][1])
                                              
                #euclidian trough minimum value                              
                min_dist = -1
                face = 'X'
                print(center_colors)
                for index in range(0, len(center_colors)):
                    cc_r, cc_g, cc_b, f = center_colors[index]
                    dist = math.pow(r - cc_r, 2) + math.pow(g - cc_g, 2) \
                           + math.pow(b - cc_b, 2)

                    if((min_dist == -1) or (dist < min_dist)):
                        min_dist = dist
                        face = f
                        min_index = index

                # append square color to cube string.
                cube_def_string = cube_def_string + face
                color_count[min_index] += 1

        print("tu vypise cube def string")
        print(cube_def_string)
        #cube_def_string = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
        #cube_def_string = "WWWWWWWWWRRRRRRRRRGGGGGGGGGYYYYYYYYYOOOOOOOOOBBBBBBBBB"
        
        # Verify there are 9 squares of each color
        success = True
        for index in range(0, 6):
            if (color_count[index] != 9):
                success = False
                
        return success, cube_def_string
