# SPDX-FileCopyrightText: 2026 Mikey Sklar, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

"""4-gray grayscale for the Adafruit 2.13" SSD1680 eInk Breakout (#4197) on a
Feather, via adafruit_epd. Uncomment the constructor that matches your panel.

adafruit_epd is the framebuf path (with optional external SRAM offload). On a
Feather you can alternatively use the displayio driver adafruit_ssd1680; reach
for adafruit_epd when you want SRAM offload or direct framebuffer access.

For Raspberry Pi + Blinka, use rpi_epd_grayscale4_2in13_breakout.py instead.

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

# ── Uncomment ONE constructor below ─────────────────────────────────────────

# 2.13" Mono Breakout #4197 — FPC-7528B panel (newer, shipped 2024+)
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
    colstart=8,
)

# 2.13" Mono Breakout #4197 — FPC-A002 / GDEY0213B74 panel (legacy)
# display = Adafruit_SSD1680_Grayscale4(
#     122, 250, spi,
#     cs_pin=cs, dc_pin=dc, sramcs_pin=None, rst_pin=rst, busy_pin=busy,
#     vcom=0x1C, colstart=0,
# )

# ─────────────────────────────────────────────────────────────────────────────

display.rotation = 1

W, H = display.width, display.height
BAR = W // 4

print("Drawing 4-bar test pattern...")
display.fill(Adafruit_EPD.WHITE)
display.fill_rect(BAR, 0, BAR, H, Adafruit_EPD.LIGHT)
display.fill_rect(BAR * 2, 0, BAR, H, Adafruit_EPD.DARK)
display.fill_rect(BAR * 3, 0, W - BAR * 3, H, Adafruit_EPD.BLACK)

print("Refreshing...")
t0 = time.monotonic()
display.display()
print(f"Done in {time.monotonic() - t0:.1f}s")
