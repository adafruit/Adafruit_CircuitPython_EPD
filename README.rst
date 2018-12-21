Introduction
============

.. image:: https://readthedocs.org/projects/adafruit-circuitpython-epd/badge/?version=latest
    :target: https://circuitpython.readthedocs.io/projects/epd/en/latest/
    :alt: Documentation Status

.. image:: https://img.shields.io/discord/327254708534116352.svg
    :target: https://discord.gg/nBQh6qu
    :alt: Discord

.. image:: https://travis-ci.com/adafruit/Adafruit_CircuitPython_EPD.svg?branch=master
    :target: https://travis-ci.com/adafruit/Adafruit_CircuitPython_EPD
    :alt: Build Status

This library is for using CircuitPython with e-ink displays with built in SRAM.

Dependencies
=============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_
* `Bus Device <https://github.com/adafruit/Adafruit_CircuitPython_BusDevice>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://github.com/adafruit/Adafruit_CircuitPython_Bundle>`_.

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
    ecs = digitalio.DigitalInOut(board.D10)
    dc = digitalio.DigitalInOut(board.D9)
    srcs = digitalio.DigitalInOut(board.D8)
    rst = digitalio.DigitalInOut(board.D7)
    busy = digitalio.DigitalInOut(board.D6)

    # give them all to our driver
    display = Adafruit_IL0373(152, 152, rst, dc, busy, srcs, ecs, spi)

    # clear the buffer
    display.clear_buffer()

    r_width = 5
    r_pos = display.height

    #draw some rectangles!
    color = Adafruit_EPD.BLACK
    while r_pos > display.height/2:
        if r_pos < display.height - 50:
            color = Adafruit_EPD.RED
        display.rect(display.width - r_pos, display.height - r_pos,
                    display.width - 2*(display.width - r_pos),
                    display.height - 2*(display.height - r_pos), color)
        r_pos = r_pos - r_width

    display.display()


Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/adafruit/Adafruit_CircuitPython_EPD/blob/master/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.

Building locally
================

Zip release files
-----------------

To build this library locally you'll need to install the
`circuitpython-build-tools <https://github.com/adafruit/circuitpython-build-tools>`_ package.

.. code-block:: shell

    python3 -m venv .env
    source .env/bin/activate
    pip install circuitpython-build-tools

Once installed, make sure you are in the virtual environment:

.. code-block:: shell

    source .env/bin/activate

Then run the build:

.. code-block:: shell

    circuitpython-build-bundles --filename_prefix adafruit-circuitpython-epd --library_location .

Sphinx documentation
-----------------------

Sphinx is used to build the documentation based on rST files and comments in the code. First,
install dependencies (feel free to reuse the virtual environment from above):

.. code-block:: shell

    python3 -m venv .env
    source .env/bin/activate
    pip install Sphinx sphinx-rtd-theme

Now, once you have the virtual environment activated:

.. code-block:: shell

    cd docs
    sphinx-build -E -W -b html . _build/html

This will output the documentation to ``docs/_build/html``. Open the index.html in your browser to
view them. It will also (due to -W) error out on any warning like Travis will. This is a good way to
locally verify it will pass.
