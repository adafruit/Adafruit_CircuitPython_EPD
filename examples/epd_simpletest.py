import digitalio
import busio
import board
from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.il0373 import Adafruit_IL0373
from adafruit_epd.il91874 import Adafruit_IL91874

# create the spi device and pins we will need
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
ecs = digitalio.DigitalInOut(board.D10)
dc = digitalio.DigitalInOut(board.D9)
srcs = digitalio.DigitalInOut(board.D7)    # can be None to use internal memory
rst = digitalio.DigitalInOut(board.D11)    # can be None to not use this pin
busy = digitalio.DigitalInOut(board.D12)   # can be None to not use this pin

# give them all to our driver
print("Creating display")
display = Adafruit_IL91874(176, 264, spi,         # 2.7" Tri-color display
#display = Adafruit_IL0373(104, 212, spi,         # 2.13" Tri-color display
                          cs_pin=ecs, dc_pin=dc, sramcs_pin=srcs,
                          rst_pin=rst, busy_pin=busy)

display.rotation = 2

# clear the buffer
print("Clear buffer")
display.fill(Adafruit_EPD.WHITE)

print("Draw Rectangles")
display.fill_rect(5, 5, 10, 10, Adafruit_EPD.RED)
display.rect(0, 0, 20, 30, Adafruit_EPD.BLACK)

print("Draw lines")
display.line(0, 0, display.width-1, display.height-1, Adafruit_EPD.BLACK)
display.line(0, display.height-1, display.width-1, 0, Adafruit_EPD.RED)

print("Draw text")
display.text('hello world', 25, 10, Adafruit_EPD.BLACK)

display.display()
