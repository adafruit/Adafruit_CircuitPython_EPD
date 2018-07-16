import time
from micropython import const
from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.mcp_sram import Adafruit_MCP_SRAM

IL0373_PANEL_SETTING = const(0x00)
IL0373_POWER_SETTING = const(0x01)
IL0373_POWER_OFF = const(0x02)
IL0373_POWER_OFF_SEQUENCE = const(0x03)
IL0373_POWER_ON = const(0x04)
IL0373_POWER_ON_MEASURE = const(0x05)
IL0373_BOOSTER_SOFT_START = const(0x06)
IL0373_DEEP_SLEEP = const(0x07)
IL0373_DTM1 = const(0x10)
IL0373_DATA_STOP = const(0x11)
IL0373_DISPLAY_REFRESH = const(0x12)
IL0373_DTM2 = const(0x13)
IL0373_PDTM1 = const(0x14)
IL0373_PDTM2 = const(0x15)
IL0373_PDRF = const(0x16)
IL0373_LUT1 = const(0x20)
IL0373_LUTWW = const(0x21)
IL0373_LUTBW = const(0x22)
IL0373_LUTWB = const(0x23)
IL0373_LUTBB = const(0x24)
IL0373_PLL = const(0x30)
IL0373_CDI = const(0x50)
IL0373_RESOLUTION = const(0x61)
IL0373_VCM_DC_SETTING = const(0x82)

class Adafruit_IL0373(Adafruit_EPD):
    # pylint: disable=too-many-arguments
    def __init__(self, width, height, rst_pin, dc_pin, busy_pin, srcs_pin, cs_pin, spi):
        super(Adafruit_IL0373, self).__init__(width, height, rst_pin, dc_pin, busy_pin,
                                              srcs_pin, cs_pin, spi)

        self.bw_bufsize = int(width * height / 8)
        self.red_bufsize = int(width * height / 8)

        self.begin()
        # pylint: enable=too-many-arguments

    def begin(self, reset=True):
        super(Adafruit_IL0373, self).begin(reset)

        while self._busy.value is False:
            pass

        self.command(IL0373_POWER_SETTING, bytearray([0x03, 0x00, 0x2b, 0x2b, 0x09]))
        self.command(IL0373_BOOSTER_SOFT_START, bytearray([0x17, 0x17, 0x17]))

    def update(self):
        self.command(IL0373_DISPLAY_REFRESH)

        while self._busy.value is False:
            pass

        self.command(IL0373_CDI, bytearray([0x17]))
        self.command(IL0373_VCM_DC_SETTING, bytearray([0x00]))
        self.command(IL0373_POWER_OFF)
        time.sleep(2)

    def power_up(self):
        self.command(IL0373_POWER_ON)

        while self._busy.value is False:
            pass

        time.sleep(.2)

        self.command(IL0373_PANEL_SETTING, bytearray([0xCF]))
        self.command(IL0373_CDI, bytearray([0x37]))
        self.command(IL0373_PLL, bytearray([0x29]))
        _b1 = self.height & 0xFF
        _b2 = (self.height >> 8) & 0xFF
        _b3 = self.width & 0xFF
        _b4 = (self.width >> 8) & 0xFF
        self.command(IL0373_RESOLUTION, bytearray([_b1, _b2, _b3, _b4]))
        self.command(IL0373_VCM_DC_SETTING, bytearray([0x0A]))


    def display(self):
        self.power_up()

        while not self.spi_device.try_lock():
            pass
        self.sram.cs_pin.value = False
        #send read command
        self.spi_device.write(bytearray([Adafruit_MCP_SRAM.SRAM_READ]))
        #send start address
        self.spi_device.write(bytearray([0x00, 0x00]))
        self.spi_device.unlock()

        #first data byte from SRAM will be transfered in at the
        #same time as the EPD command is transferred out
        cmd = self.command(IL0373_DTM1, end=False)

        while not self.spi_device.try_lock():
            pass
        self._dc.value = True
        xfer = bytearray([cmd])
        outbuf = bytearray(1)
        for _ in range(self.bw_bufsize):
            outbuf[0] = xfer[0]
            self.spi_device.write_readinto(outbuf, xfer)
        self._cs.value = True
        self.sram.cs_pin.value = True

        time.sleep(.002)

        self.sram.cs_pin.value = False
        #send read command
        self.spi_device.write(bytearray([Adafruit_MCP_SRAM.SRAM_READ]))
        #send start address
        self.spi_device.write(bytearray([(self.bw_bufsize >> 8), (self.bw_bufsize & 0xFF)]))
        self.spi_device.unlock()

        #first data byte from SRAM will be transfered in at the
        #same time as the EPD command is transferred out
        cmd = self.command(IL0373_DTM2, end=False)

        while not self.spi_device.try_lock():
            pass
        self._dc.value = True
        xfer = bytearray([cmd])
        outbuf = bytearray(1)
        for _ in range(self.bw_bufsize):
            outbuf[0] = xfer[0]
            self.spi_device.write_readinto(outbuf, xfer)
        self._cs.value = True
        self.sram.cs_pin.value = True
        self.spi_device.unlock()

        self.update()

    def draw_pixel(self, x, y, color):
        if (x < 0) or (x >= self.width) or (y < 0) or (y >= self.height):
            return

        if x == 0:
            x = 1

        addr = int(((self.width - x) * self.height + y)/8)
        if color == Adafruit_EPD.RED:
            addr = addr + self.bw_bufsize
        current = self.sram.read8(addr)

        if color == Adafruit_EPD.WHITE:
            current = current | (1 << (7 - y%8))
        elif color == Adafruit_EPD.RED or color == Adafruit_EPD.BLACK:
            current = current & ~(1 << (7 - y%8))
        elif color == Adafruit_EPD.INVERSE:
            current = current ^ (1 << (7 - y%8))

        self.sram.write8(addr, current)
        return

    def clear_buffer(self):
        self.sram.erase(0x00, self.bw_bufsize, 0xFF)
        self.sram.erase(self.bw_bufsize, self.red_bufsize, 0xFF)

    def clear_display(self):
        self.clear_buffer()
        self.display()
