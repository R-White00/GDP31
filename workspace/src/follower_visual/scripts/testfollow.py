#!/usr/bin/env python

import rospy
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
#from std_srvs.srv import Empty
import time
import numpy as np
import math
import cv2
import cv_bridge



bridge = cv_bridge.CvBridge()
## User-defined parameters: (Update these values to your liking)
# Minimum size for a contour to be considered anything
MIN_AREA = 500 

# Minimum size for a contour to be considered part of the track
MIN_AREA_TRACK = 5000

# Robot's speed when following the line
LINEAR_SPEED = 0.2

# Proportional constant to be applied on speed when turning 
# (Multiplied by the error value)
KP = 1.5/100 

# If the line is completely lost, the error value shall be compensated by:
LOSS_FACTOR = 1.2

# Send messages every $TIMER_PERIOD seconds
TIMER_PERIOD = 0.06

# When about to end the track, move for ~$FINALIZATION_PERIOD more seconds
FINALIZATION_PERIOD = 4

# The maximum error value for which the robot is still in a straight line
MAX_ERROR = 30
# BGR values to filter only the selected color range
lower_bgr_values = np.array([0,  80,  0])
upper_bgr_values = np.array([60, 255, 60])

def crop_size(height, width):
    """
    Get the measures to crop the image
    Output:
    (Height_upper_boundary, Height_lower_boundary,
     Width_left_boundary, Width_right_boundary)
    """
    ## Update these values to your liking.

    return (1*height//3, height, width//4, 3*width//4)

# Global vars. initial values
image_input = 0
error = 0
just_seen_line = False
just_seen_right_mark = False
should_move = False
right_mark_count = 0
message = Twist()
finalization_countdown = None

def nothing(n):
    pass

def start_follower_callback(request, response):
    """
    Start the robot.
    In other words, allow it to move (again)
    """
    global should_move
    global right_mark_count
    global finalization_countdown
    should_move = True
    right_mark_count = 0
    finalization_countdown = None
    return response

def stop_follower_callback(request, response):
    """
    Stop the robot
    """
    global should_move
    global finalization_countdown
    should_move = False
    finalization_countdown = None
    return response

def image_callback(msg):
    """
    Function to be called whenever a new Image message arrives.
    Update the global variable 'image_input'
    """
    global image_input
    image_input = bridge.imgmsg_to_cv2(msg,desired_encoding='bgr8')
    # node.get_logger().info('Received image')

def get_contour_data(img):
    mask = cv2.inRange(img, lower_bgr_values, upper_bgr_values)

          # lower = np.array([lh, ls, lv], dtype = "uint8")
          # higher = np.array([hh, hs, hv], dtype = "uint8")
          # hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
          # cv2.imshow('windo2qwefeww',hsv)
          # h, w = img.shape[:2]
          # mask = cv2.inRange(hsv, lower, higher)
    cv2.imshow('windo2qw',mask)

    image ,contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_L1)
    contour_centres = np.empty((0,2), int)       
    for c in contours:
        if (cv2.contourArea(c) != 0):
                    # calculate moments for each contour
            M = cv2.moments(c)        
                    # calculate x,y coordinate of center
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            contour_centres= np.append(contour_centres, np.array([[cX, cY]]), axis =0)

    return contour_centres

def turn_body():
    global message
    message.linear.x = 0.1
    message.angular.z = 1
    cmd_pub.publish(message)


def timer_callback(boo):
    global message
    cmd_pub.publish(2, 3)
    global error
    global image_input
    global just_seen_line
    global just_seen_right_mark
    global should_move
    global right_mark_count
    global finalization_countdown
    # Wait for the first image to be received
    if type(image_input) != np.ndarray:
        return
    height, width, _ = image_input.shape
    img = image_input.copy()

    #get contour centres from image
    contour_centres = get_contour_data(img)  
    if contour_centres.size == 0:
        turn_body()
        time.sleep(0.1)
    print contour_centres
    #convert centres to line path
    #[vx,vy,x0,y0] = cv2.fitLine(contour_centres, 2, 0, 0.01, 0.01)
    #print x0, y0, vy, vx
    #draw line on image and find line properties
    #m = 600
    #cv2.line(img, (int(x0[0]-m*vx[0]), int(y0[0]-m*vy[0])),(int(x0[0]+m*vx[0]), int(y0[0]+m*vy[0])), (50, 255, 50), 4)
    cv2.imshow('window',img)
    
    #angle_rad = math.tan(vy/vx)

    # line equation is y = vy/vx *x + constant
    #height / 2 = vy/vx * x + constant
    #x = height/2 - constant *vx/vy
    #find middle x values
    #constant = x0/math.tan(math.pi -angle_rad) - y0
    #middle_x = (height/2 - constant) *vx/vy
    
    #output velocities
    # if (math.pi/2 - 0.2 < angle_rad < math.pi/2 + 0.2): #for skewed line
    #     if (middle_x == width / 2):                    #for off centre line
    #         message.linear.x = LINEAR_SPEED
    #     else:
    #         error = x - width//2
    #         message.angular.z = float(error) * -KP
    #         print("Error: {} | Angular Z: {}, ".format(error, message.angular.z)) 
    # else:
    #         print poo

    # if line:
    # # if there even is a line in the image:
    # # (as the camera could not be reading any lines)      
    #     x = get_line_x[2]

    #     # error:= The difference between the center of the image
    #     # and the center of the line
    #     error = x - width//2

    #     message.linear.x = LINEAR_SPEED
    #     just_seen_line = True

    #     # plot the line on the image
    #     cv2.circle(output, line, 5, (0,255,0), 7)
    #     cv2.imshow(output)
    # else:
    #     # There is no line in the image. 
    #     # Turn on the spot to find it again. 
    #     if just_seen_line:
    #         just_seen_line = False
    #         error = error * LOSS_FACTOR
    #     message.linear.x = 0.0
    
    # # Determine the speed to turn and get the line in the center of the camera.
    # message.angular.z = float(error) * -KP
    # print("Error: {} | Angular Z: {}, ".format(error, message.angular.z))
    


    # Show the output image to the user
    #cv2.imshow("output", output)
    # Print the image for 5milis, then resume execution
    cv2.waitKey(5)

        # Publish the message to 'cmd_vel'
    cmd_pub.publish(message)




if __name__ == '__main__':
       
    try:
        rospy.init_node('Visual_Follower')
        cmd_pub = rospy.Publisher('/cmd_vel',Twist, queue_size=10)
        image_sub = rospy.Subscriber('usb_cam_front/image_raw',Image, image_callback, queue_size=10)
        timer = rospy.Timer(rospy.Duration(TIMER_PERIOD), timer_callback)
    #timer_callback()
        #start_service = rospy.Service(Empty, 'start_follower', start_follower_callback)
        #stop_service = rospy.Service(Empty, 'stop_follower', stop_follower_callback)

        rospy.spin()
    except rospy.ROSInterruptException:
        pass
