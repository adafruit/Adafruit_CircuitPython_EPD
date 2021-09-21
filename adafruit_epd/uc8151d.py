# SPDX-FileCopyrightText: 2018 Dean Miller for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_epd.uc8151d` - Adafruit UC8151D - ePaper display driver
====================================================================================
CircuitPython driver for Adafruit UC8151D display breakouts
* Author(s): Dean Miller
"""

import time
from micropython import const
import adafruit_framebuf
from adafruit_epd.epd import Adafruit_EPD

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_EPD.git"

_UC8151D_PANEL_SETTING = const(0x00)
_UC8151D_POWER_SETTING = const(0x01)
_UC8151D_POWER_OFF = const(0x02)
_UC8151D_POWER_OFF_SEQUENCE = const(0x03)
_UC8151D_POWER_ON = const(0x04)
_UC8151D_POWER_ON_MEASURE = const(0x05)
_UC8151D_BOOSTER_SOFT_START = const(0x06)
_UC8151D_DEEP_SLEEP = const(0x07)
_UC8151D_DTM1 = const(0x10)
_UC8151D_DATA_STOP = const(0x11)
_UC8151D_DISPLAY_REFRESH = const(0x12)
_UC8151D_DTM2 = const(0x13)
_UC8151D_AUTO = const(0x17)
_UC8151D_LUTOPT = const(0x2A)
_UC8151D_PLL = const(0x30)
_UC8151D_TSC = const(0x40)
_UC8151D_TSE = const(0x41)
_UC8151D_TSW = const(0x42)
_UC8151D_TSR = const(0x43)
_UC8151D_PBC = const(0x44)
_UC8151D_CDI = const(0x50)
_UC8151D_LPD = const(0x51)
_UC8151D_TRES = const(0x65)
_UC8151D_GSST = const(0x70)
_UC8151D_REV = const(0x70)
_UC8151D_FLG = const(0x71)
_UC8151D_AMV = const(0x80)
_UC8151D_VV = const(0x81)
_UC8151D_VCM_DC_SETTING = const(0x82)
_UC8151D_PTL = const(0x90)
_UC8151D_PTIN = const(0x91)
_UC8151D_PTOUT = const(0x92)
_UC8151D_PGM = const(0xA0)
_UC8151D_APG = const(0xA1)
_UC8151D_ROTP = const(0xA2)
_UC8151D_CCSET = const(0xE0)
_UC8151D_PWS = const(0xE3)
_UC8151D_LVSEL = const(0xE4)
_UC8151D_TSSET = const(0xE5)


class Adafruit_UC8151D(Adafruit_EPD):
    """driver class for Adafruit UC8151D ePaper display breakouts"""

    # pylint: disable=too-many-arguments
    def __init__(
        self, width, height, spi, *, cs_pin, dc_pin, sramcs_pin, rst_pin, busy_pin
    ):
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
        self.set_color_buffer(1, True)
        # pylint: enable=too-many-arguments

    def begin(self, reset=True):
        """Begin communication with the display and set basic settings"""
        if reset:
            self.hardware_reset()
        self.power_down()

    def busy_wait(self):
        """Wait for display to be done with current task, either by polling the
        busy pin, or pausing"""
        if self._busy:
            while not self._busy.value:
                time.sleep(0.01)
        else:
            time.sleep(0.5)

    def power_up(self):
        """Power up the display in preparation for writing RAM and updating"""
        self.hardware_reset()
        self.busy_wait()

        self.command(_UC8151D_POWER_ON)

        self.busy_wait()
        time.sleep(0.01)

        self.command(_UC8151D_PANEL_SETTING, bytearray([0x1F]))
        self.command(_UC8151D_CDI, bytearray([0x97]))
        time.sleep(0.05)

    def power_down(self):
        """Power down the display - required when not actively displaying!"""
        self.command(_UC8151D_CDI, bytearray([0xF7]))
        self.command(_UC8151D_POWER_OFF)
        self.busy_wait()
        self.command(_UC8151D_DEEP_SLEEP, bytearray([0xA5]))

    def update(self):
        """Update the display from internal memory"""
        self.command(_UC8151D_DISPLAY_REFRESH)
        time.sleep(0.1)
        self.busy_wait()
        if not self._busy:
            time.sleep(15)  # wait 15 seconds

    def write_ram(self, index):
        """Send the one byte command for starting the RAM write process. Returns
        the byte read at the same time over SPI. index is the RAM buffer, can be
        0 or 1 for tri-color displays."""
        if index == 0:
            return self.command(_UC8151D_DTM1, end=False)
        if index == 1:
            return self.command(_UC8151D_DTM2, end=False)
        raise RuntimeError("RAM index must be 0 or 1")

    def set_ram_address(self, x, y):  # pylint: disable=unused-argument, no-self-use
        """Set the RAM address location, not used on this chipset but required by
        the superclass"""
        return  # on this chip it does nothing
