from base import MotorDriver, MotorStatus, MotorConnectionError, MotorMovementError
from typing import Tuple, Optional, Dict, Any, List
import time
from thorlabs_apt_device import BSC
import re
import math

"""
Module defines a BSC203 motor class designed to interface with the thorlabs bsc203 steper motor controller.

    - Handles connection, movement in xyz, position limits, simple state tracking  

"""

class BSC203MotorDriver(MotorDriver):
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._device = None
        self._serial_port = self._config.get("serial_port", "COM3")
        self._num_axes = self._config.get("num_axes", 3)

    def connect(self) -> bool:
        try:
            self._device = BSC(serial_port=self._serial_port, x=self._num_axes, home=False)
            self._device.identify()
            self._status = MotorStatus.IDLE
            return True
        except Exception as e:
            self._status = MotorStatus.ERROR
            self._error_message = f"Connection failed: {e}"
            raise MotorConnectionError(self._error_message)

    def disconnect(self) -> bool:
        try:
            if self._device:
                self._device.close()
                self._device = None
            self._status = MotorStatus.DISCONNECTED
            return True
        except Exception as e:
            self._status = MotorStatus.ERROR
            self._error_message = f"Disconnection failed: {e}"
            return False

    def move_relative(self, dx=0.0, dy=0.0, dz=0.0,
                      speed: Optional[Dict[str, float]] = None) -> bool:
        try:
            if not self._device:
                raise MotorConnectionError("Motor not connected.")

            moves = {"x": dx, "y": dy, "z": dz}
            bays = {"x": 0, "y": 1, "z": 2}
            self._status = MotorStatus.MOVING

            for axis, delta in moves.items():
                if abs(delta) > 0:
                    new_pos = self._axes[axis] + delta
                    if not self._validate_movement(axis, new_pos):
                        raise MotorMovementError(f"Movement on {axis}-axis exceeds limits.")

                    self._device.move_relative(distance=int(delta * 1000), bay=bays[axis], channel=0)
                    self._axes[axis] = new_pos

            self._status = MotorStatus.IDLE
            return True
        except Exception as e:
            self._status = MotorStatus.ERROR
            self._error_message = f"Relative move failed: {e}"
            raise MotorMovementError(self._error_message)

    def move_absolute(self, x=None, y=None, z=None,
                      speed: Optional[Dict[str, float]] = None) -> bool:
        try:
            if not self._device:
                raise MotorConnectionError("Motor not connected.")

            targets = {"x": x, "y": y, "z": z}
            bays = {"x": 0, "y": 1, "z": 2}
            self._status = MotorStatus.MOVING

            for axis, target in targets.items():
                if target is not None:
                    if not self._validate_movement(axis, target):
                        raise MotorMovementError(f"Movement on {axis}-axis exceeds limits.")

                    delta = target - self._axes[axis]
                    self._device.move_relative(distance=int(delta * 1000), bay=bays[axis], channel=0)
                    self._axes[axis] = target

            self._status = MotorStatus.IDLE
            return True
        except Exception as e:
            self._status = MotorStatus.ERROR
            self._error_message = f"Absolute move failed: {e}"
            raise MotorMovementError(self._error_message)

    def get_position(self) -> Tuple[float, float, float]:
        return (self._axes["x"], self._axes["y"], self._axes["z"])

    def home(self, axes: Optional[List[str]] = None) -> bool:
        # The Thorlabs BSC203 does not support automatic homing in this wrapper.
        # You may implement this manually using known movement logic if needed.
        raise NotImplementedError("Homing not implemented for BSC203 driver.")

    def stop(self, emergency: bool = False) -> bool:
        # The Thorlabs API used does not expose a direct stop method, so this is a no-op
        return True