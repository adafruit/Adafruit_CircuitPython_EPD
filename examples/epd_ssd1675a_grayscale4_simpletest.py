# SPDX-FileCopyrightText: 2025 Adafruit Industries
# SPDX-License-Identifier: MIT

"""
4-level grayscale example for the Adafruit 2.13" eInk FeatherWing
pre-April 2020 revision (controller: SSD1675A / IL3897).

Identify your hardware: read the FPC ribbon label on the panel edge.
  "HINK E0213A22-A0" → SSD1675A — use this example
  Any Good Display label (GDEY0213B74, etc.) → SSD1680 — use Adafruit_SSD1680

Wiring (FeatherWing plugs directly onto any Feather):
  SCK  → SCK    MOSI → MOSI
  CS   → D9     DC   → D10
  RST  → D11    BUSY → D12
"""

import board
import busio
import digitalio

from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.ssd1675a_grayscale4 import Adafruit_SSD1675A_Grayscale4

spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
ecs = digitalio.DigitalInOut(board.D9)
dc = digitalio.DigitalInOut(board.D10)
srcs = None  # no SRAM on FeatherWing (use digitalio.DigitalInOut(board.D6) if present)
rst = digitalio.DigitalInOut(board.D11)
busy = digitalio.DigitalInOut(board.D12)

print("Creating display")
display = Adafruit_SSD1675A_Grayscale4(
    122, 250,  # 2.13" 4-gray display (HINK E0213A22-A0, pre-April 2020)
    spi,
    cs_pin=ecs,
    dc_pin=dc,
    sramcs_pin=srcs,
    rst_pin=rst,
    busy_pin=busy,
)

# Four gray levels — use these instead of the 2-color Adafruit_EPD constants
WHITE = Adafruit_SSD1675A_Grayscale4.WHITE        # L0 — lightest
LIGHT_GRAY = Adafruit_SSD1675A_Grayscale4.LIGHT_GRAY  # L1
DARK_GRAY = Adafruit_SSD1675A_Grayscale4.DARK_GRAY    # L2
BLACK = Adafruit_SSD1675A_Grayscale4.BLACK        # L3 — darkest

print("Clear buffer")
display.fill(WHITE)

print("Draw rectangles")
display.fill_rect(5, 5, 50, 50, LIGHT_GRAY)
display.fill_rect(60, 5, 50, 50, DARK_GRAY)
display.fill_rect(5, 60, 50, 50, BLACK)
display.rect(60, 60, 50, 50, DARK_GRAY)

print("Draw lines")
display.line(0, 0, display.width - 1, display.height - 1, BLACK)
display.line(0, display.height - 1, display.width - 1, 0, DARK_GRAY)

print("Draw text")
display.text("4-gray!", 25, 120, BLACK)

print("Refreshing display (~6 s)...")
display.display()
print("Done")
