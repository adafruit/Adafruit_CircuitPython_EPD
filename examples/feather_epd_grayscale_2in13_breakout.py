# SPDX-FileCopyrightText: 2026 Mikey Sklar, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

"""4-gray grayscale for the Adafruit 2.13" SSD1680 eInk Breakout (#4197) on a
Feather, via adafruit_epd. Uncomment the constructor that matches your panel.

adafruit_epd is the framebuf path (with optional external SRAM offload). On a
Feather you can alternatively use the displayio driver adafruit_ssd1680; reach
for adafruit_epd when you want SRAM offload or direct framebuffer access.

For Raspberry Pi + Blinka, use rpi_epd_grayscale_2in13_breakout.py instead.

Wiring for Feather RP2040/RP2350 + EYESPI Breakout → #4197 EYESPI:
  TCS  → D9   (use TCS pad, not ECS/SDCS/TSCS)
  DC   → D10
  RST  → D11
  BUSY → D12
  SCK  → SCK   MOSI → MOSI   3V3 → 3V3   GND → GND
"""

import time

import board
import busio
import digitalio

from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.ssd1680 import Adafruit_SSD1680_Grayscale4

# Feather RP2040/RP2350 + EYESPI Breakout
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.D9)  # TCS on EYESPI breakout
dc = digitalio.DigitalInOut(board.D10)
rst = digitalio.DigitalInOut(board.D11)
busy = digitalio.DigitalInOut(board.D12)

# 2.13" Mono Breakout #4197 — both FPC-7528B (2024+) and FPC-A002/GDEY0213B74
# (legacy) panels use colstart=0. colstart is only nonzero on panels with a
# physical left dead-zone (e.g. MagTag FPC-7519, colstart=8).
display = Adafruit_SSD1680_Grayscale4(
    122,
    250,
    spi,
    cs_pin=cs,
    dc_pin=dc,
    sramcs_pin=None,
    rst_pin=rst,
    busy_pin=busy,
    vcom=0x1C,
    colstart=0,
)

# rotation=3 (landscape, USB at right) matches the displayio driver's 270.
display.rotation = 3

W, H = display.width, display.height

print("Drawing 4-gray info card...")
display.fill(Adafruit_EPD.WHITE)

# Product text (top-left); the DARK line shows mid-gray text renders cleanly
display.text("Adafruit ThinkInk", 6, 6, Adafruit_EPD.BLACK, size=2)
display.text('2.13" 250x122', 6, 28, Adafruit_EPD.BLACK, size=2)
display.text("4-Gray E-Ink", 6, 50, Adafruit_EPD.DARK, size=2)
display.text("SSD1680 Driver", 6, 74, Adafruit_EPD.BLACK, size=1)

# 4-level gray ramp across the bottom: black | dark | light | white
RAMP_TOP, RAMP_H = 94, 24
SEG = W // 4
ramp = (Adafruit_EPD.BLACK, Adafruit_EPD.DARK, Adafruit_EPD.LIGHT, Adafruit_EPD.WHITE)
for i, color in enumerate(ramp):
    x = i * SEG
    display.fill_rect(x, RAMP_TOP, SEG if i < 3 else W - x, RAMP_H, color)
# 1px black border + dividers so every block (incl. white) reads distinctly
display.rect(0, RAMP_TOP, W, RAMP_H, Adafruit_EPD.BLACK)
for i in range(1, 4):
    display.vline(i * SEG, RAMP_TOP, RAMP_H, Adafruit_EPD.BLACK)

print("Refreshing...")
t0 = time.monotonic()
display.display()
print(f"Done in {time.monotonic() - t0:.1f}s")
