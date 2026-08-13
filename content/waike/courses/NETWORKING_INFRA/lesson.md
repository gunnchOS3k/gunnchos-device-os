# Networking and Internet Infrastructure

An IPv4 address is 32 bits wearing dots. CIDR steals high bits for the network and leaves the rest for hosts. /26 means 6 host bits — 64 addresses, 62 usable if you still believe in network and broadcast addresses.

Work 192.168.10.40/26 on paper: mask, network, usable count. Then let the lab confirm. If you only memorize '254 hosts on a /24' you will fail a /26 quiz in a SOC ticket tomorrow.

This is not CCNA. It is one calculation you can redo offline when the wiki is down.
