# SPDX-FileCopyrightText: 2026 Mikey Sklar for Adafruit Industries
# SPDX-License-Identifier: MIT
"""
4-gray grayscale demo for the Adafruit 2.13" eInk Pi Bonnet (#4687).
Panel: GDEY0213B74, controller: SSD1680, resolution: 250x122.

Demonstrates:
  - Drawing with BLACK / DARK / LIGHT / WHITE color constants
  - Displaying a grayscale PIL image (mode 'L')

Run on Raspberry Pi with the bonnet seated. Requires ~/eink-env with
adafruit-circuitpython-epd installed.

Usage:
    python3 epd_bonnet_4gray.py [image.bmp]
If an image path is given it must be a grayscale (mode 'L') BMP at 250x122.
"""

import sys
import time

import board
import busio
from digitalio import DigitalInOut
from PIL import Image, ImageDraw

from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.ssd1680 import Adafruit_SSD1680_Grayscale4

spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = DigitalInOut(board.CE0)
dc = DigitalInOut(board.D22)
rst = DigitalInOut(board.D27)
busy = DigitalInOut(board.D17)

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
)
display.rotation = 1

if len(sys.argv) > 1:
    # --- image mode ---
    img = Image.open(sys.argv[1]).convert("L")
    if img.size != (display.width, display.height):
        img = img.resize((display.width, display.height))
    print(f"Displaying {sys.argv[1]} ({img.size})")
    display.image(img)
else:
    # --- drawing mode: 4 gray bars + labels ---
    W, H = display.width, display.height
    bar = W // 4

    display.fill(Adafruit_EPD.WHITE)

    # Top half: solid gray bars left→right: black, dark grey, light grey, white
    for i, color in enumerate(
        (Adafruit_EPD.BLACK, Adafruit_EPD.DARK, Adafruit_EPD.LIGHT, Adafruit_EPD.WHITE)
    ):
        display.fill_rect(i * bar, 0, bar, H // 2, color)

    # Bottom half: checkerboard at each gray level to show dithering range
    for i, color in enumerate(
        (Adafruit_EPD.BLACK, Adafruit_EPD.DARK, Adafruit_EPD.LIGHT, Adafruit_EPD.WHITE)
    ):
        x0 = i * bar
        for cy in range(H // 2, H, 8):
            for cx in range(x0, x0 + bar, 8):
                if (cx // 8 + cy // 8) % 2 == 0:
                    display.fill_rect(cx, cy, 8, 8, color)
                else:
                    display.fill_rect(cx, cy, 8, 8, Adafruit_EPD.BLACK)

    print("Displaying 4-bar + checker test pattern")

print("Refreshing...")
t0 = time.monotonic()
display.display()
print(f"Done in {time.monotonic() - t0:.1f}s")
