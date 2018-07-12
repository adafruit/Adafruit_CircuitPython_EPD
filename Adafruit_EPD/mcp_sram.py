import time
from micropython import const
import digitalio

from adafruit_bus_device.spi_device import SPIDevice
import busio
from board import *

SRAM_SEQUENTIAL_MODE = const(1 << 6)

class Adafruit_MCP_SRAM:

	SRAM_READ = 0x03
	SRAM_WRITE = 0x02
	SRAM_RDSR = 0x05
	SRAM_WRSR = 0x01

	def __init__(self, cs, spi):
		# Handle hardware SPI
		self.spi_device = spi
		self.cs = cs

		self.cs.direction = digitalio.Direction.OUTPUT
		while not self.spi_device.try_lock():
			pass
		self.cs.value = False
		self.spi_device.write(bytearray([Adafruit_MCP_SRAM.SRAM_WRSR, 0x43]))
		self.cs.value = True
		self.spi_device.unlock()

	def write(self, addr, buf, reg=SRAM_WRITE):
		c = bytearray([reg, (addr >> 8) & 0xFF, addr & 0xFF] + buf)

		while not self.spi_device.try_lock():
			pass
		self.cs.value = False
		self.spi_device.write(c)
		self.cs.value = True
		self.spi_device.unlock()

	def read(self, addr, length, reg=SRAM_READ):
		c = bytearray([reg, (addr >> 8) & 0xFF, addr & 0xFF])
		
		buf = bytearray(length)
		while not self.spi_device.try_lock():
			pass
		self.cs.value = False
		self.spi_device.write(c)
		self.spi_device.readinto(buf)
		self.cs.value = True
		self.spi_device.unlock()
		return buf

	def read8(self, addr, reg=SRAM_READ):
		return self.read(addr, 1, reg)[0]

	def read16(self, addr, reg=SRAM_READ):
		buf = self.read(addr, 2, reg)
		return (buf[0] << 8 | buf[1])

	def write8(self, addr, value, reg=SRAM_WRITE):
		self.write(addr, [value], reg)

	def write16(self, addr, value, reg=SRAM_WRITE):
		self.write(addr, [value >> 8, value], reg)

	def erase(self, addr, length, value):
		c = bytearray([Adafruit_MCP_SRAM.SRAM_WRITE, (addr >> 8) & 0xFF, addr & 0xFF])

		while not self.spi_device.try_lock():
			pass
		self.cs.value = False
		self.spi_device.write(c)
		for x in range(length):
			self.spi_device.write(bytearray([value]))
		self.cs.value = True
		self.spi_device.unlock()
