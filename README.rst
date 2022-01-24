Introduction
============

.. image:: https://readthedocs.org/projects/adafruit-circuitpython-epd/badge/?version=latest
    :target: https://docs.circuitpython.org/projects/epd/en/latest/
    :alt: Documentation Status

.. image:: https://img.shields.io/discord/327254708534116352.svg
    :target: https://adafru.it/discord
    :alt: Discord

.. image:: https://github.com/adafruit/Adafruit_CircuitPython_EPD/workflows/Build%20CI/badge.svg
    :target: https://github.com/adafruit/Adafruit_CircuitPython_EPD/actions/
    :alt: Build Status

This library is for using CircuitPython with e-ink displays with built in SRAM.

Dependencies
=============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_
* `Bus Device <https://github.com/adafruit/Adafruit_CircuitPython_BusDevice>`_
* `font5x8.bin found in the examples bundle <https://github.com/adafruit/Adafruit_CircuitPython_Bundle>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://github.com/adafruit/Adafruit_CircuitPython_Bundle>`_.

Installing from PyPI
====================

On supported GNU/Linux systems like the Raspberry Pi, you can install the driver locally `from
PyPI <https://pypi.org/project/adafruit-circuitpython-epd/>`_. To install for current user:

.. code-block:: shell

    pip3 install adafruit-circuitpython-epd

To install system-wide (this may be required in some cases):

.. code-block:: shell

    sudo pip3 install adafruit-circuitpython-epd

To install in a virtual environment in your current project:

.. code-block:: shell

    mkdir project-name && cd project-name
    python3 -m venv .env
    source .env/bin/activate
    pip3 install adafruit-circuitpython-epd

Usage Example
=============

.. code-block:: python

    import digitalio
    import busio
    import board
    from adafruit_epd.epd import Adafruit_EPD
    from adafruit_epd.il0373 import Adafruit_IL0373

    # create the spi device and pins we will need
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    ecs = digitalio.DigitalInOut(board.D12)
    dc = digitalio.DigitalInOut(board.D11)
    srcs = digitalio.DigitalInOut(board.D10)    # can be None to use internal memory
    rst = digitalio.DigitalInOut(board.D9)    # can be None to not use this pin
    busy = digitalio.DigitalInOut(board.D5)   # can be None to not use this pin

    # give them all to our driver
    print("Creating display")
    display = Adafruit_IL0373(104, 212, spi,          # 2.13" Tri-color display
                              cs_pin=ecs, dc_pin=dc, sramcs_pin=srcs,
                              rst_pin=rst, busy_pin=busy)

    display.rotation = 1

    # clear the buffer
    print("Clear buffer")
    display.fill(Adafruit_EPD.WHITE)
    display.pixel(10, 100, Adafruit_EPD.BLACK)

    print("Draw Rectangles")
    display.fill_rect(5, 5, 10, 10, Adafruit_EPD.RED)
    display.rect(0, 0, 20, 30, Adafruit_EPD.BLACK)

    print("Draw lines")
    display.line(0, 0, display.width-1, display.height-1, Adafruit_EPD.BLACK)
    display.line(0, display.height-1, display.width-1, 0, Adafruit_EPD.RED)

    print("Draw text")
    display.text('hello world', 25, 10, Adafruit_EPD.BLACK)
    display.display()


Documentation
=============

API documentation for this library can be found on `Read the Docs <https://docs.circuitpython.org/projects/epd/en/latest/>`_.

Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/adafruit/Adafruit_CircuitPython_EPD/blob/main/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.

Documentation
=============

For information on building library documentation, please check out `this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.
