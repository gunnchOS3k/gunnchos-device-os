// Prototype descriptor for firmware/OS compatibility harness.
Not validated on physical hardware.
DefinitionBlock ("", "DSDT", 2, "GUNNCH", "GCHOS  ", 0x00000001)
{
    External (_SB.PCI0, DeviceObj)
    Scope (_SB)
    {
        Device (GCDP) { Name (_HID, "GUNN0001") /* display controller stub */ }
        Device (GCIN) { Name (_HID, "GUNN0002") /* input/touch stub */ }
        Device (GCBAT) { Name (_HID, "GUNN0003") /* battery stub */ }
        Device (GCTHM) { Name (_HID, "GUNN0004") /* thermal zone stub */ }
        Device (GCSTO) { Name (_HID, "GUNN0005") /* storage stub */ }
        Device (GCNET) { Name (_HID, "GUNN0006") /* network stub */ }
        Device (GCSEN) { Name (_HID, "GUNN0009") /* sensors stub */ }
    }
}
}
