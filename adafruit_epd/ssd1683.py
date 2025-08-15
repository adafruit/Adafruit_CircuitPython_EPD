# SPDX-FileCopyrightText: 2025 Liz Clark for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_epd.ssd1683` - Adafruit SSD1683 - ePaper display driver
====================================================================================
CircuitPython driver for Adafruit SSD1683 display breakouts
* Author(s): Liz Clark
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
_SSD1683_DRIVER_CONTROL = const(0x01)
_SSD1683_GATE_VOLTAGE = const(0x03)
_SSD1683_SOURCE_VOLTAGE = const(0x04)
_SSD1683_PROGOTP_INITIAL = const(0x08)
_SSD1683_PROGREG_INITIAL = const(0x09)
_SSD1683_READREG_INITIAL = const(0x0A)
_SSD1683_BOOST_SOFTSTART = const(0x0C)
_SSD1683_DEEP_SLEEP = const(0x10)
_SSD1683_DATA_MODE = const(0x11)
_SSD1683_SW_RESET = const(0x12)
_SSD1683_HV_READY = const(0x14)
_SSD1683_VCI_DETECT = const(0x15)
_SSD1683_PROGRAM_WSOTP = const(0x16)
_SSD1683_PROGRAM_AUTO = const(0x17)
_SSD1683_TEMP_CONTROL = const(0x18)
_SSD1683_TEMP_WRITE = const(0x1A)
_SSD1683_TEMP_READ = const(0x1B)
_SSD1683_TEMP_CONTROLEXT = const(0x1C)
_SSD1683_MASTER_ACTIVATE = const(0x20)
_SSD1683_DISP_CTRL1 = const(0x21)
_SSD1683_DISP_CTRL2 = const(0x22)
_SSD1683_WRITE_RAM1 = const(0x24)
_SSD1683_WRITE_RAM2 = const(0x26)
_SSD1683_READ_RAM1 = const(0x27)
_SSD1683_SENSE_VCOM = const(0x28)
_SSD1683_SENSEDUR_VCOM = const(0x29)
_SSD1683_PROGOTP_VCOM = const(0x2A)
_SSD1683_WRITE_VCOM = const(0x2C)
_SSD1683_READ_OTP = const(0x2D)
_SSD1683_READ_USERID = const(0x2E)
_SSD1683_READ_STATUS = const(0x2F)
_SSD1683_WRITE_LUT = const(0x32)
_SSD1683_WRITE_BORDER = const(0x3C)
_SSD1683_END_OPTION = const(0x3F)
_SSD1683_SET_RAMXPOS = const(0x44)
_SSD1683_SET_RAMYPOS = const(0x45)
_SSD1683_SET_RAMXCOUNT = const(0x4E)
_SSD1683_SET_RAMYCOUNT = const(0x4F)

# Other constants
_EPD_RAM_BW = const(0x10)
_EPD_RAM_RED = const(0x13)
_BUSY_WAIT = const(500)


