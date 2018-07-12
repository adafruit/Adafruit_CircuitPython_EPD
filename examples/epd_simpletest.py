import digitalio
import busio
import board
from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.il0373 import Adafruit_IL0373

# create the spi device and pins we will need
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
ecs = digitalio.DigitalInOut(board.D10)
dc = digitalio.DigitalInOut(board.D9)
srcs = digitalio.DigitalInOut(board.D8)
rst = digitalio.DigitalInOut(board.D7)
busy = digitalio.DigitalInOut(board.D6)

# give them all to our driver
display = Adafruit_IL0373(152, 152, rst, dc, busy, srcs, ecs, spi)

# clear the buffer
display.clear_buffer()

# draw some arbitrary lines and shapes!!
display.fill_rect(30, 20, 50, 60, Adafruit_EPD.RED)
display.hline(120, 30, 60, Adafruit_EPD.BLACK)
display.vline(120, 30, 60, Adafruit_EPD.BLACK)

display.display()
