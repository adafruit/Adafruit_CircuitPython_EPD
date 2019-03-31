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
from digitalio import Direction
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
            self._rst.direction = Direction.OUTPUT

        # Setup busy pin, if we have one
        self._busy = busy_pin
        if busy_pin:
            self._busy.direction = Direction.INPUT

        # Setup dc pin (required)
        self._dc = dc_pin
        self._dc.direction = Direction.OUTPUT
        self._dc.value = False

        # Setup cs pin (required)
        self._cs = cs_pin
        self._cs.direction = Direction.OUTPUT
        self._cs.value = True

        # SPI interface (required)
        self.spi_device = spi

        self.sram = None
        if sramcs_pin:
            self.sram = mcp_sram.Adafruit_MCP_SRAM(sramcs_pin, spi)

        self._buffer1_size = self._buffer2_size = 0
        self._buffer1 = self._buffer2 = None
        self.hardware_reset()

    def display(self):
        """show the contents of the display buffer"""
        self.power_up()

        self.set_ram_address(0, 0)

        if self.sram:
            while not self.spi_device.try_lock():
                pass
            self.sram.cs_pin.value = False
            #send read command
            self.spi_device.write(bytearray([mcp_sram.Adafruit_MCP_SRAM.SRAM_READ]))
            #send start address
            self.spi_device.write(bytearray([0x00, 0x00]))
            self.spi_device.unlock()

        #first data byte from SRAM will be transfered in at the
        #same time as the EPD command is transferred out
        cmd = self.write_ram(0)

        while not self.spi_device.try_lock():
            pass
        self._dc.value = True

        if self.sram:
            xfer = bytearray([cmd])
            outbuf = bytearray(1)
            for _ in range(self._buffer1_size):
                outbuf[0] = xfer[0]
                self.spi_device.write_readinto(outbuf, xfer)
            self.sram.cs_pin.value = True
        else:
            self.spi_device.write(self._buffer1)

        self._cs.value = True
        self.spi_device.unlock()
        time.sleep(.002)


        if self.sram:
            while not self.spi_device.try_lock():
                pass
            self.sram.cs_pin.value = False
            #send read command
            self.spi_device.write(bytearray([mcp_sram.Adafruit_MCP_SRAM.SRAM_READ]))
            #send start address
            self.spi_device.write(bytearray([(self._buffer1_size >> 8), (self._buffer1_size & 0xFF)]))
            self.spi_device.unlock()

        #first data byte from SRAM will be transfered in at the
        #same time as the EPD command is transferred out
        cmd = self.write_ram(1)

        while not self.spi_device.try_lock():
            pass
        self._dc.value = True

        if self.sram:
            xfer = bytearray([cmd])
            outbuf = bytearray(1)
            for _ in range(self._buffer1_size):
                outbuf[0] = xfer[0]
                self.spi_device.write_readinto(outbuf, xfer)
            self.sram.cs_pin.value = True
        else:
            self.spi_device.write(self._buffer2)

        self._cs.value = True
        self.spi_device.unlock()
        self.update()


    def hardware_reset(self):
        # if we have a reset pin, do a hardware reset
        if self._rst:
            self._rst.value = False
            time.sleep(0.1)
            self._rst.value = True
            time.sleep(0.1)

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
            self._dc.value = True
            self.spi_device.write(data)
        if end:
            self._cs.value = True
        self.spi_device.unlock()

        return outbuf[0]


    def pixel(self, x, y, color):
        """draw a single pixel in the display buffer"""
        self._framebuf1.pixel(x, y, (color == Adafruit_EPD.BLACK) != self.black_invert)
        self._framebuf2.pixel(x, y, (color == Adafruit_EPD.RED) != self.red_invert)

    def fill(self, color):
        """fill the screen with the passed color"""
        red_fill = (color == Adafruit_EPD.RED) != self.red_invert
        black_fill = (color == Adafruit_EPD.BLACK) != self.black_invert
        if red_fill:
            red_fill = 0xFF
        if black_fill:
            black_fill = 0xFF

        if self.sram:
            self.sram.erase(0x00, self._buffer1_size, black_fill)
            self.sram.erase(self._buffer1_size, self._buffer2_size, red_fill)
        else:
            self._framebuf1.fill(black_fill)
            self._framebuf2.fill(red_fill)

    def rect(self, x, y, width, height, color):
        """draw a rectangle"""
        self._framebuf1.rect(x, y, width, height, (color == Adafruit_EPD.BLACK) != self.black_invert)
        self._framebuf2.rect(x, y, width, height, (color == Adafruit_EPD.RED) != self.red_invert)

    # pylint: disable=too-many-arguments
    def fill_rect(self, x, y, width, height, color):
        """fill a rectangle with the passed color"""
        self._framebuf1.fill_rect(x, y, width, height, (color == Adafruit_EPD.BLACK) != self.black_invert)
        self._framebuf2.fill_rect(x, y, width, height, (color == Adafruit_EPD.RED) != self.red_invert)

    def line(self, x_0, y_0, x_1, y_1, color):
        self._framebuf1.line(x_0, y_0, x_1, y_1, (color == Adafruit_EPD.BLACK) != self.black_invert)
        self._framebuf2.line(x_0, y_0, x_1, y_1, (color == Adafruit_EPD.RED) != self.red_invert)

    def text(self, string, x, y, color, *, font_name="font5x8.bin"):
        self._framebuf1.text(string, x, y, (color == Adafruit_EPD.BLACK) != self.black_invert, font_name=font_name)
        self._framebuf2.text(string, x, y, (color == Adafruit_EPD.RED) != self.red_invert, font_name=font_name)

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
        return self._framebuf1._rotation

    @rotation.setter
    def rotation(self, val):
        self._framebuf1.rotation = val
        self._framebuf2.rotation = val

    def hline(self, x, y, width, color):
        """draw a horizontal line"""
        self.fill_rect(x, y, width, 1, color)

    def vline(self, x, y, height, color):
        """draw a vertical line"""
        self.fill_rect(x, y, 1, height, color)


    def image(self, image):
        """Set buffer to value of Python Imaging Library image.  The image should
        be in RGB mode and a size equal to the display size.
        """
        if image.mode != 'RGB':
            raise ValueError('Image must be in mode RGB.')
        imwidth, imheight = image.size
        if imwidth != self.width or imheight != self.height:
            raise ValueError('Image must be same dimensions as display ({0}x{1}).' \
                .format(self.width, self.height))
        # Grab all the pixels from the image, faster than getpixel.
        pix = image.load()

        for y in iter(range(image.size[1])):
            for x in iter(range(image.size[0])):
                if x == 0:
                    x = 1
                pixel = pix[x, y]

                addr = int(((self._width - x) * self._height + y)/8)

                if pixel == (0xFF, 0, 0):
                    addr = addr + self.bw_bufsize
                current = self.sram.read8(addr)

                if pixel in ((0xFF, 0, 0), (0, 0, 0)):
                    current = current & ~(1 << (7 - y%8))
                else:
                    current = current | (1 << (7 - y%8))

                self.sram.write8(addr, current)
