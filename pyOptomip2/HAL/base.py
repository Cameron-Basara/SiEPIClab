"""
Created on 5/20/2025 by Cameron Basara

Purpose: Abstraction classes to be used as the base for each driver for each device.

"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any, List
from enum import Enum
import time

class MotorStatus(Enum):
    """Enum representing the possible states of a motor."""
    DISCONNECTED = 0
    IDLE = 1 
    MOVING = 2
    ERROR = 3
    HOMING = 4
    CALIBRATING = 5

class MotorError(Exception):
    """Base exception for motor-related errors."""
    pass

class MotorConnectionError(MotorError):
    """Exception raised when connection to motor fails."""
    pass

class MotorMovementError(MotorError):
    """Exception raised when a movement command fails."""
    pass

class MotorDriver(ABC):
    """
    Abstract base class for all motor drivers in the HAL.
    Defines the required interface for any motor controller.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the motor driver with optional configuration.
        
        Args:
            config: Dictionary containing configuration parameters for the motor
        """
        self._config = config or {}
        self._status = MotorStatus.DISCONNECTED
        self._error_message = ""
        self._axes = {"x": 0.0, "y": 0.0, "z": 0.0}
        self._limits = {
            "x": {"min": float('-inf'), "max": float('inf')},
            "y": {"min": float('-inf'), "max": float('inf')},
            "z": {"min": float('-inf'), "max": float('inf')}
        }
        self._speeds = {"x": 1.0, "y": 1.0, "z": 1.0}  # Default speeds
        self._acceleration = {"x": 0.0, "y": 0.0, "z": 0.0}  # No acceleration by default
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the motor hardware.
        
        Returns:
            bool: True if connection was successful, False otherwise
        
        Raises:
            MotorConnectionError: If connection fails
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnect and clean up any resources.
        
        Returns:
            bool: True if disconnection was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def move_relative(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0,
                     speed: Optional[Dict[str, float]] = None) -> bool:
        """
        Move the motor by a relative amount along each axis.
        Axes not used can be left as 0.
        
        Args:
            dx: Relative movement along x-axis
            dy: Relative movement along y-axis
            dz: Relative movement along z-axis
            speed: Optional dictionary of speeds for each axis {"x": speed_x, "y": speed_y, "z": speed_z}
        
        Returns:
            bool: True if movement was successful, False otherwise
        
        Raises:
            MotorMovementError: If movement fails or would exceed limits
        """
        pass
    
    @abstractmethod
    def move_absolute(self, x: Optional[float] = None, y: Optional[float] = None, 
                     z: Optional[float] = None, speed: Optional[Dict[str, float]] = None) -> bool:
        """
        Move the motor to an absolute position. Leave any axis as None to skip.
        
        Args:
            x: Target x position, or None to maintain current position
            y: Target y position, or None to maintain current position
            z: Target z position, or None to maintain current position
            speed: Optional dictionary of speeds for each axis {"x": speed_x, "y": speed_y, "z": speed_z}
        
        Returns:
            bool: True if movement was successful, False otherwise
        
        Raises:
            MotorMovementError: If movement fails or would exceed limits
        """
        pass
    
    @abstractmethod
    def get_position(self) -> Tuple[float, float, float]:
        """
        Get the current position as (x, y, z) tuple.
        Missing axes return 0.0 or are ignored depending on device.
        
        Returns:
            Tuple[float, float, float]: Current (x, y, z) position
        """
        pass
    
    def has_axis(self, axis: str) -> bool:
        """
        Check if the motor supports a specific axis.
        
        Args:
            axis: Axis name ('x', 'y', or 'z')
            
        Returns:
            bool: True if the axis is supported, False otherwise
        """
        if axis.lower() == 'z':
            return self.has_z_axis()
        return axis.lower() in ['x', 'y']
    
    def has_z_axis(self) -> bool:
        """
        Check if this motor supports a Z-axis.
        Default = True.
        
        Returns:
            bool: True if z-axis is supported, False otherwise
        """
        return True
    
    def get_status(self) -> MotorStatus:
        """
        Get the current status of the motor.
        
        Returns:
            MotorStatus: Current status enum value
        """
        return self._status
    
    def get_error(self) -> str:
        """
        Get the last error message, if any.
        
        Returns:
            str: Error message or empty string if no error
        """
        return self._error_message
    
    def set_config(self, config: Dict[str, Any]) -> bool:
        """
        Update the motor configuration.
        
        Args:
            config: Dictionary of configuration parameters
            
        Returns:
            bool: True if configuration was updated successfully
        """
        self._config.update(config)
        return True
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current motor configuration.
        
        Returns:
            Dict[str, Any]: Current configuration
        """
        return self._config.copy()
    
    def set_limits(self, axis: str, min_val: Optional[float] = None, 
                 max_val: Optional[float] = None) -> bool:
        """
        Set movement limits for a specific axis.
        
        Args:
            axis: Axis name ('x', 'y', or 'z')
            min_val: Minimum allowed value, or None to leave unchanged
            max_val: Maximum allowed value, or None to leave unchanged
            
        Returns:
            bool: True if limits were set successfully
        """
        if axis.lower() not in self._limits:
            return False
            
        if min_val is not None:
            self._limits[axis.lower()]["min"] = min_val
        if max_val is not None:
            self._limits[axis.lower()]["max"] = max_val
        return True
    
    def get_limits(self, axis: str) -> Dict[str, float]:
        """
        Get the movement limits for a specific axis.
        
        Args:
            axis: Axis name ('x', 'y', or 'z')
            
        Returns:
            Dict[str, float]: Dictionary with 'min' and 'max' keys
        """
        if axis.lower() not in self._limits:
            return {"min": float('-inf'), "max": float('inf')}
        return self._limits[axis.lower()].copy()
    
    def set_speed(self, speeds: Dict[str, float]) -> bool:
        """
        Set movement speeds for each axis.
        
        Args:
            speeds: Dictionary of speeds for each axis {"x": speed_x, "y": speed_y, "z": speed_z}
            
        Returns:
            bool: True if speeds were set successfully
        """
        for axis, speed in speeds.items():
            if axis.lower() in self._speeds:
                self._speeds[axis.lower()] = speed
        return True
    
    def get_speeds(self) -> Dict[str, float]:
        """
        Get the current speed settings.
        
        Returns:
            Dict[str, float]: Dictionary of speeds for each axis
        """
        return self._speeds.copy()
    
    def set_acceleration(self, acceleration: Dict[str, float]) -> bool:
        """
        Set acceleration for each axis.
        
        Args:
            acceleration: Dictionary of acceleration values for each axis
                         {"x": accel_x, "y": accel_y, "z": accel_z}
            
        Returns:
            bool: True if acceleration was set successfully
        """
        for axis, accel in acceleration.items():
            if axis.lower() in self._acceleration:
                self._acceleration[axis.lower()] = accel
        return True
    
    def get_acceleration(self) -> Dict[str, float]:
        """
        Get the current acceleration settings.
        
        Returns:
            Dict[str, float]: Dictionary of acceleration values for each axis
        """
        return self._acceleration.copy()
    
    @abstractmethod
    def home(self, axes: Optional[List[str]] = None) -> bool:
        """
        Move the motor to its home position.
        
        Args:
            axes: List of axes to home, or None to home all supported axes
            
        Returns:
            bool: True if homing was successful
        """
        pass
    
    @abstractmethod
    def stop(self, emergency: bool = False) -> bool:
        """
        Stop all motor movement.
        
        Args:
            emergency: If True, perform emergency stop (faster but may cause mechanical stress)
            
        Returns:
            bool: True if stop was successful
        """
        pass
    
    def is_moving(self) -> bool:
        """
        Check if the motor is currently moving.
        
        Returns:
            bool: True if moving, False otherwise
        """
        return self._status == MotorStatus.MOVING
    
    def wait_until_idle(self, timeout: float = 30.0) -> bool:
        """
        Wait until the motor is no longer moving.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if motor is idle, False if timeout occurred
        """
        start_time = time.time()
        while self.is_moving():
            if time.time() - start_time > timeout:
                return False
            time.sleep(0.01)  # Short sleep to prevent CPU hogging
        return True
    
    def _validate_movement(self, axis: str, position: float) -> bool:
        """
        Check if a movement would exceed limits.
        
        Args:
            axis: Axis to check ('x', 'y', or 'z')
            position: Target position
            
        Returns:
            bool: True if movement is valid, False otherwise
        """
        if axis.lower() not in self._limits:
            return True
            
        limits = self._limits[axis.lower()]
        return limits["min"] <= position <= limits["max"]