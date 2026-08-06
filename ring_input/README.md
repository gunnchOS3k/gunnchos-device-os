# gunnchOS Ring Input Adapter

OS-side adapter for **authenticated** ring-class input events.

**Statuses:** `AUTHENTICATED_INPUT_PROTOCOL_PASS` · `RING_PHYSICAL_PROTOTYPE_PENDING`

No physical ring is claimed. This adapter consumes events verified by the
protocol reference in `gunnchos-hardware-industrial-design/ring_input` and maps
them to OS input actions, engaging keyboard/touch/trackpad fallback on any
authentication failure (never silent accept).
