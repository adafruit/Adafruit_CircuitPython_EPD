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

#draw some lines!!
for i in range(152):
    display.draw_pixel(i, i, Adafruit_EPD.RED)
    display.draw_pixel(152-i, i, Adafruit_EPD.RED)
    display.draw_pixel(10, i, Adafruit_EPD.BLACK)
    display.draw_pixel(20, i, Adafruit_EPD.BLACK)
    display.draw_pixel(30, i, Adafruit_EPD.BLACK)
    display.draw_pixel(40, i, Adafruit_EPD.BLACK)
    display.draw_pixel(50, i, Adafruit_EPD.BLACK)
    display.draw_pixel(60, i, Adafruit_EPD.BLACK)
    display.draw_pixel(70, i, Adafruit_EPD.BLACK)
    display.draw_pixel(80, i, Adafruit_EPD.BLACK)

display.display()
