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
`adafruit_epd.mcp_sram` - Adafruit MCP SRAM - sram driver
====================================================================================
CircuitPython driver for Microchip SRAM chips
* Author(s): Dean Miller
"""

from micropython import const
import digitalio

SRAM_SEQUENTIAL_MODE = const(1 << 6)

class Adafruit_MCP_SRAM:
    """supporting class for communicating with
    Microchip SRAM chips"""
    SRAM_READ = 0x03
    SRAM_WRITE = 0x02
    SRAM_RDSR = 0x05
    SRAM_WRSR = 0x01

    def __init__(self, cs_pin, spi):
        # Handle hardware SPI
        self.spi_device = spi
        self.cs_pin = cs_pin

        self.cs_pin.direction = digitalio.Direction.OUTPUT
        while not self.spi_device.try_lock():
            pass
        self.cs_pin.value = False
        self.spi_device.write(bytearray([Adafruit_MCP_SRAM.SRAM_WRSR, 0x43]))
        self.cs_pin.value = True
        self.spi_device.unlock()

    def write(self, addr, buf, reg=SRAM_WRITE):
        """write the passed buffer to the passed address"""
        cmd = bytearray([reg, (addr >> 8) & 0xFF, addr & 0xFF] + buf)

        while not self.spi_device.try_lock():
            pass
        self.cs_pin.value = False
        self.spi_device.write(cmd)
        self.cs_pin.value = True
        self.spi_device.unlock()

    def read(self, addr, length, reg=SRAM_READ):
        """read passed number of bytes at the passed address"""
        cmd = bytearray([reg, (addr >> 8) & 0xFF, addr & 0xFF])

        buf = bytearray(length)
        while not self.spi_device.try_lock():
            pass
        self.cs_pin.value = False
        self.spi_device.write(cmd)
        self.spi_device.readinto(buf)
        self.cs_pin.value = True
        self.spi_device.unlock()
        return buf

    def read8(self, addr, reg=SRAM_READ):
        """read a single byte at the passed address"""
        return self.read(addr, 1, reg)[0]

    def read16(self, addr, reg=SRAM_READ):
        """read 2 bytes at the passed address"""
        buf = self.read(addr, 2, reg)
        return buf[0] << 8 | buf[1]

    def write8(self, addr, value, reg=SRAM_WRITE):
        """write a single byte at the passed address"""
        self.write(addr, [value], reg)

    def write16(self, addr, value, reg=SRAM_WRITE):
        """write 2 bytes at the passed address"""
        self.write(addr, [value >> 8, value], reg)

    def erase(self, addr, length, value):
        """erase the passed number of bytes starting at the passed address"""
        cmd = bytearray([Adafruit_MCP_SRAM.SRAM_WRITE, (addr >> 8) & 0xFF, addr & 0xFF])

        while not self.spi_device.try_lock():
            pass
        self.cs_pin.value = False
        self.spi_device.write(cmd)
        for _ in range(length):
            self.spi_device.write(bytearray([value]))
        self.cs_pin.value = True
        self.spi_device.unlock()
