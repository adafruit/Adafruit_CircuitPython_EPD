import time
from Adafruit_EPD import mcp_sram
import digitalio
import busio
from board import *

class Adafruit_EPD(object):
	"""Base class for EPD displays
	"""
	BLACK = 0
	WHITE = 1
	INVERSE = 2
	RED = 3
	DARK = 4
	LIGHT = 5

	def __init__(self, width, height, rst, dc, busy, srcs, cs,
				 spi):
		self.width = width
		self.height = height

		 # Setup reset pin.
		self._rst = rst
		self._rst.direction = digitalio.Direction.OUTPUT

		 # Setup busy pin.
		self._busy = busy
		self._busy.direction = digitalio.Direction.INPUT

		# Setup dc pin.
		self._dc = dc
		self._dc.direction = digitalio.Direction.OUTPUT

		# Setup cs pin.
		self._cs = cs
		self._cs.direction = digitalio.Direction.OUTPUT

		self.spi_device = spi

		self.sram = mcp_sram.Adafruit_MCP_SRAM(srcs, spi)

	def begin(self, reset=True):
		self._cs.value = True
		self._dc.value = False

		if reset:
			self._rst.value = False
			time.sleep(.1)
			self._rst.value = True
			time.sleep(.1)

	def command(self, c, data=None, end=True):
		"""Send command byte to display."""
		self._cs.value = True
		self._dc.value = False
		self._cs.value = False
		outbuf = bytearray(1)

		while not self.spi_device.try_lock():
			pass
		self.spi_device.write_readinto(bytearray([c]), outbuf)

		if data is not None:
			self.data(data)

		elif end:
			self._cs.value = True

		self.spi_device.unlock()
		return outbuf[0]

	def data(self, d):
		"""Send data to display."""
		self._dc.value = True
		self.spi_device.write(d)
		self._cs.value = True
		self.spi_device.unlock()