import time
from Adafruit_MCP_SRAM import *
import digitalio
import busio
from board import *

from adafruit_bus_device.spi_device import SPIDevice

class Adafruit_EPD(object):
	"""Base class for EPD displays
	"""

	def __init__(self, width, height, rst, dc, busy, srcs=None, cs=None,
				 spi=None):
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

		self.sram = Adafruit_MCP_SRAM(cs=srcs, spi=spi)

	def begin(self, reset=True):
		self._cs.value = True
		self._dc.value = False

		if reset:
			self._rst.value = False
			time.sleep(.1)
			self._rst.value = True
			time.sleep(.1)

		while self._busy.value == True:
			pass

	def command(self, c, data=None, end=True):
		"""Send command byte to display."""
		self._cs.value = True
		self._dc.value = False
		self._cs.value = False	
		with self.spi_device as spi:
			spi.write(bytearray([c]))

		if data is not None:
			self.data(data)

		elif end:
			self._cs.value = True

	def data(self, d):
		"""Send data to display."""
		self._dc.value = True
		with self.spi_device as spi:
			spi.write(d)
		self._cs.value = True