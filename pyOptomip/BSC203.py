
from thorlabs_apt_device import BSC
import re
import math

"""
Module defines a BSC203 motor class designed to interface with the thorlabs bsc203 steper motor controller.

    - Handles connection, movement in xyz, position limits, simple state tracking  

"""

class BSC203Motor:
    name = 'BSC203'
    isMotor = True
    isOpt = False
    isElec = True
    isLaser = False
    isDetect = False
    isSMU = False

    def __init__(self):
        self.bsc = None
        self.numAxes = 0
        self.position = [0, 0, 0]
        self.minPositionSet = False
        self.minXPosition = 0
        self.maxZPositionSet = False
        self.maxZPosition = 0
        self.atZPosition = False
        self.calflag = False
        self.xbank = 0
        self.ybank = 0
        self.theta = 0

    def connect(self, SerialPortName, NumberOfAxis):
        """ 
            Connect to the BSC using driver https://thorlabs-apt-device.readthedocs.io/en/stable/_modules/thorlabs_apt_device/devices/bsc.html

        """
        self.visaName = SerialPortName # Started abstraction, don't know why
        numbers = re.findall('[0-9]+', SerialPortName)
        COM = "COM" + numbers[0]
        self.bsc = BSC(serial_port=COM, x=NumberOfAxis, home=False)
        self.bsc.identify()
        self.status = self.bsc.status_
        self.numAxes = NumberOfAxis
        print('Connected\n')

        # Sets maximum # of axis to send commands to
        if NumberOfAxis >= 6 | NumberOfAxis < 0:
            print('Invalid number of axes. Please enter at most six axes.\n')
            self.numAxes = 6

    def disconnect(self):
        self.bsc.close()

    def moveRelativeXYZ(self, x, y, z):
        """
        Moves the BSC203 motor a relative amount in the X, Y, and Z directions,
        while enforcing optional safety constraints such as minimum X and maximum Z limits.

        Parameters:
            x (float): Relative movement in the X-axis (positive or negative, in mm).
            y (float): Relative movement in the Y-axis (in mm).
            z (float): Relative movement in the Z-axis (in mm).

        Behavior:
            - Movement is scaled by 1000 for device communication. Movement is in encoder steps
            - If limits are not set, all movement is allowed.
            - If min X position is set, restricts leftward X movement past the defined minimum.
            - If max Z position is set, prevents lateral movement when Z is below a safe threshold.
            - Tracks software-estimated position and optional calibration values.
            - Issues user warnings in unsafe or restricted conditions.
        """

        # Case 1: No movement limits are enforced
        if not self.minPositionSet and not self.maxZPositionSet:
            # Perform full XYZ movement
            self.bsc.move_relative(distance=int(1000 * x), bay=0, channel=0)
            self.bsc.move_relative(distance=int(1000 * y), bay=1, channel=0)
            self.bsc.move_relative(distance=int(1000 * z), bay=2, channel=0)

            # Update software position tracking
            self.position[0] -= x
            self.position[1] -= y
            self.position[2] -= z

            # Accumulate displacement in calibration banks if flag is set
            if self.calflag:
                self.xbank += x
                self.ybank += y

        # Case 2: Only minimum X limit is enforced
        elif self.minPositionSet and not self.maxZPositionSet:
            if self.position[0] - x < self.minXPosition:
                print("Cannot Move Past Minimum X Position.")
            else:
                self.bsc.move_relative(distance=int(1000 * x), bay=0, channel=0)
                self.bsc.move_relative(distance=int(1000 * y), bay=1, channel=0)
                self.bsc.move_relative(distance=int(1000 * z), bay=2, channel=0)

                self.position[0] -= x
                self.position[1] -= y
                self.position[2] -= z

                if self.calflag:
                    self.xbank += x
                    self.ybank += y

        # Case 3: Only maximum Z limit is enforced
        elif not self.minPositionSet and self.maxZPositionSet:
            if self.position[2] - z >= (self.maxZPosition - 80):
                # Z motion is below safe limit — block XY motion
                self.bsc.move_relative(distance=int(1000 * z), bay=2, channel=0)
                self.position[2] -= z

                if x != 0 or y != 0:
                    print("Please Lift Wedge Probe.")
                    self.atZPosition = True
            else:
                # Full XYZ movement allowed
                self.bsc.move_relative(distance=int(1000 * x), bay=0, channel=0)
                self.bsc.move_relative(distance=int(1000 * y), bay=1, channel=0)
                self.bsc.move_relative(distance=int(1000 * z), bay=2, channel=0)

                self.position[0] -= x
                self.position[1] -= y
                self.position[2] -= z

                if self.calflag:
                    self.xbank += x
                    self.ybank += y

                # Reset wedge probe flag if Z is above limit
                if self.position[2] <= self.maxZPosition:
                    self.atZPosition = False

        # Case 4: Both min X and max Z limits are enforced
        elif self.minPositionSet and self.maxZPositionSet:
            if self.position[0] - x < self.minXPosition:
                print("Cannot Move Past Minimum X Position.")

            elif self.position[2] - z >= (self.maxZPosition - 80):
                # Z is too low to safely move XY
                self.bsc.move_relative(distance=int(1000 * z), bay=2, channel=0)
                self.position[2] -= z

                if x != 0 or y != 0:
                    print("Please Lift Wedge Probe.")
                    self.atZPosition = True
            else:
                # Safe to move XYZ
                self.bsc.move_relative(distance=int(1000 * x), bay=0, channel=0)
                self.bsc.move_relative(distance=int(1000 * y), bay=1, channel=0)
                self.bsc.move_relative(distance=int(1000 * z), bay=2, channel=0)

                self.position[0] -= x
                self.position[1] -= y
                self.position[2] -= z

                if self.calflag:
                    self.xbank += x
                    self.ybank += y

                if self.position[2] <= self.maxZPosition:
                    self.atZPosition = False


    def moveRelativeX(self, x):
        if self.minPositionSet is False:
            if x != 0:
                print('Please Set Minimum Position in X Axis.')
            else:
                pass

        else:
            if self.position[0] - x < self.minXPosition:
                print("Cannot Move Past Minimum X Position.")
            else:
                self.bsc.move_relative(distance=int(1000 * x), bay=0, channel=0)
                self.position[0] = self.position[0] - x


    def moveRelativeY(self, y):
        self.bsc.move_relative(distance=int(1000 * y), bay=1, channel=0)
        self.position[1] = self.position[1] - y

    def moveRelativeZ(self, z):
        self.bsc.move_relative(distance=int(1000 * z), bay=2, channel=0)
        self.position[2] = self.position[2] - z

    def getPosition(self):
        try:
            x = self.position[0]
            y = self.position[1]
            z = self.position[2]
            return [x, y, z]
        except Exception as e:
            print(e)
            print('An Error has occured')

    def setMinXPosition(self, minPosition):
        self.minXPosition = minPosition
        self.minPositionSet = True

    def setMaxZPosition(self, maxPosition):
        self.maxZPosition = maxPosition
        self.maxZPositionSet = True
