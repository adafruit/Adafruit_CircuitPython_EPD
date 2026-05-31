# SPDX-FileCopyrightText: 2026 Mikey Sklar, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

"""4-gray grayscale for the Adafruit 2.13" eInk Pi Bonnet (#4687, SSD1680) on a
Raspberry Pi (Blinka).

adafruit_epd is the framebuf path (with optional external SRAM offload) and runs
under Blinka on Linux, where displayio is unavailable.

Draws a self-identifying info card (panel name, resolution, driver) plus a
4-level gray ramp, so the panel shows what it is right on its own screen.

The text uses adafruit_framebuf, which on Blinka needs font5x8.bin in the same
folder as this script (CircuitPython has it built in; Blinka does not). Grab it
from the Adafruit_CircuitPython_framebuf repo's examples/ directory.

Wiring — #4687 2.13" eInk Pi Bonnet (all-in-one HAT, no jumpers needed):
  CS   → CE0 (GPIO8)    DC   → GPIO22
  RST  → GPIO27         BUSY → GPIO17
  SCK → SCK   MOSI → MOSI   MISO → MISO   3V3 → 3V3   GND → GND

Note: the Bonnet routes DC to GPIO22. The #4197 breakout wired through an EYESPI
Pi Beret routes DC to GPIO25 instead — see rpi_epd_grayscale_2in13_breakout.py
for that board.

Pi 5 only: add `dtoverlay=spi0-0cs` after `dtparam=spi=on` in
/boot/firmware/config.txt to free CE0, otherwise SPI claims it (GPIO busy).
"""

import time

import board
import busio
import digitalio

from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.ssd1680 import Adafruit_SSD1680_Grayscale4

# Raspberry Pi (Blinka) + 2.13" eInk Pi Bonnet
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.CE0)
dc = digitalio.DigitalInOut(board.D22)  # Bonnet routes DC to GPIO22
rst = digitalio.DigitalInOut(board.D27)
busy = digitalio.DigitalInOut(board.D17)

# 2.13" eInk Pi Bonnet #4687 (FPC-A002 / GDEY0213B74). colstart=0; it is only
# nonzero on panels with a physical left dead-zone (e.g. MagTag FPC-7519,
# colstart=8).
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

# rotation=1: on the Bonnet the panel is mounted 180° from the bare breakout, so
# this reads upright with the board's "adafruit 2.13" eink bonnet" label at top.
display.rotation = 1

W = display.width

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
