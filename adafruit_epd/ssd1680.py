# SPDX-FileCopyrightText: 2018 Dean Miller for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_epd.ssd1680` - Adafruit SSD1680 - ePaper display driver
====================================================================================
CircuitPython driver for Adafruit SSD1680 display breakouts
* Author(s): Melissa LeBlanc-Williams Mikey Sklar
"""
from micropython import const
import adafruit_framebuf
from adafruit_epd.epd import Adafruit_EPD
import time

# Define all SSD1680 constants
_SSD1680_DRIVER_CONTROL = const(0x01)
_SSD1680_DATA_MODE = const(0x11)
_SSD1680_SW_RESET = const(0x12)
_SSD1680_SET_RAMXPOS = const(0x44)
_SSD1680_SET_RAMYPOS = const(0x45)
_SSD1680_WRITE_BWRAM = const(0x24)
_SSD1680_WRITE_REDRAM = const(0x26)
_SSD1680_SET_RAMXCOUNT = const(0x4E)
_SSD1680_SET_RAMYCOUNT = const(0x4F)
_SSD1680_DISP_CTRL2 = const(0x22)
_SSD1680_MASTER_ACTIVATE = const(0x20)
_SSD1680_DEEP_SLEEP = const(0x10)

class Adafruit_SSD1680(Adafruit_EPD):
    """Driver for SSD1680 ePaper display, default driver."""

    def __init__(self, width, height, spi, *, cs_pin, dc_pin, sramcs_pin, rst_pin, busy_pin):
        super().__init__(width, height, spi, cs_pin, dc_pin, sramcs_pin, rst_pin, busy_pin)

        self.cs_pin = cs_pin
        self.dc_pin = dc_pin
        self.sramcs_pin = sramcs_pin
        self.rst_pin = rst_pin
        self.busy_pin = busy_pin

        self.initialize_buffers(width, height)

    def initialize_buffers(self, width, height):
        stride = width
        if stride % 8 != 0:
            stride += 8 - stride % 8

        self._buffer1_size = int(stride * height / 8)
        self._buffer2_size = self._buffer1_size

        if self.sramcs_pin:
            self._buffer1 = self.sram.get_view(0)
            self._buffer2 = self.sram.get_view(self._buffer1_size)
        else:
            self._buffer1 = bytearray(self._buffer1_size)
            self._buffer2 = bytearray(self._buffer2_size)

        self._framebuf1 = adafruit_framebuf.FrameBuffer(
            self._buffer1, width, height, buf_format=adafruit_framebuf.MHMSB
        )
        self._framebuf2 = adafruit_framebuf.FrameBuffer(
            self._buffer2, width, height, buf_format=adafruit_framebuf.MHMSB
        )
        self.set_black_buffer(0, True)
        self.set_color_buffer(1, False)

    def busy_wait(self):
        """Wait for the display to complete its current task."""
        if self.busy_pin:
            while self.busy_pin.value:
                time.sleep(0.01)
        else:
            time.sleep(0.5)

    def power_up(self):
        """Power up sequence for SSD1680."""
        self.hardware_reset()
        self.busy_wait()
        self.command(_SSD1680_SW_RESET)
        self.busy_wait()

        self.command(_SSD1680_DRIVER_CONTROL, bytearray([self._height - 1, (self._height - 1) >> 8, 0x00]))
        self.command(_SSD1680_DATA_MODE, bytearray([0x03]))
        self.command(_SSD1680_SET_RAMXPOS, bytearray([0x01, 0x10]))
        self.command(_SSD1680_SET_RAMYPOS, bytearray([0, 0, self._height - 1, (self._height - 1) >> 8]))

    def write_ram(self, index):
        """Write to RAM for SSD1680."""
        if index == 0:
            return self.command(_SSD1680_WRITE_BWRAM, end=False)
        elif index == 1:
            return self.command(_SSD1680_WRITE_REDRAM, end=False)
        else:
            raise RuntimeError("RAM index must be 0 or 1")

    def set_ram_address(self, x, y):
        """Set RAM address location for SSD1680."""
        self.command(_SSD1680_SET_RAMXCOUNT, bytearray([x + 1]))
        self.command(_SSD1680_SET_RAMYCOUNT, bytearray([y, y >> 8]))

    def update(self):
        """Update the display from internal memory."""
        self.command(_SSD1680_DISP_CTRL2, bytearray([0xF4]))  # Full update
        self.command(_SSD1680_MASTER_ACTIVATE)
        self.busy_wait()
        if not self.busy_pin:
            time.sleep(3)  # Wait for update to complete

    def power_down(self):
        """Power down the display."""
        self.command(_SSD1680_DEEP_SLEEP, bytearray([0x01]))
        time.sleep(0.1)


class Adafruit_SSD1680Z(Adafruit_SSD1680):
    """Driver for SSD1680Z ePaper display, overriding SSD1680 settings."""

    def __init__(self, width, height, spi, *, cs_pin, dc_pin, sramcs_pin, rst_pin, busy_pin):
        super().__init__(width, height, spi, cs_pin=cs_pin, dc_pin=dc_pin,
                         sramcs_pin=sramcs_pin, rst_pin=rst_pin, busy_pin=busy_pin)

    def power_up(self):
        """Power up sequence specifically for SSD1680Z."""
        self.hardware_reset()
        self.busy_wait()
        self.command(_SSD1680_SW_RESET)
        self.busy_wait()

        self.command(_SSD1680_DRIVER_CONTROL, bytearray([self._height - 1, (self._height - 1) >> 8, 0x00]))
        self.command(_SSD1680_DATA_MODE, bytearray([0x03]))
        self.command(_SSD1680_SET_RAMXPOS, bytearray([0x00, (self._width // 8) - 1]))
        self.command(_SSD1680_SET_RAMYPOS, bytearray([0x00, 0x00, self._height - 1, (self._height - 1) >> 8]))

    def update(self):
        """Update the display specifically for SSD1680Z."""
        self.command(_SSD1680_DISP_CTRL2, bytearray([0xF7]))  # Full update for SSD1680Z
        self.command(_SSD1680_MASTER_ACTIVATE)
        self.busy_wait()
        if not self.busy_pin:
            time.sleep(3)  # Wait for update to complete
