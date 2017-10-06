from Adafruit_EPD import *

class Adafruit_IL91874_base(Adafruit_EPD):
	IL91874_PANEL_SETTING = 0x00
	IL91874_POWER_SETTING = 0x01
	IL91874_POWER_OFF = 0x02
	IL91874_POWER_OFF_SEQUENCE =0x03
	IL91874_POWER_ON = 0x04
	IL91874_POWER_ON_MEASURE = 0x05
	IL91874_BOOSTER_SOFT_START = 0x06
	IL91874_DEEP_SLEEP = 0x07
	IL91874_DTM1 = 0x10
	IL91874_DATA_STOP = 0x11
	IL91874_DISPLAY_REFRESH = 0x12
	IL91874_DTM2 = 0x13
	IL91874_PDTM1 = 0x14
	IL91874_PDTM2 = 0x15
	IL91874_PDRF = 0x16
	IL91874_LUT1 = 0x20
	IL91874_LUTWW = 0x21
	IL91874_LUTBW = 0x22
	IL91874_LUTWB = 0x23
	IL91874_LUTBB = 0x24
	IL91874_PLL = 0x30
	IL91874_CDI = 0x50
	IL91874_RESOLUTION = 0x61
	IL91874_VCM_DC_SETTING = 0x82
	
	def __init__(self, width, height, rst, dc, busy, sclk=None, mosi=None, cs=None, gpio=None, spi=None):

		super(Adafruit_IL91874_base, self).__init__(width, height, rst, dc, busy, sclk, mosi, cs, gpio, spi)

		self.bw_buffer = [0xFF]* (width*height >> 3)
		self.red_buffer = [0xFF]* (width*height >> 3)

	def begin(self, reset=True):
		super(Adafruit_IL91874_base, self).begin(reset)

		self.command(self.IL91874_POWER_SETTING, [0x07, 0x00, 0x0A, 0x00])
		self.command(self.IL91874_BOOSTER_SOFT_START, [0x07, 0x07, 0x07])

	def update(self):
		self.command(self.IL91874_DISPLAY_REFRESH)

		while self._gpio.is_high(self._busy):
			pass

		time.sleep(10)

		self.command(self.IL91874_CDI, [0x17])
		self.command(self.IL91874_VCM_DC_SETTING, [0x00])
		self.command(self.IL91874_POWER_SETTING, [0x02, 0x00, 0x00, 0x00])
		self.command(self.IL91874_POWER_OFF)

		time.sleep(10)

	def power_up(self):
		self.command(self.IL91874_POWER_ON)
		while self._gpio.is_high(self._busy):
			pass

		time.sleep(.2)

		self.command(self.IL91874_PANEL_SETTING, [0xCF])
		self.command(self.IL91874_CDI, [0x37])
		self.command(self.IL91874_PLL, [0x29])
		self.command(self.IL91874_VCM_DC_SETTING, [0x0A])

	def display(self):
		self.power_up()

		self.command(self.IL91874_DTM1, end=False)
		self._gpio.set_high(self._dc)
		for i in range(len(self.bw_buffer)):
			self._spi.write([self.bw_buffer[i]])
		self._gpio.set_high(self._cs)

		self.command(self.IL91874_DTM2, end=False)
		self._gpio.set_high(self._dc)
		for i in range(len(self.red_buffer)):
			self._spi.write([self.red_buffer[i]])
		self._gpio.set_high(self._cs)
		self.update()

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

	def clear_buffer(self):
		self.bw_buffer = [0xFF]* (width*height >> 3)
		self.red_buffer = [0xFF]* (width*height >> 3)