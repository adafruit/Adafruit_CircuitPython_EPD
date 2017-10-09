from Adafruit_EPD import *
from micropython import const

IL91874_PANEL_SETTING = const(0x00)
IL91874_POWER_SETTING = const(0x01)
IL91874_POWER_OFF = const(0x02)
IL91874_POWER_OFF_SEQUENCE = const(0x03)
IL91874_POWER_ON = const(0x04)
IL91874_POWER_ON_MEASURE = const(0x05)
IL91874_BOOSTER_SOFT_START = const(0x06)
IL91874_DEEP_SLEEP = const(0x07)
IL91874_DTM1 = const(0x10)
IL91874_DATA_STOP = const(0x11)
IL91874_DISPLAY_REFRESH = const(0x12)
IL91874_DTM2 = const(0x13)
IL91874_PDTM1 = const(0x14)
IL91874_PDTM2 = const(0x15)
IL91874_PDRF = const(0x16)
IL91874_LUT1 = const(0x20)
IL91874_LUTWW = const(0x21)
IL91874_LUTBW = const(0x22)
IL91874_LUTWB = const(0x23)
IL91874_LUTBB = const(0x24)
IL91874_PLL = const(0x30)
IL91874_CDI = const(0x50)
IL91874_RESOLUTION = const(0x61)
IL91874_VCM_DC_SETTING = const(0x82)

class Adafruit_IL91874_base(Adafruit_EPD):
	
	def __init__(self, width, height, rst, dc, busy, srcs=None, cs=None, spi=None):

		super(Adafruit_IL91874_base, self).__init__(width, height, rst, dc, busy, srcs, cs, spi)

	def begin(self, reset=True):
		super(Adafruit_IL91874_base, self).begin(reset)

	def update(self):
		self.command(IL91874_DISPLAY_REFRESH)

		while self._busy.value == True:
			pass

		time.sleep(10)

		self.command(IL91874_CDI, bytearray([0x17]))
		self.command(IL91874_VCM_DC_SETTING, bytearray([0x00]))
		self.command(IL91874_POWER_SETTING, bytearray([0x02, 0x00, 0x00, 0x00]))
		self.command(IL91874_POWER_OFF)

		time.sleep(10)

	def power_up(self):
		self.command(IL91874_BOOSTER_SOFT_START, bytearray([0x07, 0x07, 0x07]))
		self.command(IL91874_POWER_SETTING, bytearray([0x07, 0x00, 0x0A, 0x00]))
		self.command(IL91874_POWER_ON)

		while self._busy.value == True:
			pass

		time.sleep(.2)

		self.command(IL91874_PANEL_SETTING, bytearray([0xCF]))
		self.command(IL91874_CDI, bytearray([0x37]))
		self.command(IL91874_PLL, bytearray([0x29]))
		self.command(IL91874_VCM_DC_SETTING, bytearray([0x0A]))

	def display(self):
		self.power_up()

		#TODO: write data when we get duplex transfer support

		self.update()

	"""
	def image(self, image):
		'''Set buffer to value of Python Imaging Library image.  The image should
		be in RGB mode and a size equal to the display size.
		'''
		if image.mode != 'RGB':
			raise ValueError('Image must be in mode RGB.')
		imwidth, imheight = image.size
		if imwidth != self.width or imheight != self.height:
			raise ValueError('Image must be same dimensions as display ({0}x{1}).' \
				.format(self.width, self.height))
		# Grab all the pixels from the image, faster than getpixel.
		pix = image.load()

		for y in xrange(image.size[1]):
			for x in xrange(image.size[0]):
				if x == 0:
					x = 1
				p = pix[x, y]
				addr = ( (self.width - x) * self.height + y) >> 3
				if p == (0xFF, 0, 0):
					#RED
					self.red_buffer[addr] &= ~(1 << (7 - (y%8)))
				elif p == (0, 0, 0):
					#BLACK
					self.bw_buffer[addr] &= ~(1 << (7 - (y%8)))
				else:
					#WHITE
					self.bw_buffer[addr] |= (1 << (7 - (y%8)))
	"""

	def clear_buffer(self):
		#self.bw_buffer = [0xFF]* (width*height >> 3)
		#self.red_buffer = [0xFF]* (width*height >> 3)
		pass