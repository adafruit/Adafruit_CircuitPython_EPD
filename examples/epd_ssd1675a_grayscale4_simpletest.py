# SPDX-FileCopyrightText: 2025 Adafruit Industries
# SPDX-License-Identifier: MIT

"""
4-level grayscale testcard for the Adafruit 2.13" eInk FeatherWing
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
import displayio

from adafruit_epd.ssd1675a_grayscale4 import Adafruit_SSD1675A_Grayscale4

displayio.release_displays()

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
display.rotation = 1  # landscape: width=250, height=122

WHITE      = Adafruit_SSD1675A_Grayscale4.WHITE
LIGHT_GRAY = Adafruit_SSD1675A_Grayscale4.LIGHT_GRAY
DARK_GRAY  = Adafruit_SSD1675A_Grayscale4.DARK_GRAY
BLACK      = Adafruit_SSD1675A_Grayscale4.BLACK

W = display.width   # 250
H = display.height  # 122

# Column x-starts and row y-starts
C0, C1, C2, C3 = 0, 62, 125, 188
R_HDR, R_BARS, R_DITH, R_CHK = 0, 14, 56, 98

print("Drawing testcard")
display.fill(WHITE)

# Header: black bar with white text
display.fill_rect(0, R_HDR, W, 14, BLACK)
display.text("SSD1675A  pux4j LUT  VCOM=0x28", 4, 4, WHITE)

# Solid gray bars
display.fill_rect(C0, R_BARS, 62, 42, WHITE)
display.fill_rect(C1, R_BARS, 63, 42, LIGHT_GRAY)
display.fill_rect(C2, R_BARS, 63, 42, DARK_GRAY)
display.fill_rect(C3, R_BARS, 62, 42, BLACK)

# Horizontal-line dither rows (42 rows, alternating each column pair)
for row in range(R_DITH, R_DITH + 42):
    e = row % 2 == 0
    display.fill_rect(C0, row, 62, 1, WHITE      if e else BLACK)
    display.fill_rect(C1, row, 63, 1, WHITE      if e else LIGHT_GRAY)
    display.fill_rect(C2, row, 63, 1, LIGHT_GRAY if e else DARK_GRAY)
    display.fill_rect(C3, row, 62, 1, DARK_GRAY  if e else BLACK)

# 2-pixel checkerboard (bottom two bands)
for by in range(R_CHK, H, 2):
    for bx in range(0, W, 2):
        c = WHITE if ((bx // 2) + (by // 2)) % 2 == 0 else BLACK
        display.fill_rect(bx, by, 2, 2, c)

# Grid lines
for y in range(R_BARS, H):
    display.pixel(C1, y, BLACK)
    display.pixel(C2, y, BLACK)
    display.pixel(C3, y, BLACK)
for x in range(W):
    display.pixel(x, R_BARS, BLACK)
    display.pixel(x, R_DITH, BLACK)
    display.pixel(x, R_CHK, BLACK)

print("Refreshing display (~6 s)...")
display.display()
print("Done")
