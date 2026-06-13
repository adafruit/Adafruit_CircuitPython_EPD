# SPDX-FileCopyrightText: 2026 Mikey Sklar, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

"""4-gray grayscale for the Adafruit 4.2" SSD1683 E-Ink Display (#6381), via adafruit_epd.

400x300 GDEY042T81 / FPC-190 ribbon. Uses Adafruit_SSD1683_Grayscale4 (vcom=0x30
baked in). Hardware-verified on Feather RP2040 ThinkInk.

Hardware: connect the 24-pin FPC ribbon to the ThinkInk board's ZIF connector.
No external wiring required.
"""

import time

import board
import busio
import digitalio

from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.ssd1683 import Adafruit_SSD1683_Grayscale4

spi = busio.SPI(board.EPD_SCK, board.EPD_MOSI)
cs = digitalio.DigitalInOut(board.EPD_CS)
dc = digitalio.DigitalInOut(board.EPD_DC)
rst = digitalio.DigitalInOut(board.EPD_RESET)
busy = digitalio.DigitalInOut(board.EPD_BUSY)

display = Adafruit_SSD1683_Grayscale4(
    400,
    300,
    spi,
    cs_pin=cs,
    dc_pin=dc,
    sramcs_pin=None,
    rst_pin=rst,
    busy_pin=busy,
)
W = display.width
H = display.height
print(f"Init OK — {W}x{H}, drawing 4-gray info card...")

display.fill(Adafruit_EPD.WHITE)
display.text("Adafruit ThinkInk", 6, 6, Adafruit_EPD.BLACK, size=2)
display.text('4.2" 400x300', 6, 28, Adafruit_EPD.BLACK, size=2)
display.text("4-Gray E-Ink", 6, 50, Adafruit_EPD.DARK, size=2)
display.text("SSD1683  #6381", 6, 74, Adafruit_EPD.BLACK, size=1)

# 4-level gray ramp across the bottom
RAMP_TOP, RAMP_H = 260, 34
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
