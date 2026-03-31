# SPDX-FileCopyrightText: 2018 Dean Miller for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_epd.ssd1680_legacy` - Adafruit SSD1680 Legacy - ePaper display driver
====================================================================================
CircuitPython driver for older Adafruit SSD1680 display breakouts
ex: pre-2024 2.13" Monochrome E-Ink Bonnet
* Author(s): Melissa LeBlanc-Williams
"""

from micropython import const

from adafruit_epd.ssd1680 import Adafruit_SSD1680

_SSD1680_DRIVER_CONTROL = const(0x01)
_SSD1680_SET_RAMXPOS = const(0x44)
_SSD1680_SET_RAMYPOS = const(0x45)
_SSD1680_SET_RAMXCOUNT = const(0x4E)
_SSD1680_SET_RAMYCOUNT = const(0x4F)
_SSD1680_WRITE_VCOM_REG = const(0x2C)
_SSD1680_GATE_VOLTAGE = const(0x03)
_SSD1680_SOURCE_VOLTAGE = const(0x04)
_SSD1680_DATA_MODE = const(0x11)
_SSD1680_WRITE_BORDER = const(0x3C)
_SSD1680_SW_RESET = const(0x12)


class Adafruit_SSD1680_Legacy(Adafruit_SSD1680):
    """Driver for older SSD1680 ePaper displays (pre-2024 2.13" Monochrome E-Ink Bonnet)"""

    def power_up(self) -> None:
        """Power up the display in preparation for writing RAM and updating"""
        self.hardware_reset()
        self.busy_wait()
        self.command(_SSD1680_SW_RESET)
        self.busy_wait()
        # driver output control
        self.command(
            _SSD1680_DRIVER_CONTROL,
            bytearray([self._height - 1, (self._height - 1) >> 8, 0x00]),
        )
        # data entry mode
        self.command(_SSD1680_DATA_MODE, bytearray([0x03]))

        # Set voltages
        self.command(_SSD1680_WRITE_VCOM_REG, bytearray([0x36]))
        self.command(_SSD1680_GATE_VOLTAGE, bytearray([0x17]))
        self.command(_SSD1680_SOURCE_VOLTAGE, bytearray([0x41, 0x00, 0x32]))

        # Set ram X start/end postion
        self.command(_SSD1680_SET_RAMXPOS, bytearray([0x01, 0x10]))
        # Set ram Y start/end postion
        self.command(
            _SSD1680_SET_RAMYPOS,
            bytearray([0, 0, self._height - 1, (self._height - 1) >> 8]),
        )
        # Set border waveform
        self.command(_SSD1680_WRITE_BORDER, bytearray([0x05]))

        # Set ram X count
        self.command(_SSD1680_SET_RAMXCOUNT, bytearray([0x01]))
        # Set ram Y count
        self.command(_SSD1680_SET_RAMYCOUNT, bytearray([self._height - 1, 0]))
        self.busy_wait()

    def set_ram_address(self, x: int, y: int) -> None:
        """Set the RAM address location"""
        # Set RAM X address counter
        self.command(_SSD1680_SET_RAMXCOUNT, bytearray([x + 1]))
        # Set RAM Y address counter
        self.command(_SSD1680_SET_RAMYCOUNT, bytearray([y, y >> 8]))
