# SPDX-FileCopyrightText: 2024
#
# SPDX-License-Identifier: MIT

"""
`adafruit_epd.uc8179` - Adafruit UC8179 - ePaper display driver
====================================================================================
CircuitPython driver for Adafruit UC8179 display breakouts
* Author(s): Your Name Here
"""

import time

import adafruit_framebuf
from micropython import const

from adafruit_epd.epd import Adafruit_EPD

try:
    """Needed for type annotations"""
    import typing

    from busio import SPI
    from digitalio import DigitalInOut
    from typing_extensions import Literal

except ImportError:
    pass

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_EPD.git"

# UC8179 commands
_UC8179_PANELSETTING = const(0x00)
_UC8179_POWERSETTING = const(0x01)
_UC8179_POWEROFF = const(0x02)
_UC8179_POWERON = const(0x04)
_UC8179_DEEPSLEEP = const(0x07)
_UC8179_WRITE_RAM1 = const(0x10)
_UC8179_DATASTOP = const(0x11)
_UC8179_DISPLAYREFRESH = const(0x12)
_UC8179_WRITE_RAM2 = const(0x13)
_UC8179_DUALSPI = const(0x15)
_UC8179_WRITE_VCOM = const(0x50)
_UC8179_TCON = const(0x60)
_UC8179_TRES = const(0x61)
_UC8179_GET_STATUS = const(0x71)

BUSY_WAIT = const(500)  # milliseconds


class Adafruit_UC8179(Adafruit_EPD):
    """driver class for Adafruit UC8179 ePaper display breakouts"""

    def __init__(
        self,
        width: int,
        height: int,
        spi: SPI,
        *,
        cs_pin: DigitalInOut,
        dc_pin: DigitalInOut,
        sramcs_pin: DigitalInOut,
        rst_pin: DigitalInOut,
        busy_pin: DigitalInOut,
    ) -> None:
        # Adjust height to be divisible by 8 (direct from Arduino)
        if (height % 8) != 0:
            height += 8 - (height % 8)

        super().__init__(width, height, spi, cs_pin, dc_pin, sramcs_pin, rst_pin, busy_pin)

        # Calculate buffer sizes exactly as Arduino does: width * height / 8
        self._buffer1_size = width * height // 8
        self._buffer2_size = self._buffer1_size

        if sramcs_pin:
            # Using external SRAM
            self._buffer1 = self.sram.get_view(0)
            self._buffer2 = self.sram.get_view(self._buffer1_size)
        else:
            # Using internal RAM
            self._buffer1 = bytearray(self._buffer1_size)
            self._buffer2 = bytearray(self._buffer2_size)

        # Create frame buffers
        self._framebuf1 = adafruit_framebuf.FrameBuffer(
            self._buffer1,
            width,
            height,
            buf_format=adafruit_framebuf.MHMSB,
        )
        self._framebuf2 = adafruit_framebuf.FrameBuffer(
            self._buffer2,
            width,
            height,
            buf_format=adafruit_framebuf.MHMSB,
        )

        # Set up which frame buffer is which color
        self.set_black_buffer(0, True)
        self.set_color_buffer(1, False)

        # UC8179 uses single byte transactions
        self._single_byte_tx = True

        # Default refresh delay (from Adafruit_EPD base class in Arduino)
        self.default_refresh_delay = 15  # seconds
        # pylint: enable=too-many-arguments

    def begin(self, reset: bool = True) -> None:
        """Begin communication with the display and set basic settings"""
        if reset:
            self.hardware_reset()
        self.power_down()

    def busy_wait(self) -> None:
        """Wait for display to be done with current task, either by polling the
        busy pin, or pausing"""
        if self._busy:
            # Wait for busy pin to go HIGH
            while not self._busy.value:
                self.command(_UC8179_GET_STATUS)
                time.sleep(0.1)
        else:
            # No busy pin, just wait
            time.sleep(BUSY_WAIT / 1000.0)
        # Additional delay after busy signal
        time.sleep(0.2)

    def power_up(self) -> None:
        """Power up the display in preparation for writing RAM and updating"""
        self.hardware_reset()

        # Power setting
        self.command(
            _UC8179_POWERSETTING,
            bytearray(
                [
                    0x07,  # VGH=20V
                    0x07,  # VGL=-20V
                    0x3F,  # VDH=15V
                    0x3F,  # VDL=-15V
                ]
            ),
        )

        # Power on
        self.command(_UC8179_POWERON)
        time.sleep(0.1)  # 100ms delay
        self.busy_wait()

        # Panel setting
        self.command(_UC8179_PANELSETTING, bytearray([0b010111]))  # BW OTP LUT

        # Resolution setting
        self.command(
            _UC8179_TRES,
            bytearray(
                [self._width >> 8, self._width & 0xFF, self._height >> 8, self._height & 0xFF]
            ),
        )

        # Dual SPI setting
        self.command(_UC8179_DUALSPI, bytearray([0x00]))

        # VCOM setting
        self.command(_UC8179_WRITE_VCOM, bytearray([0x10, 0x07]))

        # TCON setting
        self.command(_UC8179_TCON, bytearray([0x22]))

    def power_down(self) -> None:
        """Power down the display - required when not actively displaying!"""
        self.command(_UC8179_POWEROFF)
        self.busy_wait()

        # Only deep sleep if we have a reset pin to wake it up
        if self._rst:
            self.command(_UC8179_DEEPSLEEP, bytearray([0x05]))
        time.sleep(0.1)

    def update(self) -> None:
        """Update the display from internal memory"""
        self.command(_UC8179_DISPLAYREFRESH)
        time.sleep(0.1)  # 100ms delay
        self.busy_wait()

        if not self._busy:
            # If no busy pin, use default refresh delay
            time.sleep(self.default_refresh_delay)

    def write_ram(self, index: Literal[0, 1]) -> int:
        """Send the one byte command for starting the RAM write process. Returns
        the byte read at the same time over SPI. index is the RAM buffer, can be
        0 or 1 for tri-color displays."""
        if index == 0:
            return self.command(_UC8179_WRITE_RAM1, end=False)
        if index == 1:
            return self.command(_UC8179_WRITE_RAM2, end=False)
        raise RuntimeError("RAM index must be 0 or 1")

    def set_ram_address(self, x: int, y: int) -> None:  # noqa: PLR6301, F841
        """Set the RAM address location, not used on this chipset but required by
        the superclass"""
        # Not used in UC8179 chip
        pass

    def set_ram_window(self, x1: int, y1: int, x2: int, y2: int) -> None:  # noqa: PLR6301, F841
        """Set the RAM window, not used on this chipset but required by
        the superclass"""
        # Not used in UC8179 chip
        pass
