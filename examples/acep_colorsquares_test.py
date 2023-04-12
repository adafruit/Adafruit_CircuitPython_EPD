# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import digitalio
import busio
import board
import PIL
from PIL import Image
from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.acep_7color import Adafruit_ACEP

#print(dir(board))
# create the spi device and pins we will need
spi = busio.SPI(board.EPD_SCK, MOSI=board.EPD_MOSI, MISO=None)
epd_cs = digitalio.DigitalInOut(board.EPD_CS)
epd_dc = digitalio.DigitalInOut(board.EPD_DC)
epd_reset = digitalio.DigitalInOut(board.EPD_RESET)
epd_busy =  digitalio.DigitalInOut(board.EPD_BUSY)
srcs = None

display = Adafruit_ACEP(600, 448, spi, cs_pin=epd_cs, dc_pin=epd_dc, sramcs_pin=srcs, rst_pin=epd_reset, busy_pin=epd_busy)

display.fill(Adafruit_EPD.WHITE)

display.fill_rect(30, 20, 20, 20, Adafruit_EPD.BLACK)
display.fill_rect(70, 10, 20, 20, Adafruit_EPD.acep_BLUE)
display.fill_rect(110, 10, 20, 20, Adafruit_EPD.acep_RED)
display.fill_rect(150, 10, 20, 20, Adafruit_EPD.acep_GREEN)
display.fill_rect(190, 10, 20, 20, Adafruit_EPD.acep_YELLOW)
display.fill_rect(230, 10, 20, 20, Adafruit_EPD.acep_ORANGE)

display.display()
