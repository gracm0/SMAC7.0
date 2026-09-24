#!/usr/bin/env python3
from inchworm_control.ik import inverseKinematics
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String
# for servo
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
import time
from inchworm_control.lewansoul_servo_bus import ServoBus
from time import sleep 

class MotorController(Node):
    def __init__(self):
        """
        Initialization method for the motor controller node.

        Initializes ROS2 publisher, subscriber, GPIO pins, motor angles, and step actions for the inchworm robot.
        """
        # Initialize the ROS2 node with the name 'motor_controller'
        super().__init__('motor_controller')

        # Create subscriber for motor pos commands
        self.command_sub = self.create_subscription(
            
            String,
            "/motor_command",
            self.motor_pos_callback,
            10
        )

        # Create publisher for current motor positions
        self.position_pub = self.create_publisher(
            String,
            "/motor_position",
            10
        )



        # Initialize the connection to the servo motor bus over a USB-TTL connection
        # Note: The RPi should be connected to the bottom-left USB port and no other USB devices should be connected
        # If the connection fails, try disconnecting and reconnecting the USB port
    
        self.servo_bus = ServoBus('/dev/ttyUSB0')  
        self.get_logger().info('Node starting')

        # init motors
        self.init_motors()

        # init servos
        GPIO.setmode(GPIO.BOARD)

        # Initialize GPIO pins 11 and 13 for controlling the gripper servos
        GPIO.setup(11, GPIO.OUT)  # Pin 11 as output for servo1
        GPIO.setup(13, GPIO.OUT)  # Pin 13 as output for servo2

        # Set up PWM (Pulse Width Modulation) for the two gripper servos, with a frequency of 50Hz
        self.servo1 = GPIO.PWM(11,50) # pin 11 for servo1, pulse 50Hz
        self.servo2 = GPIO.PWM(13,50) # pin 13 for servo2, pulse 50Hz

        # Start PWM with an initial duty cycle of 0 (no movement)
        self.servo1.start(0)
        self.servo2.start(0)

        # Note: Motors are not allowed to have negative positions
        
        print("----------------Initial Motor Angles-----------------------")
        print(self.motor_1.pos_read(), 
            self.motor_2.pos_read(), 
            self.motor_3.pos_read(), 
            self.motor_4.pos_read(), 
            self.motor_5.pos_read())

        # Call publisher at 10hz
        self.timer = self.create_timer(
            0.1,           # 10 Hz
            self.pos_publisher_callback
        )



    def motor_pos_callback(self, msg):
        # msg string defined as: (theta1, theta2, theta3, theta4, theta5, gripper1, gripper2)
        # Would make this a message class in the future

        angles = msg.data.split(",")

        # Dont move for now, just print
        print(f"Moving to these angles: {angles}")
        # return

        # Move as quickly as possible following the debbuger sliders
        self.move_to(float(angles[0]),float(angles[1]),float(angles[2]), float(angles[3]), float(angles[4]), 0.1)

        s1_value = int(float(angles[5]))
        s2_value = int(float(angles[6]))
        self.servo1.ChangeDutyCycle(2+(s1_value/18))
        self.servo2.ChangeDutyCycle(2+(s2_value/18))

    def pos_publisher_callback(self):
        # Grippers dont have position feeedback
        motor_pos = [
            self.motor_1.pos_read(),
            self.motor_2.pos_read(),
            self.motor_3.pos_read(),
            self.motor_4.pos_read(),
            self.motor_5.pos_read()
        ]
        msg = String()
        msg.data = f"{motor_pos[0]},{motor_pos[1]},{motor_pos[2]},{motor_pos[3]},{motor_pos[4]}"
        self.position_pub.publish(msg)


    def init_motors(self):
        """
        Retrieves and initializes motors from the servo bus.
        """
        self.motor_1 = self.servo_bus.get_servo(1)
        self.motor_2 = self.servo_bus.get_servo(2)
        self.motor_3 = self.servo_bus.get_servo(3)
        self.motor_4 = self.servo_bus.get_servo(4)
        self.motor_5 = self.servo_bus.get_servo(5)
        print(self.motor_1.is_powered())
        self.time_to_move = 1.5 # Set the time over which the motors will move.


    def move_to(self, theta1, theta2, theta3, theta4, theta5, time):
        """
        Move motors to specified angles over a given time duration.

        Args:
            theta2 (float): Target angle for motor 2.
            theta3 (float): Target angle for motor 3.
            theta4 (float): Target angle for motor 4.
            time (float): Duration to reach the target angles (in seconds).
        """
        # TODO: Look into whether it's worth calling self.time_to_move here rather than passing in time as a parameter.
        # TODO: take in theta1 and theta5 as well
        self.motor_1.move_time_write(theta1, time)
        self.motor_2.move_time_write(theta2, time)
        self.motor_3.move_time_write(theta3, time)
        self.motor_4.move_time_write(theta4, time)
        self.motor_5.move_time_write(theta5, time)

        # Pause the program to allow the motors to finish moving. 
        sleep(time)
    

   
## Due to indentation things, these two functions (activate/release servo) are not part of the MotorController class
# servo angle of 0 is activated, 180 released
def activate_servo(servo_id):
    """
    Activate the servo motor so that the gripper latches onto the surface. 
    Args:
        servo_id: The servo motor object to be activated. 
    """
    # Set duty cycle to move servo to 0° position (2 corresponds to 0° for most servos)
    servo_id.ChangeDutyCycle(2+(0/18))
    # Pause to allow servo to reach position
    time.sleep(1)
    # Stop sending signal to servo
    servo_id.ChangeDutyCycle(0)

# Releases the servo by moving it to 180 degrees (or a fully released position)
def release_servo(servo_id):
    """
    Release the servo motor so that the gripper detached from the surface. 
    Args:
        servo_id: The servo motor object to be released. 
    """
    # Set duty cycle to move servo to 180° position (12 corresponds to 180° for most servos)
    servo_id.ChangeDutyCycle(2+(180/18))
    # Pause to allow servo to reach position
    time.sleep(1)
    # Stop sending signal to servo
    servo_id.ChangeDutyCycle(0)

def main(args=None):
    rclpy.init(args=args)
    motor_controller = MotorController()
    rclpy.spin(motor_controller)
    motor_controller.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()