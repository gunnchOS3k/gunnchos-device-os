# Physical Printer Validation Packet (CX4.0)

Digital CUPS/IPP already proven. This packet is for **real printers**.

`PHYSICAL_PRINTER_PENDING=true` — do not set physical printer PASS from collectors alone.

## Paths
- USB printer path
- LAN / IPP Everywhere path (when hardware supports it)

## Field script
1. Discovery (USB + network)
2. Add/configure printer in user UI
3. Print Writer document
4. Print PDF
5. Queue inspect / cancel
6. Paper-out simulation + recovery
7. Printer-offline + reconnect
8. Duplex/color where applicable
9. Restart session — persistence
10. Accessibility of print dialogs
11. User-visible recovery messaging

## Automated collectors
`os_build/cx4_linux_lab/harnesses/collect_cups_physical_evidence.sh`

## Pass rule (future)
Physical printer PASS requires successful USB or LAN path on real hardware with captured job IDs + physical output photos/hashes and no severity-1 recovery failures.
