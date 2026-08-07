# Dock Topology — USB-C / DP / HDMI

```
[gunnchOS device USB-C]──PD+USB2(+DP alt)──►[Dock controller]
        │                                      ├─► HDMI TX
        │                                      ├─► USB hub downstream
        └─ VBUS/CC negotiation                 └─► Continuity sense fixture
```

DP Alt Mode lanes mapped per USB-C pin assignment; HDMI bridge on dock PCB (digital design reference — not fabbed here).
