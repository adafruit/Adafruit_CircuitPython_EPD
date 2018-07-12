import digitalio
import busio
from adafruit_bus_device.spi_device import SPIDevice
from board import *
from Adafruit_EPD.epd import Adafruit_EPD
from Adafruit_EPD.il0373 import Adafruit_IL0373

#create the spi device and pins we will need
spi = busio.SPI(SCK, MOSI=MOSI, MISO=MISO)
ecs = digitalio.DigitalInOut(D10)
dc = digitalio.DigitalInOut(D9)
srcs = digitalio.DigitalInOut(D8)
rst = digitalio.DigitalInOut(D7)
busy = digitalio.DigitalInOut(D6)

#give them all to our driver
display = Adafruit_IL0373(152, 152, rst, dc, busy, srcs, ecs, spi)

#clear the buffer
display.clear_buffer()

#draw some arbitrary lines and shapes!!
display.fill_rect(30, 20, 50, 60, Adafruit_EPD.RED)
display.hline(120, 30, 60, Adafruit_EPD.BLACK)
display.vline(120, 30, 60, Adafruit_EPD.BLACK)

display.display()
