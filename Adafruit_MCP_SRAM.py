import time
from micropython import const

from adafruit_bus_device.spi_device import SPIDevice
import busio
from board import *

SRAM_READ = const(0x03)
SRAM_WRITE = const(0x02)
SRAM_RDSR = const(0x05)
SRAM_WRSR = const(0x01)

SRAM_SEQUENTIAL_MODE = const(1 << 6)

class Adafruit_MCP_SRAM:

	def __init__(self, cs, spi):
		# Handle hardware SPI
		self.spi_device = spi

		with self.spi_device as spi:
			spi.write(bytearray([0xFF, 0xFF, 0xFF]))

	def write(self, addr, buf, reg=SRAM_WRITE):
		c = bytearray([reg, (addr >> 16) & 0xFF, (addr >> 8) & 0xFF, addr & 0xFF] + bytearray(buf))

		with self.spi_device as spi:
			spi.write(c)

	def read(self, addr, length, reg=SRAM_READ):
		c = bytearray([reg, (addr >> 16) & 0xFF, (addr >> 8) & 0xFF, addr & 0xFF] + bytearray(buf))

		buf = bytearray(length)
		with self.spi_device as spi:
			spi.readinto(buf)

		return buf

	def read8(self, addr, reg=SRAM_READ):
		return ord(self.read(addr, 1, reg)[0])

	def read16(self, addr, reg=SRAM_READ):
		buf = self.read(addr, 2, reg)
		return (buf[0] << 8 | buf[1])

	def write8(self, addr, value, reg=SRAM_WRITE):
		self.write(addr, [value], reg)

	def write16(self, addr, value, reg=SRAM_WRITE):
		self.write(addr, [value >> 8, value], reg)

	def erase(self, addr, length, value):
		pos = 0
		while pos < length:
			buf = [value] * min(64, length - pos)
			self.write(addr, buf)
			addr = addr + len(buf)
			pos = pos + len(buf)
