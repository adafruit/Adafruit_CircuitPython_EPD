# SPDX-FileCopyrightText: 2024
#
# SPDX-License-Identifier: MIT

"""
`adafruit_epd.jd79661` - Adafruit JD79661 - quad-color ePaper display driver
====================================================================================
CircuitPython driver for Adafruit JD79661 quad-color display breakouts
* Author(s): [Your name here]

**Hardware:**
* JD79661 Quad-Color ePaper Display

**Notes on Architecture:**
This is the first quad-color display in the CircuitPython EPD library. Unlike tri-color
displays that use separate buffers for black and red/yellow, the JD79661 uses a single
buffer with 2 bits per pixel to represent 4 colors (black, white, yellow, red).

This driver overrides the parent class's dual-buffer architecture to accommodate the
quad-color packed pixel format. All drawing operations are reimplemented to work with
the 2-bit color depth.
"""

import time

import adafruit_framebuf
from micropython import const

from adafruit_epd.epd import Adafruit_EPD

try:
    """Needed for type annotations"""
    import typing

    from busio import SPI
    from digitalio import DigitalInOut
    from typing_extensions import Literal

except ImportError:
    pass

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_EPD.git"

# Command constants
_JD79661_PANEL_SETTING = const(0x00)
_JD79661_POWER_SETTING = const(0x01)
_JD79661_POWER_OFF = const(0x02)
_JD79661_POWER_ON = const(0x04)
_JD79661_BOOSTER_SOFTSTART = const(0x06)
_JD79661_DEEP_SLEEP = const(0x07)
_JD79661_DATA_START_XMIT = const(0x10)
_JD79661_DISPLAY_REFRESH = const(0x12)
_JD79661_PLL_CONTROL = const(0x30)
_JD79661_CDI = const(0x50)
_JD79661_RESOLUTION = const(0x61)

# Color constants for internal use (2-bit values)
_JD79661_BLACK = const(0b00)
_JD79661_WHITE = const(0b01)
_JD79661_YELLOW = const(0b10)
_JD79661_RED = const(0b11)

# Other command constants from init sequence
_JD79661_POFS = const(0x03)
_JD79661_TCON = const(0x60)
_JD79661_CMD_E7 = const(0xE7)
_JD79661_CMD_E3 = const(0xE3)
_JD79661_CMD_B4 = const(0xB4)
_JD79661_CMD_B5 = const(0xB5)
_JD79661_CMD_E9 = const(0xE9)
_JD79661_CMD_4D = const(0x4D)


