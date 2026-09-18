# Camera / Microphone / AV Physical Validation Packet (CX4.0)

`PHYSICAL_CAMERA_MIC_AV_PENDING=true`
Do not claim audiovisual quality without human/physical evidence.
Device enumeration fixtures ≠ physical PASS.

## Field tests
- camera discovery / preview / photo-frame capture
- microphone discovery / record / playback
- browser permission allow/deny
- meeting-app permission flow
- hot-plug/unplug
- audio output / headphones / Bluetooth if supported
- failure/recovery
- privacy indicator/state
- restart persistence

## Automated collectors
`collect_av_diagnostics.sh` — V4L2, PipeWire/WirePlumber, audio graph snapshots.
