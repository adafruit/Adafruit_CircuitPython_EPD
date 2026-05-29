# SPDX-FileCopyrightText: 2026 Mikey Sklar, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

"""4-gray grayscale demo for the Adafruit 2.13" Mono eInk Display Breakout (#4197).
Panel: FPC-7528B, controller: SSD1680, resolution: 250x122.

Requires a Feather RP2040/RP2350 + EYESPI Breakout connected to the #4197 EYESPI
connector. Run on CircuitPython with adafruit_epd installed via circup.

Wiring (EYESPI Breakout → Feather):
  TCS  → D9    (use TCS pad on breakout — not ECS/SDCS/TSCS)
  DC   → D10
  RST  → D11
  BUSY → D12
  SCK  → SCK   MOSI → MOSI   3V3 → 3V3   GND → GND

Note: EPD SDO is not connected on this breakout; panel type is hardcoded.
FPC-7528B requires colstart=8 and vcom=0x1C.
"""

import time

import board
import busio
import digitalio

from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.ssd1680 import Adafruit_SSD1680_Grayscale4

spi  = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs   = digitalio.DigitalInOut(board.D9)   # TCS on EYESPI breakout
dc   = digitalio.DigitalInOut(board.D10)
rst  = digitalio.DigitalInOut(board.D11)
busy = digitalio.DigitalInOut(board.D12)

display = Adafruit_SSD1680_Grayscale4(
    122, 250,
    spi,
    cs_pin=cs,
    dc_pin=dc,
    sramcs_pin=None,
    rst_pin=rst,
    busy_pin=busy,
    vcom=0x1C,
    colstart=8,   # FPC-7528B: correct source channel alignment
)
display.rotation = 1

W, H = display.width, display.height
BAR = W // 4

# Draw 4-bar testcard
print("Drawing 4-bar test pattern...")
display.fill(Adafruit_EPD.WHITE)
display.fill_rect(BAR,     0, BAR,          H, Adafruit_EPD.LIGHT)
display.fill_rect(BAR * 2, 0, BAR,          H, Adafruit_EPD.DARK)
display.fill_rect(BAR * 3, 0, W - BAR * 3, H, Adafruit_EPD.BLACK)  # fill to edge

print("Refreshing...")
t0 = time.monotonic()
display.display()
print(f"Done in {time.monotonic() - t0:.1f}s")
