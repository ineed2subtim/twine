# Twine P4 Filter

A packet filtering and forwarding pipeline implemented in P4, targeting the Xilinx SmartNIC platform (Alveo U280).

## Features

- Filters and forwards packets based on table rules. Supported protocols (as of the latest commit):
    - Ethernet
    - VLAN
    - IPv4
    - IPv6
    - TCP
    - UDP
    - ICMP
    - SSH
    - MPLS
    - PW (Pseudowire)
    - BGP

- IP address anonymization using CryptoPAN:
    - Masks IPv4 32-bit source and destination addresses
    - Masks IPv6 128-bit source and destination addresses

- Packet sampling using a mid-square Pseudo-Random Number Generator (PRNG) to select packets for sampling. Sampled packets are sent to host0 interface. 

- Packet truncation support (Availabile and tested on esnet-smartnic-hw commit: 4a97547ef12f2bf1ac6f4836038d7e7f603d0865; esnet-smartnic-fw commit: c064d4ac775ed1a4c50ec72dea3615f9c644433e )

- Implements counters for various packet types:
    - Forwarded packets
    - Dropped packets
    - Protocol-specific packets (TCP, UDP, ICMP, SSH, MPLS, PW, BGP)

## Pipeline Structure

1. Parser: Extracts headers from incoming packets based on supported protocols
2. Match-Action Pipeline: Applies filtering and forwarding rules, IP anonymization, packet sampling, and updates counters
3. Deparser: Emits headers for outgoing packets

The pipeline is designed to handle a wide range of network protocols and provides flexibility in defining filtering and forwarding rules. The IP anonymization feature enhances privacy, while packet sampling enables network monitoring and analysis. Packet truncation support allows for efficient packet processing and storage. The counters provide insights into network traffic patterns and help in troubleshooting and performance optimization.