class Adafruit_SSD1683(Adafruit_EPD):
    """driver class for Adafruit SSD1683 ePaper display breakouts"""

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
            self._buffer1, width, height, buf_format=adafruit_framebuf.MHMSB
        )
        self._framebuf2 = adafruit_framebuf.FrameBuffer(
            self._buffer2, width, height, buf_format=adafruit_framebuf.MHMSB
        )
        self.set_black_buffer(0, True)
        self.set_color_buffer(1, False)

        # Set single byte transactions flag
        self._single_byte_tx = True

        # Set the display update value
        self._display_update_val = 0xF7

        # Default initialization sequence (tri-color mode)
        self._default_init_code = bytes(
            [
                _SSD1683_SW_RESET,
                0,  # Software reset
                0xFF,
                50,  # Wait for busy (50ms delay)
                _SSD1683_WRITE_BORDER,
                1,  # Border waveform control
                0x05,  # Border color/waveform
                _SSD1683_TEMP_CONTROL,
                1,  # Temperature control
                0x80,  # Read temp
                _SSD1683_DATA_MODE,
                1,  # Data entry mode
                0x03,  # Y decrement, X increment
                0xFE,  # End of initialization
            ]
        )

    def begin(self, reset: bool = True) -> None:
        """Begin communication with the display and set basic settings"""
        if reset:
            self.hardware_reset()
        self.power_down()

    def busy_wait(self) -> None:
        """Wait for display to be done with current task, either by polling the
        busy pin, or pausing"""
        if self._busy:
            while self._busy.value:  # wait for busy low
                time.sleep(0.01)
        else:
            time.sleep(_BUSY_WAIT / 1000.0)  # Convert ms to seconds

    def power_up(self) -> None:
        """Power up the display in preparation for writing RAM and updating"""
        self.hardware_reset()
        time.sleep(0.1)
        self.busy_wait()

        # Use custom init code if provided, otherwise use default
        init_code = self._default_init_code
        if hasattr(self, "_epd_init_code") and self._epd_init_code is not None:
            init_code = self._epd_init_code

        # Send initialization sequence
        self._send_command_list(init_code)

        # Set RAM window
        self.set_ram_window(0, 0, (self._width // 8) - 1, self._height - 1)

        # Set RAM address to start position
        self.set_ram_address(0, 0)

        # Set LUT if we have one
        if hasattr(self, "_epd_lut_code") and self._epd_lut_code:
            self._send_command_list(self._epd_lut_code)

        # Set display size and driver output control
        _b0 = (self._height - 1) & 0xFF
        _b1 = ((self._height - 1) >> 8) & 0xFF
        _b2 = 0x00
        self.command(_SSD1683_DRIVER_CONTROL, bytearray([_b0, _b1, _b2]))

    def power_down(self) -> None:
        """Power down the display - required when not actively displaying!"""
        # Only deep sleep if we can get out of it
        if self._rst:
            # deep sleep
            self.command(_SSD1683_DEEP_SLEEP, bytearray([0x01]))
            time.sleep(0.1)
        else:
            self.command(_SSD1683_SW_RESET)
            self.busy_wait()

    def update(self) -> None:
        """Update the display from internal memory"""
        # display update sequence
        self.command(_SSD1683_DISP_CTRL2, bytearray([self._display_update_val]))
        self.command(_SSD1683_MASTER_ACTIVATE)
        self.busy_wait()

        if not self._busy:
            time.sleep(1)  # wait 1 second

    def write_ram(self, index: Literal[0, 1]) -> int:
        """Send the one byte command for starting the RAM write process. Returns
        the byte read at the same time over SPI. index is the RAM buffer, can be
        0 or 1 for tri-color displays."""
        if index == 0:
            return self.command(_SSD1683_WRITE_RAM1, end=False)
        if index == 1:
            return self.command(_SSD1683_WRITE_RAM2, end=False)
        raise RuntimeError("RAM index must be 0 or 1")

    def set_ram_address(self, x: int, y: int) -> None:
        """Set the RAM address location"""
        # set RAM x address count
        self.command(_SSD1683_SET_RAMXCOUNT, bytearray([x & 0xFF]))

        # set RAM y address count
        self.command(_SSD1683_SET_RAMYCOUNT, bytearray([y & 0xFF, (y >> 8) & 0xFF]))

    def set_ram_window(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Set the RAM window for partial updates"""
        # Set ram X start/end position
        self.command(_SSD1683_SET_RAMXPOS, bytearray([x1 & 0xFF, x2 & 0xFF]))

        # Set ram Y start/end position
        self.command(
            _SSD1683_SET_RAMYPOS,
            bytearray([y1 & 0xFF, (y1 >> 8) & 0xFF, y2 & 0xFF, (y2 >> 8) & 0xFF]),
        )

    def _send_command_list(self, init_sequence: bytes) -> None:
        """Send a sequence of commands from an initialization list"""
        i = 0
        while i < len(init_sequence):
            cmd = init_sequence[i]
            i += 1

            if cmd == 0xFE:  # End marker
                break
            elif cmd == 0xFF:  # Delay marker
                if i < len(init_sequence):
                    delay_ms = init_sequence[i]
                    i += 1
                    time.sleep(delay_ms / 1000.0)
            elif i < len(init_sequence):
                num_args = init_sequence[i]
                i += 1
                if num_args > 0 and (i + num_args) <= len(init_sequence):
                    args = init_sequence[i : i + num_args]
                    self.command(cmd, bytearray(args))
                    i += num_args
                else:
                    self.command(cmd)