class Adafruit_JD79661(Adafruit_EPD):
    """driver class for Adafruit JD79661 quad-color ePaper display breakouts
    
    This driver implements a quad-color display with a single buffer using 2 bits
    per pixel. This differs from the parent class architecture which assumes
    separate buffers for black and color pixels in tri-color displays.
    
    **Color Architecture:**
    - Uses a single buffer with 2 bits per pixel
    - Supports 4 colors: BLACK (0b00), WHITE (0b01), YELLOW (0b10), RED (0b11)
    - All drawing methods are overridden to handle the 2-bit packed pixel format
    - The parent class's dual-buffer methods (_blackframebuf/_colorframebuf) are
      set to the same buffer for compatibility but are not used directly
    """

    # Add color constants for convenience - these match parent class where applicable
    BLACK = const(0)   # 0b00 in the display buffer
    WHITE = const(1)   # 0b01 in the display buffer
    YELLOW = const(2)  # 0b10 in the display buffer  
    RED = const(3)     # 0b11 in the display buffer

    def __init__(
        self,
        width: int,
        height: int,
        spi: SPI,
        *,
        cs_pin: DigitalInOut,
        dc_pin: DigitalInOut,
        sramcs_pin: DigitalInOut,
        rst_pin: DigitalInOut,
        busy_pin: DigitalInOut,
    ) -> None:
        """Initialize the quad-color display driver.
        
        Note: This driver uses a different buffer architecture than the parent class.
        Instead of separate black and color buffers, it uses a single buffer with
        2 bits per pixel to represent 4 colors.
        """
        super().__init__(width, height, spi, cs_pin, dc_pin, sramcs_pin, rst_pin, busy_pin)

        # Adjust width to be divisible by 8 for proper byte alignment
        stride = width
        if stride % 8 != 0:
            stride += 8 - stride % 8

        # For quad-color display, we need 2 bits per pixel
        # So buffer size is width * height / 4 bytes
        self._buffer1_size = int(stride * height / 4)
        self._buffer2_size = 0  # No second buffer for this display

        if sramcs_pin:
            self._buffer1 = self.sram.get_view(0)
            # IMPORTANT: Both buffers point to the same memory for compatibility
            # with parent class, but only _buffer1 is actually used
            self._buffer2 = self._buffer1
        else:
            self._buffer1 = bytearray(self._buffer1_size)
            # IMPORTANT: Both buffers point to the same memory for compatibility
            # with parent class, but only _buffer1 is actually used
            self._buffer2 = self._buffer1

        # Create framebuffers for API compatibility with parent class
        # NOTE: These framebuffers are not used for actual drawing operations
        # since they don't support 2-bit color depth. All drawing is done
        # through overridden methods that directly manipulate the buffer.
        self._framebuf1 = adafruit_framebuf.FrameBuffer(
            self._buffer1,
            width,
            height,
            stride=stride,
            buf_format=adafruit_framebuf.MHMSB,
        )
        self._framebuf2 = self._framebuf1  # Same framebuffer for compatibility
        
        # Set single byte transactions
        self._single_byte_tx = True
        
        # Set up buffer references for parent class compatibility
        # Both point to the same buffer since we don't have separate color planes
        self.set_black_buffer(0, False)
        self.set_color_buffer(0, False)
        
        # Initialize with default fill
        self.fill(Adafruit_JD79661.WHITE)

    def begin(self, reset: bool = True) -> None:
        """Begin communication with the display and set basic settings"""
        if reset:
            self.hardware_reset()
        time.sleep(0.1)
        self.power_down()

    def busy_wait(self) -> None:
        """Wait for display to be done with current task, either by polling the
        busy pin, or pausing. Note: JD79661 busy is HIGH when busy"""
        if self._busy:
            while not self._busy.value:  # Wait for busy HIGH
                time.sleep(0.01)
        else:
            time.sleep(0.5)

    def power_up(self) -> None:
        """Power up the display in preparation for writing RAM and updating"""
        self.hardware_reset()
        self.busy_wait()
        
        # Send initialization sequence
        time.sleep(0.01)  # Wait 10ms
        
        self.command(_JD79661_CMD_4D, bytearray([0x78]))
        self.command(_JD79661_PANEL_SETTING, bytearray([0x8F, 0x29]))  # PSR, Display resolution is 128x250
        self.command(_JD79661_POWER_SETTING, bytearray([0x07, 0x00]))  # PWR
        self.command(_JD79661_POFS, bytearray([0x10, 0x54, 0x44]))  # POFS
        self.command(_JD79661_BOOSTER_SOFTSTART, bytearray([0x05, 0x00, 0x3F, 0x0A, 0x25, 0x12, 0x1A]))
        self.command(_JD79661_CDI, bytearray([0x37]))  # CDI
        self.command(_JD79661_TCON, bytearray([0x02, 0x02]))  # TCON
        self.command(_JD79661_RESOLUTION, bytearray([0, 128, 0, 250]))  # TRES
        self.command(_JD79661_CMD_E7, bytearray([0x1C]))
        self.command(_JD79661_CMD_E3, bytearray([0x22]))
        self.command(_JD79661_CMD_B4, bytearray([0xD0]))
        self.command(_JD79661_CMD_B5, bytearray([0x03]))
        self.command(_JD79661_CMD_E9, bytearray([0x01]))
        self.command(_JD79661_PLL_CONTROL, bytearray([0x08]))
        self.command(_JD79661_POWER_ON)
        
        self.busy_wait()

    def power_down(self) -> None:
        """Power down the display - required when not actively displaying!"""
        # Only deep sleep if we have a reset pin
        if self._rst:
            self.command(_JD79661_POWER_OFF, bytearray([0x00]))
            self.busy_wait()
            self.command(_JD79661_DEEP_SLEEP, bytearray([0xA5]))
            time.sleep(0.1)

    def update(self) -> None:
        """Update the display from internal memory"""
        self.command(_JD79661_DISPLAY_REFRESH, bytearray([0x00]))
        self.busy_wait()
        if not self._busy:
            time.sleep(1)  # Wait 1 second if no busy pin

    def write_ram(self, index: Literal[0, 1]) -> int:
        """Send the one byte command for starting the RAM write process.
        
        Note: The index parameter is ignored since JD79661 uses a single buffer.
        This parameter exists for API compatibility with the parent class.
        """
        # JD79661 uses same command for all data
        return self.command(_JD79661_DATA_START_XMIT, end=False)

    def set_ram_address(self, x: int, y: int) -> None:
        """Set the RAM address location.
        
        Note: Not used on JD79661 chipset. Exists for API compatibility.
        """
        # Not used for JD79661
        pass

    def fill(self, color: int) -> None:
        """Fill the entire display with the specified color.
        
        This method is overridden to handle the 2-bit packed pixel format
        used by the quad-color display.
        
        Args:
            color: Color value (BLACK, WHITE, YELLOW, or RED)
        
        Raises:
            ValueError: If an invalid color is specified
        """
        # Map colors to fill patterns (4 pixels per byte)
        color_map = {
            Adafruit_JD79661.BLACK: 0x00,   # 0b00000000 - all pixels black
            Adafruit_JD79661.WHITE: 0x55,   # 0b01010101 - all pixels white
            Adafruit_JD79661.YELLOW: 0xAA,  # 0b10101010 - all pixels yellow
            Adafruit_JD79661.RED: 0xFF,     # 0b11111111 - all pixels red
        }
        
        if color not in color_map:
            raise ValueError(f"Invalid color: {color}. Use BLACK (0), WHITE (1), YELLOW (2), or RED (3).")
        
        fill_byte = color_map[color]
        
        if self.sram:
            self.sram.erase(0x00, self._buffer1_size, fill_byte)
        else:
            for i in range(self._buffer1_size):
                self._buffer1[i] = fill_byte

    def pixel(self, x: int, y: int, color: int) -> None:
        """Draw a single pixel in the display buffer.
        
        This method is overridden to handle the 2-bit packed pixel format.
        Each byte contains 4 pixels, with 2 bits per pixel.
        
        Args:
            x: X coordinate
            y: Y coordinate  
            color: Color value (BLACK, WHITE, YELLOW, or RED)
        """
        if (x < 0) or (x >= self.width) or (y < 0) or (y >= self.height):
            return

        # Handle rotation
        if self.rotation == 1:
            x, y = y, x
            x = self._width - x - 1
            if self._width % 8 != 0:
                x -= self._width % 8
        elif self.rotation == 2:
            x = self._width - x - 1
            y = self._height - y - 1
            if self._width % 8 != 0:
                x += self._width % 8
        elif self.rotation == 3:
            x, y = y, x
            y = self._height - y - 1

        # Calculate stride (width adjusted to be divisible by 8)
        stride = self._width
        if stride % 8 != 0:
            stride += 8 - stride % 8

        # Map color constants to 2-bit values
        color_map = {
            Adafruit_JD79661.BLACK: _JD79661_BLACK,
            Adafruit_JD79661.WHITE: _JD79661_WHITE,
            Adafruit_JD79661.YELLOW: _JD79661_YELLOW,
            Adafruit_JD79661.RED: _JD79661_RED,
        }
        
        if color not in color_map:
            # Default to white for invalid colors
            pixel_color = _JD79661_WHITE
        else:
            pixel_color = color_map[color]

        # Calculate byte address (4 pixels per byte)
        addr = (x + y * stride) // 4
        
        # Calculate bit offset within byte (2 bits per pixel)
        # Pixels are packed left-to-right, MSB first
        bit_offset = (3 - (x % 4)) * 2
        
        # Create masks
        byte_mask = 0x3 << bit_offset
        byte_value = (pixel_color & 0x3) << bit_offset
        
        # Read, modify, write
        if self.sram:
            current = self.sram.read8(addr)
            current &= ~byte_mask
            current |= byte_value
            self.sram.write8(addr, current)
        else:
            self._buffer1[addr] &= ~byte_mask
            self._buffer1[addr] |= byte_value

    # Override these methods to handle quad-color properly
    def rect(self, x: int, y: int, width: int, height: int, color: int) -> None:
        """Draw a rectangle.
        
        Overridden to use the quad-color pixel method.
        """
        for i in range(x, x + width):
            self.pixel(i, y, color)
            self.pixel(i, y + height - 1, color)
        for j in range(y + 1, y + height - 1):
            self.pixel(x, j, color)
            self.pixel(x + width - 1, j, color)

    def fill_rect(self, x: int, y: int, width: int, height: int, color: int) -> None:
        """Fill a rectangle with the passed color.
        
        Overridden to use the quad-color pixel method.
        """
        for i in range(x, x + width):
            for j in range(y, y + height):
                self.pixel(i, j, color)

    def line(self, x_0: int, y_0: int, x_1: int, y_1: int, color: int) -> None:
        """Draw a line from (x_0, y_0) to (x_1, y_1) in passed color.
        
        Overridden to use the quad-color pixel method.
        """
        # Bresenham's line algorithm
        dx = abs(x_1 - x_0)
        dy = abs(y_1 - y_0)
        sx = 1 if x_0 < x_1 else -1
        sy = 1 if y_0 < y_1 else -1
        err = dx - dy
        
        while True:
            self.pixel(x_0, y_0, color)
            if x_0 == x_1 and y_0 == y_1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x_0 += sx
            if e2 < dx:
                err += dx
                y_0 += sy

    def text(
        self,
        string: str,
        x: int,
        y: int,
        color: int,
        *,
        font_name: str = "font5x8.bin",
        size: int = 1,
    ) -> None:
        """Write text string at location (x, y) in given color, using font file.
        
        This method is for CircuitPython's built-in bitmap fonts only.
        For TrueType fonts, use PIL/Pillow to draw text on an image and then
        display the image using the image() method.
        """
        # Validate color
        if color not in [Adafruit_JD79661.BLACK, Adafruit_JD79661.WHITE, 
                         Adafruit_JD79661.YELLOW, Adafruit_JD79661.RED]:
            raise ValueError(f"Invalid color: {color}. Use BLACK (0), WHITE (1), YELLOW (2), or RED (3).")
        
        # Since we can't use the parent's framebuffer text method directly
        # (it only supports 1-bit depth), we need to render to a temporary buffer
        # and then copy the pixels in the requested color
        
        # Estimate text dimensions
        text_width = len(string) * 6 * size  # ~6 pixels per char
        text_height = 8 * size  # 8 pixel high font
        
        # Bounds check
        text_width = min(text_width, self.width - x)
        text_height = min(text_height, self.height - y)
        
        if text_width <= 0 or text_height <= 0:
            return
        
        # Create temporary monochrome buffer
        temp_buf_width = ((text_width + 7) // 8) * 8
        temp_buf = bytearray((temp_buf_width * text_height) // 8)
        
        # Create temporary framebuffer
        temp_fb = adafruit_framebuf.FrameBuffer(
            temp_buf,
            temp_buf_width,
            text_height,
            buf_format=adafruit_framebuf.MHMSB
        )
        
        # Render text
        temp_fb.fill(0)
        temp_fb.text(string, 0, 0, 1, font_name=font_name, size=size)
        
        # Copy pixels in the requested color
        for j in range(text_height):
            for i in range(text_width):
                byte_index = (j * temp_buf_width + i) // 8
                bit_index = 7 - ((j * temp_buf_width + i) % 8)
                
                if byte_index < len(temp_buf):
                    if (temp_buf[byte_index] >> bit_index) & 1:
                        self.pixel(x + i, y + j, color)

    def image(self, image: Image) -> None:
        """Set buffer to value of Python Imaging Library image.  The image should
        be in RGB mode and a size equal to the display size.
        """
        imwidth, imheight = image.size
        if imwidth != self.width or imheight != self.height:
            raise ValueError(
                f"Image must be same dimensions as display ({self.width}x{self.height})."
            )
        if self.sram:
            raise RuntimeError("PIL image is not for use with SRAM assist")
        # Grab all the pixels from the image, faster than getpixel.
        pix = image.load()
        # clear out any display buffers
        self.fill(Adafruit_EPD.WHITE)

        if image.mode == "RGB":  # RGB Mode
            for y in range(image.size[1]):
                for x in range(image.size[0]):
                    pixel = pix[x, y]
                    # Check for yellow first (high red + green, low blue)
                    if (pixel[0] >= 0x80) and (pixel[1] >= 0x80) and (pixel[2] < 0x80):
                        # yellowish
                        self.pixel(x, y, Adafruit_JD79661.YELLOW)
                    # Then check for red (high red, low green and blue)
                    elif (pixel[0] >= 0x80) and (pixel[1] < 0x80) and (pixel[2] < 0x80):
                        # reddish
                        self.pixel(x, y, Adafruit_JD79661.RED)
                    # Then black (all low)
                    elif (pixel[0] < 0x80) and (pixel[1] < 0x80) and (pixel[2] < 0x80):
                        # dark
                        self.pixel(x, y, Adafruit_JD79661.BLACK)
                    # else: remains white (from fill)
                    
        elif image.mode == "L":  # Grayscale
            for y in range(image.size[1]):
                for x in range(image.size[0]):
                    pixel = pix[x, y]
                    if pixel < 0x40:  # 0-63
                        self.pixel(x, y, Adafruit_JD79661.BLACK)
                    elif pixel < 0x80:  # 64-127
                        self.pixel(x, y, Adafruit_JD79661.YELLOW)
                    elif pixel < 0xC0:  # 128-191
                        self.pixel(x, y, Adafruit_JD79661.RED)
                    # else: 192-255 remains white
        else:
            raise ValueError("Image must be in mode RGB or mode L.")

    def image_dithered(self, image, dither_type="floyd-steinberg") -> None:
        """Display an image with dithering to better represent colors/shades.
        
        This method converts the image to use only the 4 available colors
        using error diffusion dithering for better visual quality.
        
        Args:
            image: PIL Image object
            dither_type: Type of dithering - "floyd-steinberg" or "simple"
            
        Raises:
            ValueError: If image dimensions don't match display
            RuntimeError: If SRAM is being used (not supported)
        """
        imwidth, imheight = image.size
        if imwidth != self.width or imheight != self.height:
            raise ValueError(
                f"Image must be same dimensions as display ({self.width}x{self.height})."
            )
        if self.sram:
            raise RuntimeError("PIL image dithering is not supported with SRAM assist")
        
        # Convert to RGB if not already
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Define our 4 color palette in RGB
        palette = [
            (0, 0, 0),       # BLACK
            (255, 255, 255), # WHITE
            (255, 255, 0),   # YELLOW
            (255, 0, 0),     # RED
        ]
        
        # Create a working copy of the image as a list of lists
        pixels = []
        for y in range(imheight):
            row = []
            for x in range(imwidth):
                r, g, b = image.getpixel((x, y))
                row.append([r, g, b])
            pixels.append(row)
        
        if dither_type == "floyd-steinberg":
            # Floyd-Steinberg dithering
            for y in range(imheight):
                for x in range(imwidth):
                    old_pixel = pixels[y][x]
                    
                    # Find closest color in palette
                    min_dist = float('inf')
                    closest_color = 0
                    closest_rgb = palette[0]
                    
                    for i, pal_color in enumerate(palette):
                        dist = sum((old_pixel[j] - pal_color[j])**2 for j in range(3))
                        if dist < min_dist:
                            min_dist = dist
                            closest_color = i
                            closest_rgb = pal_color
                    
                    # Set pixel to closest color
                    self.pixel(x, y, closest_color)
                    
                    # Calculate error
                    error = [old_pixel[i] - closest_rgb[i] for i in range(3)]
                    
                    # Distribute error to neighboring pixels
                    if x + 1 < imwidth:
                        for i in range(3):
                            pixels[y][x + 1][i] += error[i] * 7 / 16
                    
                    if y + 1 < imheight:
                        if x > 0:
                            for i in range(3):
                                pixels[y + 1][x - 1][i] += error[i] * 3 / 16
                        
                        for i in range(3):
                            pixels[y + 1][x][i] += error[i] * 5 / 16
                        
                        if x + 1 < imwidth:
                            for i in range(3):
                                pixels[y + 1][x + 1][i] += error[i] * 1 / 16
        
        else:  # Simple nearest-color mapping
            for y in range(imheight):
                for x in range(imwidth):
                    pixel = pixels[y][x]
                    
                    # Find closest color in palette
                    min_dist = float('inf')
                    closest_color = 0
                    
                    for i, pal_color in enumerate(palette):
                        dist = sum((pixel[j] - pal_color[j])**2 for j in range(3))
                        if dist < min_dist:
                            min_dist = dist
                            closest_color = i
                    
                    self.pixel(x, y, closest_color)

    # Parent class drawing method overrides for documentation
    def set_black_buffer(self, index: Literal[0, 1], inverted: bool) -> None:
        """Set the index for the black buffer data.
        
        Note: This method exists for API compatibility but has no effect on the
        JD79661 since it uses a single buffer with 2-bit color depth rather than
        separate black/color buffers.
        """
        super().set_black_buffer(index, inverted)

    def set_color_buffer(self, index: Literal[0, 1], inverted: bool) -> None:
        """Set the index for the color buffer data.
        
        Note: This method exists for API compatibility but has no effect on the
        JD79661 since it uses a single buffer with 2-bit color depth rather than
        separate black/color buffers.
        """
        super().set_color_buffer(index, inverted)