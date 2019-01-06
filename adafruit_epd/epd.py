# The MIT License (MIT)
#
# Copyright (c) 2018 Dean Miller for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`adafruit_epd.epd` - Adafruit EPD - ePaper display driver
====================================================================================
CircuitPython driver for Adafruit ePaper display breakouts
* Author(s): Dean Miller
"""

import time
import digitalio
import adafruit_framebuf
from adafruit_epd import mcp_sram

class Adafruit_EPD:
    """Base class for EPD displays
    """
    BLACK = 0
    WHITE = 1
    INVERSE = 2
    RED = 3
    DARK = 4
    LIGHT = 5

    # pylint: disable=too-many-arguments
    def __init__(self, width, height, spi, cs_pin, dc_pin, sramcs_pin, rst_pin, busy_pin):
        # pylint: enable=too-many-arguments
        self._width = width
        self._height = height

        # Setup reset pin, if we have one
        self._rst = rst_pin
        if rst_pin:
            self._rst.direction = digitalio.Direction.OUTPUT

        # Setup busy pin, if we have one
        self._busy = busy_pin
        if busy_pin:
            self._busy.direction = digitalio.Direction.INPUT

        # Setup dc pin (required)
        self._dc = dc_pin
        self._dc.direction = digitalio.Direction.OUTPUT
        self._dc.value = False

        # Setup cs pin (required)
        self._cs = cs_pin
        self._cs.direction = digitalio.Direction.OUTPUT
        self._cs.value = True

        # SPI interface (required)
        self.spi_device = spi

        if sramcs_pin:
            self.sram = mcp_sram.Adafruit_MCP_SRAM(sramcs_pin, spi)
        else:
            self.sram = None
            self._bw_buffer = bytearray((width * height) // 8)
            self._red_buffer = bytearray((width * height) // 8)
            # since we have *two* framebuffers - one for red and one for black, we dont subclass but manage manually
            self._red_framebuf = adafruit_framebuf.FrameBuffer(self._red_buffer, width, height, buf_format=adafruit_framebuf.MHMSB)
            self._bw_framebuf = adafruit_framebuf.FrameBuffer(self._bw_buffer, width, height, buf_format=adafruit_framebuf.MHMSB)

        # if we hav ea reset pin, do a hardware reset
        if self._rst:
            self._rst.value = False
            time.sleep(.1)
            self._rst.value = True
            time.sleep(.1)


    def command(self, cmd, data=None, end=True):
        """Send command byte to display."""
        self._cs.value = True
        self._dc.value = False
        self._cs.value = False
        outbuf = bytearray(1)

        while not self.spi_device.try_lock():
            pass
        self.spi_device.write_readinto(bytearray([cmd]), outbuf)

        if data is not None:
            self.data(data)
        else:
            self.spi_device.unlock()

        if end:
            self._cs.value = True

        return outbuf[0]

    def data(self, dat):
        """Send data to display."""
        self._dc.value = True
        self.spi_device.write(dat)
        self._cs.value = True
        self.spi_device.unlock()

    def fill(self, color):
        #This should be overridden in the subclass
        self._bw_framebuf.fill((color == Adafruit_EPD.BLACK) != self.black_invert)
        self._red_framebuf.fill((color == Adafruit_EPD.RED) != self.red_invert)

    def pixel(self, x, y, color=None):
        """This should be overridden in the subclass"""
        self._bw_framebuf.pixel(x, y, (color == Adafruit_EPD.BLACK) != self.black_invert)
        self._red_framebuf.pixel(x, y, (color == Adafruit_EPD.RED) != self.red_invert)

    def rect(self, x, y, width, height, color):
        """draw a rectangle"""
        self._bw_framebuf.rect(x, y, width, height, (color == Adafruit_EPD.BLACK) != self.black_invert)
        self._red_framebuf.rect(x, y, width, height, (color == Adafruit_EPD.RED) != self.red_invert)

    # pylint: disable=too-many-arguments
    def fill_rect(self, x, y, width, height, color):
        """fill a rectangle with the passed color"""
        self._bw_framebuf.fill_rect(x, y, width, height, (color == Adafruit_EPD.BLACK) != self.black_invert)
        self._red_framebuf.fill_rect(x, y, width, height, (color == Adafruit_EPD.RED) != self.red_invert)

    def line(self, x_0, y_0, x_1, y_1, color):
        self._bw_framebuf.line(x_0, y_0, x_1, y_1, (color == Adafruit_EPD.BLACK) != self.black_invert)
        self._red_framebuf.line(x_0, y_0, x_1, y_1, (color == Adafruit_EPD.RED) != self.red_invert)

    def text(self, string, x, y, color, *, font_name="font5x8.bin"):
        self._bw_framebuf.text(string, x, y, (color == Adafruit_EPD.BLACK) != self.black_invert, font_name=font_name)
        self._red_framebuf.text(string, x, y, (color == Adafruit_EPD.RED) != self.red_invert, font_name=font_name)

    @property
    def width(self):
        if self.rotation in (0, 2):
            return self._width
        return self._height

    @property
    def height(self):
        if self.rotation in (0, 2):
            return self._height
        return self._width

    @property
    def rotation(self):
        return self._bw_framebuf._rotation

    @rotation.setter
    def rotation(self, val):
        self._bw_framebuf.rotation = val
        self._red_framebuf.rotation = val

    def hline(self, x, y, width, color):
        """draw a horizontal line"""
        self.fill_rect(x, y, width, 1, color)

    def vline(self, x, y, height, color):
        """draw a vertical line"""
        self.fill_rect(x, y, 1, height, color)
