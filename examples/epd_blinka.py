import digitalio
import busio
import board

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.il0373 import Adafruit_IL0373
from adafruit_epd.il91874 import Adafruit_IL91874  # pylint: disable=unused-import
from adafruit_epd.il0398 import Adafruit_IL0398    # pylint: disable=unused-import
from adafruit_epd.ssd1608 import Adafruit_SSD1608  # pylint: disable=unused-import
from adafruit_epd.ssd1675 import Adafruit_SSD1675  # pylint: disable=unused-import

# create the spi device and pins we will need
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

ecs = digitalio.DigitalInOut(board.D22)
dc = digitalio.DigitalInOut(board.D13)
srcs = digitalio.DigitalInOut(board.D6)
rst = digitalio.DigitalInOut(board.D19)
busy = digitalio.DigitalInOut(board.D26)


# give them all to our driver
print("Creating display")
#display = Adafruit_SSD1608(200, 200, spi,        # 1.54" HD mono display
#display = Adafruit_SSD1675(122, 250, spi,        # 2.13" HD mono display
#display = Adafruit_IL91874(176, 264, spi,        # 2.7" Tri-color display
#display = Adafruit_IL0373(152, 152, spi,         # 1.54" Tri-color display
#display = Adafruit_IL0373(128, 296, spi,         # 2.9" Tri-color display
#display = Adafruit_IL0398(400, 300, spi,         # 4.2" Tri-color display
display = Adafruit_IL0373(104, 212, spi,          # 2.13" Tri-color display
                          cs_pin=ecs, dc_pin=dc, sramcs_pin=srcs,
                          rst_pin=rst, busy_pin=busy)


# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = display.width
height = display.height
image = Image.new('RGB', (width, height))

WHITE = (0xFF, 0xFF, 0xFF)
RED = (0xFF, 0x00, 0x00)
BLACK = (0x00, 0x00, 0x00)

# clear the buffer
display.fill(Adafruit_EPD.WHITE)

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a white filled box to clear the image.
draw.rectangle((0,0,width,height), outline=BLACK, fill=WHITE)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = 2
shape_width = 30
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = padding
# Draw an ellipse.
draw.ellipse((x, top , x+shape_width, bottom), outline=RED, fill=WHITE)
x += shape_width+padding
# Draw a rectangle.
draw.rectangle((x, top, x+shape_width, bottom), outline=RED, fill=BLACK)
x += shape_width+padding
# Draw a triangle.
draw.polygon([(x, bottom), (x+shape_width/2, top), (x+shape_width, bottom)],
             outline=BLACK, fill=RED)
x += shape_width+padding
# Draw an X.
draw.line((x, bottom, x+shape_width, top), fill=RED)
draw.line((x, top, x+shape_width, bottom), fill=RED)
x += shape_width+padding

# Load default font.
font = ImageFont.load_default()

# Alternatively load a TTF font.  Make sure the .ttf font
# file is in the same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
#font = ImageFont.truetype('Minecraftia.ttf', 8)

# Write two lines of text.
draw.text((x, top),    'Hello',  font=font, fill=RED)
draw.text((x, top+20), 'World!', font=font, fill=RED)

# Display image.
display.image(image)

display.display()
