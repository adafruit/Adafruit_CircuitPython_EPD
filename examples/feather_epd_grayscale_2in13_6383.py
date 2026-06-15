# SPDX-FileCopyrightText: 2026 Mikey Sklar, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

"""4-gray grayscale for the Adafruit 2.13" SSD1680Z E-Ink Display (#6383), via adafruit_epd.

250x122 FPC-7528B ribbon. Uses Adafruit_SSD1680_Grayscale4 (colstart=0,
vcom=0x1C baked in). Hardware-verified on Feather RP2040 ThinkInk.

Hardware: connect the 24-pin FPC ribbon to the ThinkInk board's ZIF connector.
No external wiring required.
"""

import time

import board
import busio
import digitalio

from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.ssd1680 import Adafruit_SSD1680_Grayscale4

spi = busio.SPI(board.EPD_SCK, board.EPD_MOSI)
cs = digitalio.DigitalInOut(board.EPD_CS)
dc = digitalio.DigitalInOut(board.EPD_DC)
rst = digitalio.DigitalInOut(board.EPD_RESET)
busy = digitalio.DigitalInOut(board.EPD_BUSY)

display = Adafruit_SSD1680_Grayscale4(
    122,
    250,
    spi,
    cs_pin=cs,
    dc_pin=dc,
    sramcs_pin=None,
    rst_pin=rst,
    busy_pin=busy,
)
display.rotation = 3
W = display.width
H = display.height
print(f"Init OK — {W}x{H}, drawing 4-gray info card...")

display.fill(Adafruit_EPD.WHITE)
display.text("Adafruit ThinkInk", 6, 6, Adafruit_EPD.BLACK, size=2)
display.text('2.13" 250x122', 6, 28, Adafruit_EPD.BLACK, size=2)
display.text("4-Gray E-Ink", 6, 50, Adafruit_EPD.DARK, size=2)
display.text("SSD1680Z  #6383", 6, 74, Adafruit_EPD.BLACK, size=1)

# 4-level gray ramp across the bottom
RAMP_TOP, RAMP_H = 96, 20
SEG = W // 4
ramp = (Adafruit_EPD.BLACK, Adafruit_EPD.DARK, Adafruit_EPD.LIGHT, Adafruit_EPD.WHITE)
for i, color in enumerate(ramp):
    x = i * SEG
    display.fill_rect(x, RAMP_TOP, SEG if i < 3 else W - x, RAMP_H, color)
display.rect(0, RAMP_TOP, W, RAMP_H, Adafruit_EPD.BLACK)
for i in range(1, 4):
    display.vline(i * SEG, RAMP_TOP, RAMP_H, Adafruit_EPD.BLACK)

print("Refreshing...")
t0 = time.monotonic()
display.display()
print(f"Done in {time.monotonic() - t0:.1f}s")
