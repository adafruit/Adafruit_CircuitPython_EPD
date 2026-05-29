# SPDX-FileCopyrightText: 2018 Dean Miller for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_epd.ssd1680` - Adafruit SSD1680 - ePaper display driver
====================================================================================
CircuitPython driver for Adafruit SSD1680 display breakouts
* Author(s): Melissa LeBlanc-Williams
"""

import time

import adafruit_framebuf
from micropython import const

from adafruit_epd.epd import Adafruit_EPD

# for backwards compatibility
from adafruit_epd.ssd1680b import Adafruit_SSD1680B as Adafruit_SSD1680Z

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

_SSD1680_DRIVER_CONTROL = const(0x01)
_SSD1680_GATE_VOLTAGE = const(0x03)
_SSD1680_SOURCE_VOLTAGE = const(0x04)
_SSD1680_INIT_SETTING = const(0x08)
_SSD1680_INIT_WRITE_REG = const(0x09)
_SSD1680_INIT_READ_REG = const(0x0A)
_SSD1680_BOOSTER_SOFT_START = const(0x0C)
_SSD1680_DEEP_SLEEP = const(0x10)
_SSD1680_DATA_MODE = const(0x11)
_SSD1680_SW_RESET = const(0x12)
_SSD1680_HV_DETECT = const(0x14)
_SSD1680_VCI_DETECT = const(0x15)
_SSD1680_TEMP_CONTROL = const(0x18)
_SSD1680_TEMP_WRITE = const(0x1A)
_SSD1680_TEMP_READ = const(0x1B)
_SSD1680_EXTTEMP_WRITE = const(0x1C)
_SSD1680_MASTER_ACTIVATE = const(0x20)
_SSD1680_DISP_CTRL1 = const(0x21)
_SSD1680_DISP_CTRL2 = const(0x22)
_SSD1680_WRITE_BWRAM = const(0x24)
_SSD1680_WRITE_REDRAM = const(0x26)
_SSD1680_READ_RAM = const(0x27)
_SSD1680_VCOM_SENSE = const(0x28)
_SSD1680_VCOM_DURATION = const(0x29)
_SSD1680_WRITE_VCOM_OTP = const(0x2A)
_SSD1680_WRITE_VCOM_CTRL = const(0x2B)
_SSD1680_WRITE_VCOM_REG = const(0x2C)
_SSD1680_READ_OTP = const(0x2D)
_SSD1680_READ_USERID = const(0x2E)
_SSD1680_READ_STATUS = const(0x2F)
_SSD1680_WRITE_WS_OTP = const(0x30)
_SSD1680_LOAD_WS_OTP = const(0x31)
_SSD1680_WRITE_LUT = const(0x32)
_SSD1680_CRC_CALC = const(0x34)
_SSD1680_CRC_READ = const(0x35)
_SSD1680_PROG_OTP = const(0x36)
_SSD1680_WRITE_DISPLAY_OPT = const(0x37)
_SSD1680_WRITE_USERID = const(0x38)
_SSD1680_OTP_PROGMODE = const(0x39)
_SSD1680_WRITE_BORDER = const(0x3C)
_SSD1680_END_OPTION = const(0x3F)
_SSD1680_READ_RAM_OPT = const(0x41)
_SSD1680_SET_RAMXPOS = const(0x44)
_SSD1680_SET_RAMYPOS = const(0x45)
_SSD1680_AUTOWRITE_RED = const(0x46)
_SSD1680_AUTOWRITE_BW = const(0x47)
_SSD1680_SET_RAMXCOUNT = const(0x4E)
_SSD1680_SET_RAMYCOUNT = const(0x4F)
_SSD1680_NOP = const(0x7F)


class Adafruit_SSD1680(Adafruit_EPD):
    """driver class for Adafruit SSD1680 ePaper display breakouts"""

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
        super().__init__(width, height, spi, cs_pin, dc_pin, sramcs_pin, rst_pin, busy_pin)

        stride = width
        if stride % 8 != 0:
            stride += 8 - stride % 8

        self._buffer1_size = int(stride * height / 8)
        self._buffer2_size = self._buffer1_size

        if sramcs_pin:
            self._buffer1 = self.sram.get_view(0)
            self._buffer2 = self.sram.get_view(self._buffer1_size)
        else:
            self._buffer1 = bytearray(self._buffer1_size)
            self._buffer2 = bytearray(self._buffer2_size)

        self._framebuf1 = adafruit_framebuf.FrameBuffer(
            self._buffer1,
            width,
            height,
            stride=stride,
            buf_format=adafruit_framebuf.MHMSB,
        )
        self._framebuf2 = adafruit_framebuf.FrameBuffer(
            self._buffer2,
            width,
            height,
            stride=stride,
            buf_format=adafruit_framebuf.MHMSB,
        )
        self.set_black_buffer(0, True)
        self.set_color_buffer(1, False)
        # pylint: enable=too-many-arguments

    def begin(self, reset: bool = True) -> None:
        """Begin communication with the display and set basic settings"""
        if reset:
            self.hardware_reset()
        self.power_down()

    def busy_wait(self) -> None:
        """Wait for display to be done with current task, either by polling the
        busy pin, or pausing"""
        if self._busy:
            while self._busy.value:
                time.sleep(0.01)
        else:
            time.sleep(0.5)

    def power_up(self) -> None:
        """Power up the display in preparation for writing RAM and updating"""
        self.hardware_reset()
        self.busy_wait()
        self.command(_SSD1680_SW_RESET)
        self.busy_wait()
        # driver output control
        self.command(
            _SSD1680_DRIVER_CONTROL,
            bytearray([(self._height - 1) & 0xFF, (self._height - 1) >> 8, 0x00]),
        )
        # data entry mode
        self.command(_SSD1680_DATA_MODE, bytearray([0x03]))

        # Set voltages
        self.command(_SSD1680_WRITE_VCOM_REG, bytearray([0x36]))
        self.command(_SSD1680_GATE_VOLTAGE, bytearray([0x17]))
        self.command(_SSD1680_SOURCE_VOLTAGE, bytearray([0x41, 0x00, 0x32]))

        height = self._width
        if height % 8 != 0:
            height += 8 - (height % 8)
        # Set ram X start/end postion
        self.command(_SSD1680_SET_RAMXPOS, bytearray([0x00, (height // 8) - 1]))
        # Set ram Y start/end postion
        self.command(
            _SSD1680_SET_RAMYPOS,
            bytearray([0x00, 0x00, (self._height - 1) & 0xFF, (self._height - 1) >> 8]),
        )
        # Set border waveform
        self.command(_SSD1680_WRITE_BORDER, bytearray([0x05]))

        # Set ram X count
        self.command(_SSD1680_SET_RAMXCOUNT, bytearray([0x00]))
        # Set ram Y count
        self.command(_SSD1680_SET_RAMYCOUNT, bytearray([0x00, 0x00]))
        self.busy_wait()

    def power_down(self) -> None:
        """Power down the display - required when not actively displaying!"""
        self.command(_SSD1680_DEEP_SLEEP, bytearray([0x01]))
        time.sleep(0.1)

    def update(self) -> None:
        """Update the display from internal memory"""
        self.command(_SSD1680_DISP_CTRL2, bytearray([0xF4]))
        self.command(_SSD1680_MASTER_ACTIVATE)
        self.busy_wait()
        if not self._busy:
            time.sleep(3)  # wait 3 seconds

    def write_ram(self, index: Literal[0, 1]) -> int:
        """Send the one byte command for starting the RAM write process. Returns
        the byte read at the same time over SPI. index is the RAM buffer, can be
        0 or 1 for tri-color displays."""
        if index == 0:
            return self.command(_SSD1680_WRITE_BWRAM, end=False)
        if index == 1:
            return self.command(_SSD1680_WRITE_REDRAM, end=False)
        raise RuntimeError("RAM index must be 0 or 1")

    def set_ram_address(self, x: int, y: int) -> None:  # noqa: PLR6301, F841
        """Set the RAM address location, not used on this chipset but required by
        the superclass"""
        # Set RAM X address counter
        self.command(_SSD1680_SET_RAMXCOUNT, bytearray([0]))
        # Set RAM Y address counter
        self.command(_SSD1680_SET_RAMYCOUNT, bytearray([0, 0]))


# 4-gray waveform LUT for GDEY0213B74 (SSD1680, FPC-A002).
# Source: GxEPD2_4G lut_4G[] adapted for CircuitPython polarity convention:
#   - L0↔L3 VS rows swapped  (GxEPD2: L0=white, L3=black; CP: luma 0→L0=black)
#   - L1↔L2 VS rows also swapped  (required for correct grey ordering on this panel)
# DC balance byte 0x48 (alternating VSH1/GND/VSL/GND) eliminates speckle.
_SSD1680_GRAY4_LUT = bytes(
    [
        # VS rows (5 × 12 = 60 bytes)
        0x20,
        0x48,
        0x01,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,  # L0 black
        0x02,
        0x48,
        0x04,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,  # L1 light grey
        0x08,
        0x48,
        0x10,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,  # L2 dark grey
        0x40,
        0x48,
        0x80,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,  # L3 white
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,  # L4 VCOM
        # TP timing groups (12 × 7 = 84 bytes)
        0x0A,
        0x19,
        0x00,
        0x03,
        0x08,
        0x00,
        0x00,
        0x14,
        0x01,
        0x00,
        0x14,
        0x01,
        0x00,
        0x03,
        0x0A,
        0x03,
        0x00,
        0x08,
        0x19,
        0x00,
        0x00,
        0x01,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x01,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        # XON/FR (9 bytes)
        0x22,
        0x22,
        0x22,
        0x22,
        0x22,
        0x22,
        0x00,
        0x00,
        0x00,
    ]
)


class Adafruit_SSD1680_Grayscale4(Adafruit_SSD1680):
    """4-gray (2-bit grayscale) driver for SSD1680-based 2.13" eInk panels.

    Uses the GxEPD2 _Init_4G waveform with L0↔L3 and L1↔L2 VS row swaps for
    CircuitPython polarity (luma 0 → L0=black, luma 255 → L3=white).

    Supports Adafruit_EPD color constants BLACK, DARK, LIGHT, WHITE for drawing,
    and accepts mode-L PIL images via image().

    RAM encoding (BW RAM × RED RAM → gray level):
        BW=0, RED=0 → L0 (black)
        BW=1, RED=0 → L2 (dark grey)
        BW=0, RED=1 → L1 (light grey)
        BW=1, RED=1 → L3 (white)

    :param colstart: RAM column byte offset for panel alignment.
        0 for FPC-A002/GDEY0213B74 (default, original #4687 bonnet panel).
        8 for FPC-7528B and FPC-7519rev.b panels (#4197 breakout, MagTag).
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        width: int,
        height: int,
        spi: "SPI",
        *,
        cs_pin: "DigitalInOut",
        dc_pin: "DigitalInOut",
        sramcs_pin: "DigitalInOut",
        rst_pin: "DigitalInOut",
        busy_pin: "DigitalInOut",
        vcom: int = 0x1C,
        colstart: int = 0,
    ) -> None:
        super().__init__(
            width,
            height,
            spi,
            cs_pin=cs_pin,
            dc_pin=dc_pin,
            sramcs_pin=sramcs_pin,
            rst_pin=rst_pin,
            busy_pin=busy_pin,
        )
        self._vcom = vcom
        self._colstart = colstart
        # pylint: enable=too-many-arguments

    def power_up(self) -> None:
        """Power up with GxEPD2 _Init_4G() sequence and write the 4-gray LUT."""
        self.hardware_reset()
        self.busy_wait()
        self.command(_SSD1680_SW_RESET)
        self.busy_wait()

        self.command(0x74, bytearray([0x54]))  # analog block control
        self.command(0x7E, bytearray([0x3B]))  # digital block control
        # Gate driver MUX=295 required for 4G waveform on 2.13" panels
        self.command(_SSD1680_DRIVER_CONTROL, bytearray([0x27, 0x01, 0x00]))
        self.command(_SSD1680_DATA_MODE, bytearray([0x03]))  # X-inc, Y-inc

        # RAM window accounting for colstart byte offset
        x_start = self._colstart // 8
        x_end = (self._colstart + self._width + 7) // 8 - 1
        self.command(_SSD1680_SET_RAMXPOS, bytearray([x_start, x_end]))
        self.command(
            _SSD1680_SET_RAMYPOS,
            bytearray([0x00, 0x00, (self._height - 1) & 0xFF, (self._height - 1) >> 8]),
        )

        self.command(_SSD1680_WRITE_BORDER, bytearray([0x00]))
        self.command(_SSD1680_WRITE_VCOM_REG, bytearray([self._vcom]))
        self.command(_SSD1680_END_OPTION, bytearray([0x22]))  # EOPQ
        self.command(_SSD1680_GATE_VOLTAGE, bytearray([0x17]))
        self.command(_SSD1680_SOURCE_VOLTAGE, bytearray([0x41, 0x00, 0x32]))
        # Enable RED RAM as second source for 4-gray
        self.command(_SSD1680_DISP_CTRL1, bytearray([0x00, 0x80]))
        self.command(_SSD1680_WRITE_LUT, bytearray(_SSD1680_GRAY4_LUT))

        # Reset RAM address counters to (colstart_byte, 0)
        self.command(_SSD1680_SET_RAMXCOUNT, bytearray([self._colstart // 8]))
        self.command(_SSD1680_SET_RAMYCOUNT, bytearray([0x00, 0x00]))

    def set_ram_address(self, x: int, y: int) -> None:
        """Reset RAM address counters respecting colstart."""
        self.command(_SSD1680_SET_RAMXCOUNT, bytearray([x]))
        self.command(_SSD1680_SET_RAMYCOUNT, bytearray([y, y >> 8]))

    def update(self) -> None:
        """Trigger display refresh using the custom LUT loaded in power_up."""
        self.command(_SSD1680_DISP_CTRL2, bytearray([0xC7]))  # custom LUT full refresh
        self.command(_SSD1680_MASTER_ACTIVATE)
        self.busy_wait()
        if not self._busy:
            time.sleep(6)

    def _color_dup(self, func: str, args: tuple, color: int) -> None:
        """Write to both BW and RED framebufs for 4-gray level mapping."""
        bw_draw = getattr(self._blackframebuf, func)
        red_draw = getattr(self._colorframebuf, func)
        # BW RAM bit: 1 for DARK (L2) and WHITE (L3), 0 otherwise
        bw_draw(*args, color=color in {Adafruit_EPD.DARK, Adafruit_EPD.WHITE})
        # RED RAM bit: 1 for LIGHT (L1) and WHITE (L3), 0 otherwise
        red_draw(*args, color=color in {Adafruit_EPD.LIGHT, Adafruit_EPD.WHITE})

    def fill(self, color: int) -> None:
        """Fill entire display buffer with one of the 4 gray levels."""
        bw_fill = 0xFF if color in {Adafruit_EPD.DARK, Adafruit_EPD.WHITE} else 0x00
        red_fill = 0xFF if color in {Adafruit_EPD.LIGHT, Adafruit_EPD.WHITE} else 0x00
        if self.sram:
            self.sram.erase(0x00, self._buffer1_size, bw_fill)
            self.sram.erase(self._buffer1_size, self._buffer2_size, red_fill)
        else:
            self._blackframebuf.fill(bw_fill)
            self._colorframebuf.fill(red_fill)

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
        """Draw text string using 4-gray level colors."""
        self._blackframebuf.text(
            string,
            x,
            y,
            font_name=font_name,
            size=size,
            color=color in {Adafruit_EPD.DARK, Adafruit_EPD.WHITE},
        )
        self._colorframebuf.text(
            string,
            x,
            y,
            font_name=font_name,
            size=size,
            color=color in {Adafruit_EPD.LIGHT, Adafruit_EPD.WHITE},
        )

    def image(self, image: "Image") -> None:
        """Render a grayscale PIL image using 4 gray levels.

        Image must be mode 'L' (grayscale) sized to match the display dimensions.
        Luma thresholds:
            < 64  → BLACK (L0)
            64–127 → DARK grey (L2)
            128–191 → LIGHT grey (L1)
            ≥ 192  → WHITE (L3)
        """
        if image.mode != "L":
            image = image.convert("L")
        imwidth, imheight = image.size
        if imwidth != self.width or imheight != self.height:
            raise ValueError(
                f"Image must be same dimensions as display ({self.width}x{self.height})."
            )
        if self.sram:
            raise RuntimeError("PIL image is not supported with SRAM assist")
        pix = image.load()
        self.fill(Adafruit_EPD.BLACK)
        for iy in range(imheight):
            for ix in range(imwidth):
                luma = pix[ix, iy]
                if luma >= 192:
                    self.pixel(ix, iy, Adafruit_EPD.WHITE)
                elif luma >= 128:
                    self.pixel(ix, iy, Adafruit_EPD.LIGHT)
                elif luma >= 64:
                    self.pixel(ix, iy, Adafruit_EPD.DARK)
