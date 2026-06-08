# SPDX-FileCopyrightText: 2026 Mikey Sklar, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

"""4-gray grayscale for the Adafruit 2.13" SSD1680 eInk FeatherWing (#4195), via adafruit_epd.

The framebuf path (companion to the displayio adafruit_ssd1680 driver). Reach for adafruit_epd
when you want external-SRAM offload or direct framebuffer access. 250x122 GDEY0213B74 /
FPC-A002. Uses the upstream Adafruit_SSD1680_Grayscale4 class (LUT + colstart=0 baked in) — no
library change; the class default vcom=0x1C is tuned for this GDEY0213B74 panel.

FeatherWing wiring notes (differ from the #4197 EYESPI breakout):
  CS=D9  DC=D10  SCK/MOSI on the shared bus.
  BUSY is not connected on the Wing -> busy_pin=None (timed refresh).
  RST is on the Feather RESET line, not a GPIO -> the panel can only be woken by a Feather
  hardware reset, so we never deep-sleep it (power_down -> no-op). Run after a power-on/reset.
"""

import time

import board
import digitalio

from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.ssd1680 import Adafruit_SSD1680_Grayscale4


class WingGrayscale4(Adafruit_SSD1680_Grayscale4):
    # FeatherWing: RST is on the Feather RESET line, so the panel can't be GPIO-reset to wake
    # from deep sleep -> never deep-sleep it.
    def power_down(self):
        pass


spi = board.SPI()
cs = digitalio.DigitalInOut(board.D9)
dc = digitalio.DigitalInOut(board.D10)
rst = digitalio.DigitalInOut(board.D11)  # harmless on the Wing (RST not routed here)

display = WingGrayscale4(
    122,
    250,
    spi,
    cs_pin=cs,
    dc_pin=dc,
    sramcs_pin=None,
    rst_pin=rst,
    busy_pin=None,  # BUSY not connected on the Wing
    vcom=0x1C,  # class default, tuned for GDEY0213B74 / FPC-A002
)
display.rotation = 3  # landscape; matches the displayio driver's 270
W = display.width
print("Init OK — drawing 4-gray info card...")

display.fill(Adafruit_EPD.WHITE)
display.text("Adafruit ThinkInk", 6, 6, Adafruit_EPD.BLACK, size=2)
display.text('2.13" 250x122', 6, 28, Adafruit_EPD.BLACK, size=2)
display.text("4-Gray E-Ink", 6, 50, Adafruit_EPD.DARK, size=2)
display.text("SSD1680  #4195", 6, 74, Adafruit_EPD.BLACK, size=1)

# 4-level gray ramp across the bottom: black | dark | light | white
RAMP_TOP, RAMP_H = 100, 20
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
