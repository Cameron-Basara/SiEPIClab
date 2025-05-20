from base import MotorDriver, MotorStatus, MotorConnectionError, MotorMovementError
from typing import Tuple, Optional, Dict, Any, List
import time

class StepperMotorDriver(MotorDriver):
    """
    Implementation of a stepper motor driver.
    This is an example implementation showing how to use the base class.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._connected = False
        # Extract configuration or use defaults
        self._port = self._config.get("port", "/dev/ttyUSB0")
        self._baud_rate = self._config.get("baud_rate", 115200)
        self._steps_per_mm = self._config.get("steps_per_mm", {"x": 80.0, "y": 80.0, "z": 400.0})
        self._has_z = self._config.get("has_z_axis", True)
        # Initialize connection object (in a real implementation, this would be a serial connection)
        self._connection = None
        
    def connect(self) -> bool:
        """Connect to the stepper motor controller."""
        try:
            # In a real implementation, this would establish a serial connection
            # self._connection = serial.Serial(self._port, self._baud_rate, timeout=1.0)
            
            # For demonstration purposes:
            print(f"Connecting to stepper motor controller on {self._port} at {self._baud_rate} baud")
            time.sleep(0.5)  # Simulate connection time
            
            # Initialize motor
            self._connected = True
            self._status = MotorStatus.IDLE
            
            # Send homing command to initialize position
            # self._send_command("G28")  # In real implementation
            
            return True
        except Exception as e:
            self._error_message = f"Connection failed: {str(e)}"
            self._status = MotorStatus.ERROR
            raise MotorConnectionError(self._error_message)
    
    def disconnect(self) -> bool:
        """Disconnect from the stepper motor controller."""
        if not self._connected:
            return True
        
        try:
            # In a real implementation, this would close the serial connection
            # self._connection.close()
            
            # For demonstration purposes:
            print("Disconnecting from stepper motor controller")
            
            self._connected = False
            self._status = MotorStatus.DISCONNECTED
            return True
        except Exception as e:
            self._error_message = f"Disconnection failed: {str(e)}"
            return False
    
    def move_relative(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0, 
                     speed: Optional[Dict[str, float]] = None) -> bool:
        """Move the motor by a relative distance."""
        if not self._connected:
            self._error_message = "Motor not connected"
            return False
        
        # Calculate new positions
        new_x = self._axes["x"] + dx
        new_y = self._axes["y"] + dy
        new_z = self._axes["z"] + dz
        
        # Validate movement is within limits
        if not self._validate_movement("x", new_x) or \
           not self._validate_movement("y", new_y) or \
           not self._validate_movement("z", new_z):
            self._error_message = "Movement would exceed limits"
            raise MotorMovementError(self._error_message)
        
        # Apply speed overrides if provided
        move_speeds = self._speeds.copy()
        if speed:
            move_speeds.update(speed)
        
        # Adjust for Z-axis support
        if not self.has_z_axis() and dz != 0:
            self._error_message = "Z-axis not supported"
            raise MotorMovementError(self._error_message)
        
        try:
            # For demonstration purposes:
            print(f"Moving relatively by X:{dx:.3f}, Y:{dy:.3f}, Z:{dz:.3f}")
            
            # In a real implementation, calculate steps from mm and send commands
            # x_steps = int(dx * self._steps_per_mm["x"])
            # y_steps = int(dy * self._steps_per_mm["y"])
            # z_steps = int(dz * self._steps_per_mm["z"])
            # self._send_command(f"G91")  # Set to relative mode
            # self._send_command(f"G1 X{dx} Y{dy} Z{dz} F{move_speeds['x']}")
            
            self._status = MotorStatus.MOVING
            time.sleep(0.5)  # Simulate movement time
            
            # Update internal position tracking
            self._axes["x"] = new_x
            self._axes["y"] = new_y
            self._axes["z"] = new_z
            
            self._status = MotorStatus.IDLE
            return True
        except Exception as e:
            self._error_message = f"Movement failed: {str(e)}"
            self._status = MotorStatus.ERROR
            raise MotorMovementError(self._error_message)
    
    def move_absolute(self, x: Optional[float] = None, y: Optional[float] = None, 
                     z: Optional[float] = None, speed: Optional[Dict[str, float]] = None) -> bool:
        """Move the motor to an absolute position."""
        if not self._connected:
            self._error_message = "Motor not connected"
            return False
        
        # Calculate movement values
        target_x = x if x is not None else self._axes["x"]
        target_y = y if y is not None else self._axes["y"]
        target_z = z if z is not None else self._axes["z"]
        
        # Validate movement is within limits
        if not self._validate_movement("x", target_x) or \
           not self._validate_movement("y", target_y) or \
           not self._validate_movement("z", target_z):
            self._error_message = "Movement would exceed limits"
            raise MotorMovementError(self._error_message)
        
        # Apply speed overrides if provided
        move_speeds = self._speeds.copy()
        if speed:
            move_speeds.update(speed)
        
        # Adjust for Z-axis support
        if not self.has_z_axis() and z is not None:
            self._error_message = "Z-axis not supported"
            raise MotorMovementError(self._error_message)
        
        try:
            # For demonstration purposes:
            print(f"Moving to absolute position X:{target_x:.3f}, Y:{target_y:.3f}, Z:{target_z:.3f}")
            
            # In a real implementation, send G-code commands
            # self._send_command(f"G90")  # Set to absolute mode
            # self._send_command(f"G1 X{target_x} Y{target_y} Z{target_z} F{move_speeds['x']}")
            
            self._status = MotorStatus.MOVING
            time.sleep(0.5)  # Simulate movement time
            
            # Update internal position tracking
            self._axes["x"] = target_x
            self._axes["y"] = target_y
            self._axes["z"] = target_z
            
            self._status = MotorStatus.IDLE
            return True
        except Exception as e:
            self._error_message = f"Movement failed: {str(e)}"
            self._status = MotorStatus.ERROR
            raise MotorMovementError(self._error_message)
    
    def get_position(self) -> Tuple[float, float, float]:
        """Get the current position."""
        # In a real implementation, you might query the actual hardware position
        # For demonstration purposes, return the tracked position:
        return (self._axes["x"], self._axes["y"], self._axes["z"])
    
    def has_z_axis(self) -> bool:
        """Check if the motor has Z-axis capability."""
        return self._has_z
    
    def home(self, axes: Optional[List[str]] = None) -> bool:
        """Move the motor to its home position."""
        if not self._connected:
            self._error_message = "Motor not connected"
            return False
        
        # Default to all axes if none specified
        if axes is None:
            axes = ["x", "y"]
            if self.has_z_axis():
                axes.append("z")
        
        try:
            # Lowercase and filter valid axes
            axes = [axis.lower() for axis in axes if axis.lower() in ["x", "y", "z"]]
            
            if not axes:
                return True  # No axes to home
            
            # For demonstration purposes:
            print(f"Homing axes: {', '.join(axes)}")
            
            # In a real implementation, send homing commands
            # if all(axis in axes for axis in ["x", "y", "z"]):
            #     self._send_command("G28")  # Home all axes
            # else:
            #     homing_cmd = "G28"
            #     if "x" in axes:
            #         homing_cmd += " X"
            #     if "y" in axes:
            #         homing_cmd += " Y"
            #     if "z" in axes:
            #         homing_cmd += " Z"
            #     self._send_command(homing_cmd)
            
            self._status = MotorStatus.HOMING
            time.sleep(1.0)  # Simulate homing time
            
            # Reset positions for homed axes
            for axis in axes:
                self._axes[axis] = 0.0
            
            self._status = MotorStatus.IDLE
            return True
        except Exception as e:
            self._error_message = f"Homing failed: {str(e)}"
            self._status = MotorStatus.ERROR
            return False
    
    def stop(self, emergency: bool = False) -> bool:
        """Stop all motor movement."""
        if not self._connected:
            return True
        
        try:
            # For demonstration purposes:
            print(f"{'Emergency ' if emergency else ''}Stop command sent")
            
            # In a real implementation, send stop commands
            # if emergency:
            #     self._send_command("M112")  # Emergency stop
            # else:
            #     self._send_command("M410")  # Quick stop
            
            self._status = MotorStatus.IDLE
            return True
        except Exception as e:
            self._error_message = f"Stop failed: {str(e)}"
            self._status = MotorStatus.ERROR
            return False
    
    # Additional helper methods for this implementation
    
    def _send_command(self, command: str) -> str:
        """
        Send a command to the motor controller and get the response.
        
        Args:
            command: Command string to send
            
        Returns:
            str: Response from the controller
        """
        # In a real implementation, this would send serial commands
        # self._connection.write(f"{command}\n".encode())
        # return self._connection.readline().decode().strip()
        
        # For demonstration purposes:
        print(f"SEND: {command}")
        return "ok"  # Simulate controller response