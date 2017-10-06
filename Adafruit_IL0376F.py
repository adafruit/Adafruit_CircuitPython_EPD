from Adafruit_EPD import *
from micropython import const

IL0376F_PANEL_SETTING = const(0x00)
IL0376F_POWER_SETTING = const(0x01)
IL0376F_POWER_OFF = const(0x02)
IL0376F_POWER_OFF_SEQUENCE = const(0x03)
IL0376F_POWER_ON = const(0x04)
IL0376F_POWER_ON_MEASURE = const(0x05)
IL0376F_BOOSTER_SOFT_START = const(0x06)
IL0376F_DTM1 = const(0x10)
IL0376F_DATA_STOP = const(0x11)
IL0376F_DISPLAY_REFRESH = const(0x12)
IL0376F_DTM2 = const(0x13)
IL0376F_VCOM1_LUT = const(0x20)
IL0376F_WHITE_LUT = const(0x21)
IL0376F_BLACK_LUT = const(0x22)
IL0376F_GRAY1_LUT = const(0x23)
IL0376F_GRAY2_LUT = const(0x24)
IL0376F_VCOM2_LUT = const(0x25)
IL0376F_RED0_LUT = const(0x26)
IL0376F_RED1_LUT = const(0x27)
IL0376F_PLL = const(0x30)
IL0376F_CDI = const(0x50)
IL0376F_RESOLUTION = const(0x61)
IL0376F_VCM_DC_SETTING = const(0x82)

class Adafruit_IL0376F_base(Adafruit_EPD):
	
	def __init__(self, width, height, rst, dc, busy, srcs=None, cs=None, spi=None):

		super(Adafruit_IL0376F_base, self).__init__(width, height, rst, dc, busy, srcs, cs, spi)

	def begin(self, reset=True):
		super(Adafruit_IL0376F_base, self).begin(reset)

		self.command(IL0376F_POWER_SETTING, bytearray([0x07, 0x00, 0x0D, 0x00]))
		self.command(IL0376F_BOOSTER_SOFT_START, bytearray([0x07, 0x07, 0x07]))

	def update(self):
		self.command(IL0376F_DISPLAY_REFRESH)

		while self._busy.value == True:
			pass

		time.sleep(10)

		self.command(IL0376F_CDI, bytearray([0x17]))
		self.command(IL0376F_VCM_DC_SETTING, bytearray([0x00]))
		self.command(IL0376F_POWER_SETTING, bytearray([0x02, 0x00, 0x00, 0x00]))
		self.command(IL0376F_POWER_OFF)

	def power_up(self):
		self.command(IL0376F_POWER_ON)
		while self._busy.value == True:
			pass

		time.sleep(.2)

		self.command(IL0376F_PANEL_SETTING, bytearray([0xCF]))
		self.command(IL0376F_CDI, bytearray([0x37]))
		self.command(IL0376F_PLL, bytearray([0x39]))
		self.command(IL0376F_VCM_DC_SETTING, bytearray([0x0E]))

	def display(self):
		self.power_up()

		self.command(IL0376F_DTM1, end=False)
		self._dc.value = True
		with self.spi_device as spi:
			for i in range(10000):
					spi.write(bytearray([0xff]))#TODO actual data
		self._cs.value = True

		self.command(IL0376F_DTM2, end=False)
		self._dc.value = True
		with self.spi_device as spi:
			for i in range(5000):
					spi.write(bytearray([0xff]))#TODO actual data
		self._cs.value = True

		self.update()

	"""
	def image(self, image):
		Set buffer to value of Python Imaging Library image.  The image should
		be in RGB mode and a size equal to the display size.
		
		if image.mode != 'RGB':
			raise ValueError('Image must be in mode RGB.')
		imwidth, imheight = image.size
		if imwidth != self.width or imheight != self.height:
			raise ValueError('Image must be same dimensions as display ({0}x{1}).' \
				.format(self.width, self.height))
		# Grab all the pixels from the image, faster than getpixel.
		pix = image.load()

		for y in xrange(image.size[0]):
			for x in xrange(image.size[1]):
				if x == 0:
					x = 1
				p = pix[x, y]
				if p == (0xFF, 0, 0):
					#RED
					addr = ( (self.width - x) * self.height + y) >> 3
					self.red_buffer[addr] &= ~(1 << (7 - (y%8)))
				else:
					#GS
					bits = (6 - y%4 * 2)
					addr = ( (self.width - x) * self.height + y) >> 2
					self.bw_buffer[addr] &= ~(0x3 << bits)
					if p == (0xFF, 0xFF, 0xFF): #WHITE
						self.bw_buffer[addr] |= (0x3 << bits)

					elif p == (0x7F, 0x7F, 0x7F): #GRAY
						self.bw_buffer[addr] |= (0x2 << bits)
	"""