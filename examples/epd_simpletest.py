# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import board
import busio
import digitalio

from adafruit_epd.ek79686 import Adafruit_EK79686
from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.il0373 import Adafruit_IL0373
from adafruit_epd.il0398 import Adafruit_IL0398
from adafruit_epd.il91874 import Adafruit_IL91874
from adafruit_epd.jd79661 import Adafruit_JD79661
from adafruit_epd.ssd1608 import Adafruit_SSD1608
from adafruit_epd.ssd1675 import Adafruit_SSD1675
from adafruit_epd.ssd1680 import Adafruit_SSD1680, Adafruit_SSD1680Z
from adafruit_epd.ssd1681 import Adafruit_SSD1681
from adafruit_epd.uc8151d import Adafruit_UC8151D

# create the spi device and pins we will need
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
ecs = digitalio.DigitalInOut(board.D12)
dc = digitalio.DigitalInOut(board.D11)
srcs = digitalio.DigitalInOut(board.D10)  # can be None to use internal memory
rst = digitalio.DigitalInOut(board.D9)  # can be None to not use this pin
busy = digitalio.DigitalInOut(board.D5)  # can be None to not use this pin

# give them all to our drivers
print("Creating display")
# display = Adafruit_JD79661(122, 150,        # 2.13" Quad-color display
# display = Adafruit_SSD1608(200, 200,        # 1.54" HD mono display
# display = Adafruit_SSD1675(122, 250,        # 2.13" HD mono display
# display = Adafruit_SSD1680(122, 250,        # 2.13" HD Tri-color display
# display = Adafruit_SSD1681(200, 200,        # 1.54" HD Tri-color display
# display = Adafruit_SSD1681(200, 200,        # 1.54" HD Tri-color display
# display = Adafruit_IL91874(176, 264,        # 2.7" Tri-color display
# display = Adafruit_EK79686(176, 264,        # 2.7" Tri-color display
# display = Adafruit_IL0373(152, 152,         # 1.54" Tri-color display
# display = Adafruit_UC8151D(128, 296,        # 2.9" mono flexible display
# display = Adafruit_IL0373(128, 296,         # 2.9" Tri-color display IL0373
# display = Adafruit_SSD1680(128, 296,        # 2.9" Tri-color display SSD1680
# display = Adafruit_IL0398(400, 300,         # 4.2" Tri-color display
display = Adafruit_IL0373(
    104,
    212,  # 2.13" Tri-color display
    spi,
    cs_pin=ecs,
    dc_pin=dc,
    sramcs_pin=srcs,
    rst_pin=rst,
    busy_pin=busy,
)

# IF YOU HAVE A 2.13" FLEXIBLE DISPLAY uncomment these lines!
# display.set_black_buffer(1, False)
# display.set_color_buffer(1, False)

# IF YOU HAVE A 2.9" FLEXIBLE DISPLAY uncomment these lines!
# display.set_black_buffer(1, True)
# display.set_color_buffer(1, True)

display.rotation = 1
if type(display) == Adafruit_JD79661:
    WHITE = Adafruit_JD79661.WHITE
    BLACK = Adafruit_JD79661.BLACK
    RED = Adafruit_JD79661.RED
    YELLOW = Adafruit_JD79661.YELLOW
else:
    WHITE = Adafruit_EPD.WHITE
    BLACK = Adafruit_EPD.BLACK
    RED = Adafruit_EPD.RED

# clear the buffer
print("Clear buffer")
display.fill(WHITE)
display.pixel(10, 100, BLACK)

print("Draw Rectangles")
display.fill_rect(5, 5, 10, 10, RED)
display.rect(0, 0, 20, 30, BLACK)

print("Draw lines")
if type(display) == Adafruit_JD79661:
    display.line(0, 0, display.width - 1, display.height - 1, YELLOW)
    display.line(0, display.height - 1, display.width - 1, 0, YELLOW)
else:
    display.line(0, 0, display.width - 1, display.height - 1, BLACK)
    display.line(0, display.height - 1, display.width - 1, 0, RED)

print("Draw text")
display.text("hello world", 25, 10, BLACK)
display.display()
