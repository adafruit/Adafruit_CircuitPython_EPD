# SPDX-FileCopyrightText: 2023 Liz Clark for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_epd.ACEP` - Adafruit ACEP - ePaper display driver
====================================================================================
CircuitPython driver for Adafruit ACEP display breakouts
* Author(s): Dean Miller
"""

import time
from micropython import const
import adafruit_framebuf
from adafruit_epd.epd import Adafruit_EPD

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_EPD.git"

_ACEP_PANEL_SETTING = const(0x00)
_ACEP_POWER_SETTING = const(0x01)
_ACEP_POWER_OFF = const(0x02)
_ACEP_POWER_OFF_SEQUENCE = const(0x03)
_ACEP_POWER_ON = const(0x04)
_ACEP_BOOSTER_SOFT_START = const(0x06)
_ACEP_DEEP_SLEEP = const(0x07)
_ACEP_DTM = const(0x10)
_ACEP_DISPLAY_REFRESH = const(0x12)
_ACEP_PLL = const(0x30)
_ACEP_TSE = const(0x40)
_ACEP_CDI = const(0x50)
_ACEP_TCON = const(0x60)
_ACEP_RESOLUTION = const(0x61)
_ACEP_PWS = const(0xE3)


class Adafruit_ACEP(Adafruit_EPD):
    """driver class for Adafruit ACEP ePaper display breakouts"""

    # pylint: disable=too-many-arguments
    def __init__(
        self, width, height, spi, *, cs_pin, dc_pin, sramcs_pin, rst_pin, busy_pin
    ):
        super().__init__(
            width, height, spi, cs_pin, dc_pin, sramcs_pin, rst_pin, busy_pin
        )

        if (height % 8) != 0:
            height += 8 - (height % 8)

        self._buffer1_size = int(width * height / 2)
        self._buffer2_size = 0

        if sramcs_pin:
            self._buffer1 = 0
            self._buffer2 = 0
        else:
            self._buffer1 = bytearray(self._buffer1_size)
            self._buffer2 = self._buffer1

        self._framebuf1 = adafruit_framebuf.FrameBuffer(
            self._buffer1, width, height, buf_format=adafruit_framebuf.MHMSB
        )

        self.set_black_buffer(0, True)
        self.set_color_buffer(0, True)
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
                time.sleep(0.1)
        else:
            time.sleep(0.5)

    def power_up(self):
        """Power up the display in preparation for writing RAM and updating"""
        self.hardware_reset()
        time.sleep(0.2)
        self.busy_wait()

        time.sleep(0.1)
        self.command(_ACEP_PANEL_SETTING, bytearray([0xEF, 0x08]))
        self.command(_ACEP_POWER_SETTING, bytearray([0x37, 0x00, 0x23, 0x23]))
        self.command(_ACEP_POWER_OFF_SEQUENCE, bytearray([0x00]))
        self.command(_ACEP_BOOSTER_SOFT_START, bytearray([0xC7, 0xC7, 0x1D]))
        self.command(_ACEP_PLL, bytearray([0x3C]))
        self.command(_ACEP_TSE, bytearray([0x00]))
        self.command(_ACEP_CDI, bytearray([0x37]))
        self.command(_ACEP_TCON, bytearray([0x22]))
        self.command(_ACEP_RESOLUTION, bytearray([0x02, 0x58, 0x01, 0xC0]))
        self.command(_ACEP_PWS, bytearray([0xAA]))
        time.sleep(0.1)
        self.command(_ACEP_CDI, bytearray([0x37]))

        self.command(_ACEP_RESOLUTION, bytearray([0x02, 0x58, 0x01, 0xC0]))
        time.sleep(0.1)

    def power_down(self):
        """Power down the display - required when not actively displaying!"""
        time.sleep(1)

        self.command(_ACEP_DEEP_SLEEP, bytearray([0xA5]))

        time.sleep(0.1)

    def update(self):
        """Update the display from internal memory"""
        self.command(_ACEP_POWER_ON)
        self.busy_wait()
        self.command(_ACEP_DISPLAY_REFRESH, bytearray([0x01, 0x00]))
        self.busy_wait()
        self.command(_ACEP_POWER_OFF)
        if not self._busy:
            time.sleep(15)  # wait 15 seconds
        else:
            self.busy_wait()

    def write_ram(self, index):
        """Send the one byte command for starting the RAM write process. Returns
        the byte read at the same time over SPI. index is the RAM buffer, can be
        0 or 1 for tri-color displays."""
        # self.command(_ACEP_DTM, end=False)
        if index == 0:
            return self.command(_ACEP_DTM, end=False)
        if index == 1:
            return self.command(_ACEP_DTM, end=False)
        raise RuntimeError("RAM index must be 0 or 1")

    def set_ram_address(self, x, y):  # pylint: disable=unused-argument, no-self-use
        """Set the RAM address location, not used on this chipset but required by
        the superclass"""
        return  # on this chip it does nothing
