# Embedded Systems and Device Prototyping

A GPIO bitmask is a set of pins encoded as bits. Pin 3 set means OR with 1<<3. Pin 0 is not 'optional' — it is bit 0, value 1, and firmware people forget it because zero looks like off.

You will encode pins 0, 3, and 7. Read the hex back. If your mask is 0x88 you dropped pin 0. This maps to header-pin pointing on a real board later; this seed does not toggle hardware.
