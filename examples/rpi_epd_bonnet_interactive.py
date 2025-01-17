# SPDX-FileCopyrightText: 2024 Joel Miller for Adafruit Industries
# SPDX-License-Identifier: MIT

# pylint: disable=line-too-long
"""
A minimalist example for tinkering with eInk displays interactively on a Raspberry Pi.

1. Install system packages for working with Python programs and images

    ```bash
    sudo apt update
    sudo apt install -y python3-dev python3-pil python3-venv

    ```

2. Create and activate a Python virtual environment (named `examples`)

    ```bash
    python3 -m venv --system-site-packages --upgrade-deps ./examples
    source ./examples/bin/activate
    ```

3. Install the Adafruit CircuitPython EPD package

    ```bash
    pip install adafruit-circuitpython-epd
    ```

4. Download this script and some example images from GitHub

    ```bash
    wget https://raw.githubusercontent.com/adafruit/Adafruit_CircuitPython_EPD/refs/heads/main/examples/rpi_epd_bonnet_interactive.py
    wget https://raw.githubusercontent.com/adafruit/Adafruit_CircuitPython_EPD/refs/heads/main/examples/epd_bonnet_blinka_250x122.bmp
    wget https://raw.githubusercontent.com/adafruit/Adafruit_CircuitPython_EPD/refs/heads/main/examples/epd_bonnet_grid_250x122.bmp
    ```

5. Try it out!

    ```bash
    python -i rpi_epd_bonnet_interactive.py
    ```
"""

import board
from busio import SPI
from digitalio import DigitalInOut

try:
    from PIL import Image  # pylint: disable=unused-import
except ImportError:
    print("Failed to import Pillow (PIL), the image examples below will not work.")


INTERACTIVE_EXAMPLES_HELP = """# EXAMPLES

# Fill the entire display with black pixels:
>>> display.fill(display.BLACK)
>>> display.display()

# Fill the entire display with white pixels:
>>> display.fill(display.WHITE)
>>> display.display()

# Display the example grid image:
>>> display.image(Image.open("epd_bonnet_grid_250x122.bmp"))
>>> display.display()

# Display the example blinka image:
>>> display.image(Image.open("epd_bonnet_blinka_250x122.bmp"))
>>> display.display()

# If you want to try a different driver: import, setup, repeat:
>>> from adafruit_epd.ssd1675 import Adafruit_SSD1675
>>> display = setup_display(Adafruit_SSD1675)

# To quit out of this interactive prompt:
>>> exit()

# Try it yourself!
"""


def setup_display(driver_class, width=122, height=250):
    disp = driver_class(
        width=width,
        height=height,
        spi=SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO),
        cs_pin=DigitalInOut(board.CE0),
        dc_pin=DigitalInOut(board.D22),
        sramcs_pin=None,
        rst_pin=DigitalInOut(board.D27),
        busy_pin=DigitalInOut(board.D17),
    )
    disp.rotation = 1
    return disp


if __name__ == "__main__":
    from adafruit_epd.ssd1680b import Adafruit_SSD1680B

    display = setup_display(Adafruit_SSD1680B)
    print(INTERACTIVE_EXAMPLES_HELP)
