import digitalio
import busio
import board

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from adafruit_epd.il0373 import Adafruit_IL0373

# create the spi device and pins we will need
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
while not spi.try_lock():
    pass
spi.configure(baudrate=16000000)
spi.unlock()

ecs = digitalio.DigitalInOut(board.D22)
dc = digitalio.DigitalInOut(board.D13)
srcs = digitalio.DigitalInOut(board.D6)
rst = digitalio.DigitalInOut(board.D19)
busy = digitalio.DigitalInOut(board.D26)

# give them all to our driver
display = Adafruit_IL0373(152, 152, rst, dc, busy, srcs, ecs, spi)
# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = display.width
height = display.height
image = Image.new('RGB', (width, height))

WHITE = (0xFF, 0xFF, 0xFF)
RED = (0xFF, 0x00, 0x00)
BLACK = (0x00, 0x00, 0x00)

# clear the buffer
display.clear_buffer()

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
