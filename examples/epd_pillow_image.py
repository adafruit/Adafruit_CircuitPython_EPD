# SPDX-FileCopyrightText: 2019 Melissa LeBlanc-Williams for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
Image resizing and drawing using the Pillow Library. For the image, check out the
associated Adafruit Learn guide at:
https://learn.adafruit.com/adafruit-eink-display-breakouts/python-code

"""

import board
import busio
import digitalio
from PIL import Image

from adafruit_epd.ek79686 import Adafruit_EK79686
from adafruit_epd.il0373 import Adafruit_IL0373
from adafruit_epd.il0398 import Adafruit_IL0398
from adafruit_epd.il91874 import Adafruit_IL91874
from adafruit_epd.jd79661 import Adafruit_JD79661
from adafruit_epd.ssd1608 import Adafruit_SSD1608
from adafruit_epd.ssd1675 import Adafruit_SSD1675
from adafruit_epd.ssd1680 import Adafruit_SSD1680, Adafruit_SSD1680Z
from adafruit_epd.ssd1681 import Adafruit_SSD1681
from adafruit_epd.uc8151d import Adafruit_UC8151D

# create the spi device and pins we will need
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
ecs = digitalio.DigitalInOut(board.CE0)
dc = digitalio.DigitalInOut(board.D22)
srcs = None
rst = digitalio.DigitalInOut(board.D27)
busy = digitalio.DigitalInOut(board.D17)

# give them all to our driver
# display = Adafruit_JD79661(122, 150,        # 2.13" Quad-color display
# display = Adafruit_SSD1608(200, 200,        # 1.54" HD mono display
# display = Adafruit_SSD1675(122, 250,        # 2.13" HD mono display
# display = Adafruit_SSD1680(122, 250,        # 2.13" HD Tri-color or mono display
# display = Adafruit_SSD1680Z(122, 250,       # Newer 2.13" mono display
# display = Adafruit_SSD1681(200, 200,        # 1.54" HD Tri-color display
# display = Adafruit_IL91874(176, 264,        # 2.7" Tri-color display
# display = Adafruit_EK79686(176, 264,        # 2.7" Tri-color display
# display = Adafruit_IL0373(152, 152,         # 1.54" Tri-color display
# display = Adafruit_UC8151D(128, 296,        # 2.9" mono flexible display
# display = Adafruit_IL0373(128, 296,         # 2.9" Tri-color display IL0373
# display = Adafruit_SSD1680(128, 296,        # 2.9" Tri-color display SSD1680
# display = Adafruit_IL0398(400, 300,         # 4.2" Tri-color display
display = Adafruit_IL0373(
    104,
    212,  # 2.13" Tri-color display
    spi,
    cs_pin=ecs,
    dc_pin=dc,
    sramcs_pin=srcs,
    rst_pin=rst,
    busy_pin=busy,
)

# IF YOU HAVE A 2.13" FLEXIBLE DISPLAY uncomment these lines!
# display.set_black_buffer(1, False)
# display.set_color_buffer(1, False)

# IF YOU HAVE A 2.9" FLEXIBLE DISPLAY uncomment these lines!
# display.set_black_buffer(1, True)
# display.set_color_buffer(1, True)

display.rotation = 1

image = Image.open("blinka.png")

# Scale the image to the smaller screen dimension
image_ratio = image.width / image.height
screen_ratio = display.width / display.height
if screen_ratio < image_ratio:
    scaled_width = image.width * display.height // image.height
    scaled_height = display.height
else:
    scaled_width = display.width
    scaled_height = image.height * display.width // image.width
image = image.resize((scaled_width, scaled_height), Image.BICUBIC)

# Crop and center the image
x = scaled_width // 2 - display.width // 2
y = scaled_height // 2 - display.height // 2
image = image.crop((x, y, x + display.width, y + display.height)).convert("RGB")

# Convert to Monochrome and Add dithering
# image = image.convert("1").convert("L")

if type(display) == Adafruit_JD79661:
    # Create a palette with the 4 colors: Black, White, Red, Yellow
    # The palette needs 768 values (256 colors × 3 channels)
    palette = []

    # We'll map the 256 palette indices to our 4 colors
    # 0-63: Black, 64-127: Red, 128-191: Yellow, 192-255: White
    for i in range(256):
        if i < 64:
            palette.extend([0, 0, 0])  # Black
        elif i < 128:
            palette.extend([255, 0, 0])  # Red
        elif i < 192:
            palette.extend([255, 255, 0])  # Yellow
        else:
            palette.extend([255, 255, 255])  # White

    # Create a palette image
    palette_img = Image.new("P", (1, 1))
    palette_img.putpalette(palette)

    # Optional: Enhance colors before dithering for better results
    # from PIL import ImageEnhance
    # enhancer = ImageEnhance.Color(image)
    # image = enhancer.enhance(1.5)  # Increase color saturation

    # Quantize the image using Floyd-Steinberg dithering
    image = image.quantize(palette=palette_img, dither=Image.FLOYDSTEINBERG)

    # Convert back to RGB for the display driver
    image = image.convert("RGB")

# Display image.
display.image(image)
display.display()
