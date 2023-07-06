# SPDX-FileCopyrightText: 2018 Dean Miller for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_epd.EK79686` - Adafruit EK79686 - ePaper display driver
====================================================================================
CircuitPython driver for Adafruit EK79686 display breakouts
* Author(s): Melissa LeBlanc-Williams
"""

import time
from micropython import const
import adafruit_framebuf
from adafruit_epd.epd import Adafruit_EPD

try:
    "Needed for type annotations"
    import typing  # pylint: disable=unused-import
    from typing_extensions import Literal
    from busio import SPI
    from digitalio import DigitalInOut

except ImportError:
    pass

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_EPD.git"

_EK79686_PANEL_SETTING = const(0x00)
_EK79686_POWER_SETTING = const(0x01)
_EK79686_POWER_OFF = const(0x02)
_EK79686_POWER_OFF_SEQUENCE = const(0x03)
_EK79686_POWER_ON = const(0x04)
_EK79686_POWER_ON_MEASURE = const(0x05)
_EK79686_BOOSTER_SOFT_START = const(0x06)
_EK79686_DEEP_SLEEP = const(0x07)
_EK79686_DTM1 = const(0x10)
_EK79686_DATA_STOP = const(0x11)
_EK79686_DISPLAY_REFRESH = const(0x12)
_EK79686_DTM2 = const(0x13)
_EK79686_PDTM1 = const(0x14)
_EK79686_PDTM2 = const(0x15)
_EK79686_PDRF = const(0x16)
_EK79686_LUT1 = const(0x20)
_EK79686_LUTWW = const(0x21)
_EK79686_LUTBW = const(0x22)
_EK79686_LUTWB = const(0x23)
_EK79686_LUTBB = const(0x24)
_EK79686_PLL = const(0x30)
_EK79686_CDI = const(0x50)
_EK79686_RESOLUTION = const(0x61)
_EK79686_VCM_DC_SETTING = const(0x82)


class Adafruit_EK79686(Adafruit_EPD):
    """driver class for Adafruit EK79686 ePaper display breakouts"""

    # pylint: disable=too-many-arguments
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
        busy_pin: DigitalInOut
    ) -> None:
        super().__init__(
            width, height, spi, cs_pin, dc_pin, sramcs_pin, rst_pin, busy_pin
        )

        self._buffer1_size = int(width * height / 8)
        self._buffer2_size = int(width * height / 8)

        if sramcs_pin:
            self._buffer1 = self.sram.get_view(0)
            self._buffer2 = self.sram.get_view(self._buffer1_size)
        else:
            self._buffer1 = bytearray((width * height) // 8)
            self._buffer2 = bytearray((width * height) // 8)
        # since we have *two* framebuffers - one for red and one for black
        # we dont subclass but manage manually
        self._framebuf1 = adafruit_framebuf.FrameBuffer(
            self._buffer1, width, height, buf_format=adafruit_framebuf.MHMSB
        )
        self._framebuf2 = adafruit_framebuf.FrameBuffer(
            self._buffer2, width, height, buf_format=adafruit_framebuf.MHMSB
        )
        self.set_black_buffer(0, True)
        self.set_color_buffer(1, False)
        self._single_byte_tx = False

    def begin(self, reset: bool = True) -> None:
        """Begin communication with the display and set basic settings"""
        if reset:
            self.hardware_reset()

        self.power_down()

    def busy_wait(self) -> None:
        """Wait for display to be done with current task, either by polling the
        busy pin, or pausing"""
        if self._busy:
            while not self._busy.value:
                time.sleep(0.01)
        else:
            time.sleep(0.5)

    def power_up(self) -> None:
        """Power up the display in preparation for writing RAM and updating"""
        self.hardware_reset()
        time.sleep(0.2)

        self.command(_EK79686_PANEL_SETTING, bytearray([0x0F]))  # LUT from OTP 176x264
        self.command(0x4D, bytearray([0xAA]))  # FITI cmd (???)
        self.command(0x87, bytearray([0x28]))
        self.command(0x84, bytearray([0x00]))
        self.command(0x83, bytearray([0x05]))
        self.command(0xA8, bytearray([0xDF]))
        self.command(0xA9, bytearray([0x05]))
        self.command(0xB1, bytearray([0xE8]))
        self.command(0xAB, bytearray([0xA1]))
        self.command(0xB9, bytearray([0x10]))
        self.command(0x88, bytearray([0x80]))
        self.command(0x90, bytearray([0x02]))
        self.command(0x86, bytearray([0x15]))
        self.command(0x91, bytearray([0x8D]))
        self.command(0xAA, bytearray([0x0F]))
        self.command(_EK79686_POWER_ON)
        self.busy_wait()

    def power_down(self) -> None:
        """Power down the display - required when not actively displaying!"""
        self.command(_EK79686_POWER_OFF, bytearray([0x17]))
        self.busy_wait()

        if self._rst:  # Only deep sleep if we can get out of it
            self.command(_EK79686_DEEP_SLEEP, bytearray([0xA5]))

    def update(self) -> None:
        """Update the display from internal memory"""
        self.command(_EK79686_DISPLAY_REFRESH)
        self.busy_wait()
        if not self._busy:
            time.sleep(16)  # wait 16 seconds

    def write_ram(self, index: Literal[0, 1]) -> int:
        """Send the one byte command for starting the RAM write process. Returns
        the byte read at the same time over SPI. index is the RAM buffer, can be
        0 or 1 for tri-color displays."""
        if index == 0:
            return self.command(_EK79686_DTM1, end=False)
        if index == 1:
            return self.command(_EK79686_DTM2, end=False)
        raise RuntimeError("RAM index must be 0 or 1")

    def set_ram_address(
        self, x: int, y: int
    ) -> None:  # pylint: disable=unused-argument, no-self-use
        """Set the RAM address location, not used on this chipset but required by
        the superclass"""
        return  # on this chip it does nothing
