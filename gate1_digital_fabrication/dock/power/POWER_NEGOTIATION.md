# Dock Power Negotiation

| State | Source | Sink | PDO class | Notes |
|---|---|---|---|---|
| Idle undocked | device battery | — | — | |
| Docked default | dock 5V/3A | device | Fixed 5V | Minimum bring-up |
| Docked PD | dock | device | Optional 9V | After PD contract |
| Display active | dock | HDMI sink 5V | HDMI 5V | Separate from PD |

Simulation path exercises state machine without VBUS.
