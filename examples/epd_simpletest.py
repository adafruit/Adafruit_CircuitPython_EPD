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

r_width = 5
r_pos = display.height

color = Adafruit_EPD.BLACK
while r_pos > display.height/2:
    if r_pos < display.height - 50:
        color = Adafruit_EPD.RED
    display.rect(display.width - r_pos, display.height - r_pos,
                 display.width - 2*(display.width - r_pos),
                 display.height - 2*(display.height - r_pos), color)
    r_pos = r_pos - r_width

display.display()
