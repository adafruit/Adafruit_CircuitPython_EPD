from Adafruit_IL91874 import *

class Adafruit_IL91874_212_104(Adafruit_IL91874_base):
	def __init__(self, rst, dc, busy, srcs=None, cs=None, spi=None):

		super(Adafruit_IL91874_212_104, self).__init__(212, 104, rst, dc, busy, srcs, cs, spi)

	def power_up(self):
		super(Adafruit_IL91874_212_104, self).power_up()
		self.command(IL91874_RESOLUTION, bytearray([0x68, 0x00, 0xD4]))
		time.sleep(.02)