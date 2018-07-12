from micropython import const
import digitalio

SRAM_SEQUENTIAL_MODE = const(1 << 6)

class Adafruit_MCP_SRAM(object):

    SRAM_READ = 0x03
    SRAM_WRITE = 0x02
    SRAM_RDSR = 0x05
    SRAM_WRSR = 0x01

    def __init__(self, cs_pin, spi):
        # Handle hardware SPI
        self.spi_device = spi
        self.cs_pin = cs_pin

        self.cs_pin.direction = digitalio.Direction.OUTPUT
        while not self.spi_device.try_lock():
            pass
        self.cs_pin.value = False
        self.spi_device.write(bytearray([Adafruit_MCP_SRAM.SRAM_WRSR, 0x43]))
        self.cs_pin.value = True
        self.spi_device.unlock()

    def write(self, addr, buf, reg=SRAM_WRITE):
        cmd = bytearray([reg, (addr >> 8) & 0xFF, addr & 0xFF] + buf)

        while not self.spi_device.try_lock():
            pass
        self.cs_pin.value = False
        self.spi_device.write(cmd)
        self.cs_pin.value = True
        self.spi_device.unlock()

    def read(self, addr, length, reg=SRAM_READ):
        cmd = bytearray([reg, (addr >> 8) & 0xFF, addr & 0xFF])

        buf = bytearray(length)
        while not self.spi_device.try_lock():
            pass
        self.cs_pin.value = False
        self.spi_device.write(cmd)
        self.spi_device.readinto(buf)
        self.cs_pin.value = True
        self.spi_device.unlock()
        return buf

    def read8(self, addr, reg=SRAM_READ):
        return self.read(addr, 1, reg)[0]

    def read16(self, addr, reg=SRAM_READ):
        buf = self.read(addr, 2, reg)
        return buf[0] << 8 | buf[1]

    def write8(self, addr, value, reg=SRAM_WRITE):
        self.write(addr, [value], reg)

    def write16(self, addr, value, reg=SRAM_WRITE):
        self.write(addr, [value >> 8, value], reg)

    def erase(self, addr, length, value):
        cmd = bytearray([Adafruit_MCP_SRAM.SRAM_WRITE, (addr >> 8) & 0xFF, addr & 0xFF])

        while not self.spi_device.try_lock():
            pass
        self.cs_pin.value = False
        self.spi_device.write(cmd)
        for _ in range(length):
            self.spi_device.write(bytearray([value]))
        self.cs_pin.value = True
        self.spi_device.unlock()
