# SPDX-FileCopyrightText: 2026 Mikey Sklar, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

"""4-gray grayscale for the Adafruit 1.54" 200x200 eInk Breakout (#4196,
SSD1681 / GDEY0154D67) on a Feather, via adafruit_epd.

adafruit_epd is the framebuf path (with optional external SRAM offload). On a
Feather you can alternatively use the displayio driver adafruit_ssd1681; reach
for adafruit_epd when you want SRAM offload or direct framebuffer access.

Wiring for Feather RP2040/RP2350 + EYESPI Breakout -> #4196 EYESPI:
  TCS  -> D9   (use TCS pad, not ECS/SDCS/TSCS)
  DC   -> D10
  RST  -> D11
  BUSY -> D12
  SCK  -> SCK   MOSI -> MOSI   3V3 -> 3V3   GND -> GND
"""

import time

import board
import busio
import digitalio

from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.ssd1681 import Adafruit_SSD1681_Grayscale4

# Feather RP2040/RP2350 + EYESPI Breakout
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.D9)  # TCS on EYESPI breakout
dc = digitalio.DigitalInOut(board.D10)
rst = digitalio.DigitalInOut(board.D11)
busy = digitalio.DigitalInOut(board.D12)

# 1.54" 200x200 Breakout #4196 (GDEY0154D67). colstart=0; the 4-gray waveform and
# VCOM come from the panel OTP + the driver's built-in GxEPD2 LUT.
display = Adafruit_SSD1681_Grayscale4(
    200,
    200,
    spi,
    cs_pin=cs,
    dc_pin=dc,
    sramcs_pin=None,
    rst_pin=rst,
    busy_pin=busy,
    vcom=0x1C,
    colstart=0,
)

display.rotation = 0

W = display.width

print("Drawing 4-gray info card...")
display.fill(Adafruit_EPD.WHITE)

# Product text (top-left); the DARK line shows mid-gray text renders cleanly
display.text("Adafruit", 6, 6, Adafruit_EPD.BLACK, size=2)
display.text("ThinkInk", 6, 28, Adafruit_EPD.BLACK, size=2)
display.text('1.54" 200x200', 6, 54, Adafruit_EPD.BLACK, size=2)
display.text("4-Gray E-Ink", 6, 78, Adafruit_EPD.DARK, size=2)
display.text("SSD1681 Driver", 6, 104, Adafruit_EPD.BLACK, size=2)

# 4-level gray ramp across the bottom: black | dark | light | white
RAMP_TOP, RAMP_H = 150, 40
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
