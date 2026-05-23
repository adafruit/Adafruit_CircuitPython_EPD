# SPDX-FileCopyrightText: 2025 Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_epd.ssd1675a_grayscale4` - 4-level grayscale driver for SSD1675A (IL3897)
=====================================================================================
CircuitPython driver for Adafruit SSD1675A ePaper display breakouts in 4-gray mode.

Confirmed hardware: HINK E0213A22-A0 SLH 1852, Adafruit #4195 (pre-April 2020 revision).

Identify your hardware: read the FPC ribbon label on the panel edge.
  "HINK E0213A22-A0" → SSD1675A (this driver)
  Any Good Display label (GDEY0213B74, etc.) → SSD1680 (use Adafruit_SSD1680)

Critical differences from 2-color SSD1675 init:
  1. Voltage commands (EOPQ/VGH/VSH/VCOM) must come AFTER the LUT write.
  2. 0x3A (dummy line period) and 0x3B (gate line width) must be omitted.
  3. VCOM=0x28 (not 0x70 — the 2-color value overdrives grayscale).
  4. Double-pass refresh: write buffers and activate twice for clean output.

* Author(s): Adafruit Industries
"""

import time

from micropython import const

from adafruit_epd.epd import Adafruit_EPD
from adafruit_epd.ssd1675 import Adafruit_SSD1675

try:
    from busio import SPI
    from digitalio import DigitalInOut
except ImportError:
    pass

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_EPD.git"

_SSD1675A_SW_RESET = const(0x12)
_SSD1675A_SET_ANALOGBLOCK = const(0x74)
_SSD1675A_SET_DIGITALBLOCK = const(0x7E)
_SSD1675A_DRIVER_CONTROL = const(0x01)
_SSD1675A_DATA_MODE = const(0x11)
_SSD1675A_WRITE_BORDER = const(0x3C)
_SSD1675A_DISP_CTRL1 = const(0x21)
_SSD1675A_DISP_CTRL2 = const(0x22)
_SSD1675A_MASTER_ACTIVATE = const(0x20)
_SSD1675A_SET_RAMXPOS = const(0x44)
_SSD1675A_SET_RAMYPOS = const(0x45)
_SSD1675A_SET_RAMXCOUNT = const(0x4E)
_SSD1675A_SET_RAMYCOUNT = const(0x4F)
_SSD1675A_WRITE_LUT = const(0x32)
_SSD1675A_WRITE_RAM1 = const(0x24)
_SSD1675A_WRITE_RAM2 = const(0x26)
_SSD1675A_END_OPTION = const(0x3F)
_SSD1675A_GATE_VOLTAGE = const(0x03)
_SSD1675A_SOURCE_VOLTAGE = const(0x04)
_SSD1675A_WRITE_VCOM = const(0x2C)

# pux4j GRAY4_LUT (153 bytes): VS rows + timing groups + FR/XON.
# Source: darranl/pux4j (Java/Pi4J, SSD1675A 2.9" panel), adapted for 250×122.
# 0x60 DC balance — works reliably from any prior display state.
# (The GxEPD2 0x48 LUT fails from a clean all-white prior state on SSD1675A.)
_GRAY4_LUT = bytes([
    # VS rows (5 × 12 bytes)
    0x00, 0x60, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # L0 white
    0x20, 0x60, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # L1 light gray
    0x28, 0x60, 0x14, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # L2 dark gray
    0x2A, 0x60, 0x15, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # L3 black
    0x00, 0x90, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # L4 VCOM
    # Timing groups (12 × 7 bytes)
    0x00, 0x02, 0x00, 0x05, 0x14, 0x00, 0x00,  # G0
    0x1E, 0x1E, 0x00, 0x00, 0x00, 0x00, 0x01,  # G1 (RP=1)
    0x00, 0x02, 0x00, 0x05, 0x14, 0x00, 0x00,  # G2
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # G3–G11: zeros
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    # FR / XON (9 bytes)
    0x24, 0x22, 0x22, 0x22, 0x23, 0x32, 0x00, 0x00, 0x00,
])


class Adafruit_SSD1675A_Grayscale4(Adafruit_SSD1675):
    """4-level grayscale driver for SSD1675A (IL3897) ePaper displays.

    Tested on Adafruit #4195 2.13" eInk FeatherWing (pre-April 2020,
    panel FPC label: HINK E0213A22-A0).

    Pass width=122, height=250 to match the 250×122 panel RAM layout.

    Four color constants are available::

        WHITE      = 1   # L0 — BW=1, COLOR=0
        LIGHT_GRAY = 2   # L1 — BW=1, COLOR=1
        DARK_GRAY  = 3   # L2 — BW=0, COLOR=1
        BLACK      = 0   # L3 — BW=0, COLOR=0

    Usage::

        import busio, board, digitalio
        from adafruit_epd.ssd1675a_grayscale4 import Adafruit_SSD1675A_Grayscale4

        spi = busio.SPI(board.SCK, MOSI=board.MOSI)
        display = Adafruit_SSD1675A_Grayscale4(
            122, 250, spi,
            cs_pin=digitalio.DigitalInOut(board.D9),
            dc_pin=digitalio.DigitalInOut(board.D10),
            sramcs_pin=None,
            rst_pin=digitalio.DigitalInOut(board.D11),
            busy_pin=digitalio.DigitalInOut(board.D12),
        )
        display.fill(Adafruit_SSD1675A_Grayscale4.WHITE)
        display.fill_rect(0, 0, 60, 250, Adafruit_SSD1675A_Grayscale4.BLACK)
        display.display()
    """

    LIGHT_GRAY = const(2)
    DARK_GRAY = const(3)

    def __init__(self, width, height, spi, *, cs_pin, dc_pin, sramcs_pin,
                 rst_pin, busy_pin):
        super().__init__(width, height, spi, cs_pin=cs_pin, dc_pin=dc_pin,
                         sramcs_pin=sramcs_pin, rst_pin=rst_pin, busy_pin=busy_pin)
        # Parent sets both framebuffers to _framebuf1 (monochrome). Redirect
        # the color framebuffer to _framebuf2 so drawing ops use both RAM banks.
        self.set_color_buffer(1, False)

    # ------------------------------------------------------------------
    # 4-gray drawing API
    # ------------------------------------------------------------------

    def _color_dup(self, func, args, color):
        """Set a pixel or region in both BW and COLOR RAM for 4-gray output.

        BW RAM:    1 = white/light-gray tendency  (L0 / L1)
        COLOR RAM: 1 = gray pixel (L1 / L2)

        Resulting LUT state per pixel:
          WHITE(1)      BW=1 COLOR=0 → L0
          LIGHT_GRAY(2) BW=1 COLOR=1 → L1
          DARK_GRAY(3)  BW=0 COLOR=1 → L2
          BLACK(0)      BW=0 COLOR=0 → L3
        """
        bw_fn = getattr(self._blackframebuf, func)
        color_fn = getattr(self._colorframebuf, func)
        bw_bit = color in (Adafruit_EPD.WHITE, 2)    # LIGHT_GRAY=2
        color_bit = color in (2, 3)                  # LIGHT_GRAY=2, DARK_GRAY=3
        bw_fn(*args, color=bw_bit)
        color_fn(*args, color=color_bit)

    def pixel(self, x, y, color):
        """Set one pixel to one of the four gray levels."""
        self._color_dup("pixel", (x, y), color)

    def fill_rect(self, x, y, width, height, color):
        """Fill a rectangle with one of the four gray levels."""
        self._color_dup("fill_rect", (x, y, width, height), color)

    def fill(self, color):
        """Fill the entire display with one of the four gray levels."""
        bw_byte = 0xFF if color in (Adafruit_EPD.WHITE, 2) else 0x00
        color_byte = 0xFF if color in (2, 3) else 0x00
        if self.sram:
            self.sram.erase(0x00, self._buffer1_size, bw_byte)
            self.sram.erase(self._buffer1_size, self._buffer2_size, color_byte)
        else:
            self._blackframebuf.fill(bw_byte)
            self._colorframebuf.fill(color_byte)

    # ------------------------------------------------------------------
    # Hardware control
    # ------------------------------------------------------------------

    def _send(self, cmd, data=None) -> None:
        """Send one command+data with the SPI bus already locked by the caller."""
        self._cs.value = False
        self._dc.value = False
        self.spi_device.write(bytearray([cmd]))
        if data is not None:
            self._dc.value = True
            self.spi_device.write(
                bytearray(data) if isinstance(data, bytes) else data
            )
        self._cs.value = True

    def _set_ram_window(self) -> None:
        """Set RAM X/Y window and reset counters to (0,0). SPI must be locked."""
        self._send(_SSD1675A_SET_RAMXPOS, bytearray([0x00, 0x0F]))
        self._send(_SSD1675A_SET_RAMYPOS, bytearray([0x00, 0x00, 0xF9, 0x00]))
        self._send(_SSD1675A_SET_RAMXCOUNT, bytearray([0x00]))
        self._send(_SSD1675A_SET_RAMYCOUNT, bytearray([0x00, 0x00]))

    def display(self) -> None:
        """Double-pass refresh for clean 4-gray output.

        The SPI bus is held locked for the entire sequence. Releasing and
        re-acquiring the lock between commands corrupts the SSD1675A controller
        state, preventing the custom LUT refresh from triggering.

        Pass 1 establishes the prior pixel state; pass 2 drives cleanly to
        the target gray level.
        """
        while not self.spi_device.try_lock():
            time.sleep(0.01)
        try:
            for _ in range(2):
                # Hardware reset is GPIO — safe while SPI is locked
                self.hardware_reset()
                time.sleep(0.02)

                self._send(_SSD1675A_SW_RESET)
                time.sleep(0.02)

                self._send(_SSD1675A_SET_ANALOGBLOCK, bytearray([0x54]))
                self._send(_SSD1675A_SET_DIGITALBLOCK, bytearray([0x3B]))
                self._send(_SSD1675A_DRIVER_CONTROL, bytearray([0xF9, 0x00, 0x00]))
                self._send(_SSD1675A_DATA_MODE, bytearray([0x03]))
                self._send(_SSD1675A_WRITE_BORDER, bytearray([0x03]))
                self._send(_SSD1675A_DISP_CTRL1, bytearray([0x00, 0x80]))
                self._set_ram_window()

                # LUT first, then voltage — ordering critical for SSD1675A 4-gray
                self._send(_SSD1675A_WRITE_LUT, _GRAY4_LUT)
                self._send(_SSD1675A_END_OPTION, bytearray([0x22]))
                self._send(_SSD1675A_GATE_VOLTAGE, bytearray([0x17]))
                self._send(_SSD1675A_SOURCE_VOLTAGE, bytearray([0x41, 0xAE, 0x32]))
                self._send(_SSD1675A_WRITE_VCOM, bytearray([0x28]))
                self._send(_SSD1675A_DISP_CTRL2, bytearray([0xC7]))

                # BW RAM — reset window before each write
                self._set_ram_window()
                self._cs.value = False
                self._dc.value = False
                self.spi_device.write(bytearray([_SSD1675A_WRITE_RAM1]))
                self._dc.value = True
                self.spi_device.write(self._buffer1)
                self._cs.value = True
                time.sleep(0.002)

                # COLOR RAM
                self._set_ram_window()
                self._cs.value = False
                self._dc.value = False
                self.spi_device.write(bytearray([_SSD1675A_WRITE_RAM2]))
                self._dc.value = True
                self.spi_device.write(self._buffer2)
                self._cs.value = True

                self._send(_SSD1675A_MASTER_ACTIVATE)
                time.sleep(3.0)
        finally:
            self.spi_device.unlock()
