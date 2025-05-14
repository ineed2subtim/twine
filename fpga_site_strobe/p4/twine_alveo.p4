    #include <core.p4>
    #include <xsa.p4>

    // Port definitions
    #define CMAC0_PORT 0x00 // CMAC0 
    #define CMAC1_PORT 0x01 // CMAC1 
    #define HOST0_PORT 0x02 // HOST0 
    #define HOST1_PORT 0x03  // HOST1

    // Ethernet types
    const bit<16> TYPE_IPV4 = 0x0800;
    const bit<16> TYPE_IPV6 = 0x86DD;
    const bit<16> TYPE_VLAN = 0x8100;
    const bit<16> TYPE_MPLS = 0x8847;

    // Ports & protocols
    const bit<16> SSH_PORT = 22;
    const bit<16> BGP_PORT = 179;

    // Protocol types
    const bit<8> SSH_PROTOCOL = 22;
    const bit<8> MPLS_PROTOCOL = 137;
    const bit<8> PW_PROTOCOL = 4;
    const bit<8> BGP_PROTOCOL = 179;
    const bit<8> TCP = 6; 
    const bit<8> UDP = 17;
    const bit<8> ICMP = 1; 

    // Masks
    const bit<32> MASK_32 = 0x00F0F0F0;
    const bit<128> MASK_128 = 0x00F000F000F000F000F000F000F000F0;
    
    // Counters 
    const bit<32> NUM_COUNTERS = 10;

    // Type definitions
    typedef bit<48> macAddr_t;
    typedef bit<32> ip4Addr_t; 
    typedef bit<128> ip6Addr_t;
    typedef bit<13> counter_index_t; 

    // Header definitions
    header ethernet_t {
        bit<48> dstAddr;
        bit<48> srcAddr;
        bit<16> etherType;
    }

    header ipv4_t {
        bit<4>  version;
        bit<4>  ihl;
        bit<8>  diffserv;
        bit<16> totalLen;
        bit<16> identification;
        bit<3>  flags;
        bit<13> fragOffset;
        bit<8>  ttl;
        bit<8>  protocol;
        bit<16> hdrChecksum;
        ip4Addr_t srcAddr;
        ip4Addr_t dstAddr;
    }

    header ipv6_t {
        bit<4>   version;
        bit<8>   trafficClass;
        bit<20>  flowLabel;
        bit<16>  payloadLen;
        bit<8>   nextHdr;
        bit<8>   hopLimit;
        ip6Addr_t srcAddr;
        ip6Addr_t dstAddr;
    }

    header tcp_t {
        bit<16> srcPort;
        bit<16> dstPort;
        bit<32> seqNo;
        bit<32> ackNo;
        bit<4>  dataOffset;
        bit<3>  res;
        bit<3>  ecn;
        bit<6>  ctrl;
        bit<16> window;
        bit<16> checksum;
        bit<16> urgentPtr;
        bit<16> length; 
    }

    header udp_t {
        bit<16> srcPort; 
        bit<16> dstPort; 
        bit<16> length; 
        bit<16> checksum; 
    }

    header icmp_t {
        bit<8>  type; 
        bit<8>  code; 
        bit<16> checksum; 
        bit<32> restOfHeader; 
    }

    header vlan_t {
        bit<3>  pcp;
        bit<1>  cfi;
        bit<12> vid;
        bit<16> etherType;
    }

    header ssh_t {
        bit<8>  version;
        bit<8>  padding;
        bit<16> packetLength;
        bit<8>  paddingLength;
        bit<8>  messageCode;
    }

    header mpls_t {
        bit<20> label;
        bit<3>  exp;
        bit<1>  bos;
        bit<8>  ttl;
    }

    header pw_t {
        bit<4>  flags;
        bit<12> fragId;
        bit<16> tag;
    }

    header bgp_t {
        bit<16> marker;
        bit<16> length;
        bit<8>  type;
    }

    // Headers
    struct headers_t {
        ethernet_t ethernet;
        vlan_t     vlan;
        ipv4_t     ipv4;
        ipv6_t     ipv6;
        tcp_t      tcp;
        udp_t      udp;
        icmp_t     icmp;
        ssh_t      ssh;
        mpls_t     mpls;
        pw_t       pw;
        bgp_t      bgp;
    }

    // Metadata
    struct smartnic_metadata {
        bit<64> timestamp_ns;    // 64b timestamp (in nanoseconds). Set at packet arrival time.
        bit<16> pid;             // 16b packet id used by platform (READ ONLY - DO NOT EDIT).
        bit<3>  ingress_port;    // 3b ingress port (0:CMAC0, 1:CMAC1, 2:HOST0, 3:HOST1).
        bit<3>  egress_port;     // 3b egress port  (0:CMAC0, 1:CMAC1, 2:HOST0, 3:HOST1).
        bit<1>  truncate_enable; // reserved (tied to 0).
        bit<16> truncate_length; // reserved (tied to 0).
        bit<1>  rss_enable;      // reserved (tied to 0).
        bit<12> rss_entropy;     // reserved (tied to 0).
        bit<4>  drop_reason;     // reserved (tied to 0).
        bit<32> scratch;         // reserved (tied to 0).
    }

    // Counter Indexes
    const counter_index_t forwarded_packets_count_index = 0;
    const counter_index_t tcp_packets_count_index = 0;
    const counter_index_t udp_packets_count_index = 0;
    const counter_index_t icmp_packets_count_index = 0;
    const counter_index_t dropped_packets_count_index = 0;
    const counter_index_t sample_counter_count_index = 0;
    const counter_index_t ssh_packets_count_index = 0;
    const counter_index_t mpls_packets_count_index = 0;
    const counter_index_t pw_packets_count_index = 0;
    const counter_index_t bgp_packets_count_index = 0;

    // Counter definitions
    Counter<bit<32>, counter_index_t>(NUM_COUNTERS, CounterType_t.PACKETS) forwarded_packets;
    Counter<bit<32>, counter_index_t>(NUM_COUNTERS, CounterType_t.PACKETS) tcp_packets;
    Counter<bit<32>, counter_index_t>(NUM_COUNTERS, CounterType_t.PACKETS) udp_packets;
    Counter<bit<32>, counter_index_t>(NUM_COUNTERS, CounterType_t.PACKETS) icmp_packets;
    Counter<bit<32>, counter_index_t>(NUM_COUNTERS, CounterType_t.PACKETS) ssh_packets;
    Counter<bit<32>, counter_index_t>(NUM_COUNTERS, CounterType_t.PACKETS) mpls_packets;
    Counter<bit<32>, counter_index_t>(NUM_COUNTERS, CounterType_t.PACKETS) pw_packets;
    Counter<bit<32>, counter_index_t>(NUM_COUNTERS, CounterType_t.PACKETS) bgp_packets;
    Counter<bit<32>, counter_index_t>(NUM_COUNTERS, CounterType_t.PACKETS) dropped_packets;
    Counter<bit<32>, counter_index_t>(NUM_COUNTERS, CounterType_t.PACKETS) sample_counter;

    // Parser
    parser ParserImpl(packet_in packet,
                    out headers_t hdr,
                    inout smartnic_metadata sn_meta,
                    inout standard_metadata_t smeta)
    {   
        state start {
            transition parse_ethernet;
        }
        
        state parse_ethernet {
            packet.extract(hdr.ethernet);
            transition select(hdr.ethernet.etherType) {
                TYPE_VLAN: parse_vlan;
                TYPE_IPV4: parse_ipv4; 
                TYPE_IPV6: parse_ipv6;
                TYPE_MPLS: parse_mpls;
                default: accept;
            }
        }

        state parse_vlan {
            packet.extract(hdr.vlan);
            transition select(hdr.vlan.etherType) {
                TYPE_IPV4: parse_ipv4;
                TYPE_IPV6: parse_ipv6;
                default: accept;
            }
        }
        
        state parse_ipv4 {
            packet.extract(hdr.ipv4);
            transition select(hdr.ipv4.protocol) {
                TCP: parse_tcp; 
                UDP: parse_udp;
                ICMP: parse_icmp;
                default: accept;
            }
        }
        
        state parse_ipv6 {
            packet.extract(hdr.ipv6);
            transition select(hdr.ipv6.nextHdr) {
                TCP: parse_tcp; 
                UDP: parse_udp;
                ICMP: parse_icmp;
                default: accept;
            }
        }
        
        state parse_tcp {
            packet.extract(hdr.tcp);
            transition select(hdr.tcp.dstPort) {
                SSH_PORT: parse_ssh;
                BGP_PORT: parse_bgp;
                default: accept;
            }
        }
        
        state parse_udp {
            packet.extract(hdr.udp);
            transition accept;
        }
        
        state parse_icmp {
            packet.extract(hdr.icmp);
            transition accept;
        }

        state parse_ssh {
            packet.extract(hdr.ssh);
            transition accept;
        }

        state parse_bgp {
            packet.extract(hdr.bgp);
            transition accept;
        }

        state parse_mpls {
            packet.extract(hdr.mpls);
            transition select(hdr.mpls.bos) {
                0: parse_mpls; // Parse next MPLS header recursively
                1: parse_pw;
                default: parse_mpls;
            }
        }

        state parse_pw {
            packet.extract(hdr.pw);
            transition accept;
        }
    }

    // Match-Action pipeline
    control MatchActionImpl(inout headers_t hdr,
                            inout smartnic_metadata sn_meta,
                            inout standard_metadata_t smeta) 
    {
        action truncate_packet(bit<16> truncate_len) {
            sn_meta.truncate_enable = 1;
            sn_meta.truncate_length = truncate_len;
        }

		action set_mac(macAddr_t new_dst_mac) {
			hdr.ethernet.dstAddr = new_dst_mac;	
		}

        action sample_packet_action() {
            sn_meta.egress_port = HOST0_PORT;
            sample_counter.count(sample_counter_count_index);
        }

        action forward(bit<3> dest_port) {
            sn_meta.egress_port = dest_port;
            forwarded_packets.count(forwarded_packets_count_index);
        }

        action forward_tcp(bit<3> dest_port, bit<16> len) {
            truncate_packet(len); // Truncate to include only Ethernet, IP, and TCP headers (IPv6 74 bytes)
            forward(dest_port);
            tcp_packets.count(tcp_packets_count_index);
        }

        action forward_udp(bit<3> dest_port, bit<16> len) {
            truncate_packet(len); // Truncate to include only Ethernet, IP, and UDP headers (IPv6 62 bytes)
            forward(dest_port);
            udp_packets.count(udp_packets_count_index);
        }

        action forward_icmp(bit<3> dest_port, bit<16> len) {
            truncate_packet(len); // Truncate to include only Ethernet, IP, and ICMP headers (IPv6 62 bytes)
            forward(dest_port);
            icmp_packets.count(icmp_packets_count_index);
        }

        action forward_ssh(bit<3> dest_port, bit<16> len) {
            truncate_packet(len); // Truncate to include only Ethernet, IP, and SSH headers (IPv6 62 bytes)
            forward(dest_port);
            ssh_packets.count(ssh_packets_count_index);
        }

        action forward_mpls(bit<3> dest_port, bit<16> len) {
            truncate_packet(len); // Truncate to include only Ethernet and MPLS headers (assuming: 1 Label)
            forward(dest_port);
            mpls_packets.count(mpls_packets_count_index);
        }

        action forward_pw(bit<3> dest_port, bit<16> len) {
            truncate_packet(len); // Truncate to include only Ethernet, MPLS, and PW headers
            forward(dest_port);
            pw_packets.count(pw_packets_count_index);
        }

        action forward_bgp(bit<3> dest_port, bit<16> len) {
            truncate_packet(len); 
            forward(dest_port);
            bgp_packets.count(bgp_packets_count_index);
        }
        
        action drop_packet() {
            smeta.drop = 1;
            dropped_packets.count(dropped_packets_count_index); 
        }

        action drop_tcp() {
            drop_packet();
            tcp_packets.count(tcp_packets_count_index);
        }

        action drop_udp() {
            drop_packet();
            udp_packets.count(udp_packets_count_index);
        }

        action drop_icmp() {
            drop_packet();
            icmp_packets.count(icmp_packets_count_index);
        }

        action drop_ssh() {
            drop_packet();
            ssh_packets.count(ssh_packets_count_index);
        }

        action drop_mpls() {
            drop_packet();
            mpls_packets.count(mpls_packets_count_index);
        }

        action drop_pw() {
            drop_packet();
            pw_packets.count(pw_packets_count_index);
        }

        action drop_bgp() {
            drop_packet();
            bgp_packets.count(bgp_packets_count_index);
        }

        action cryptoPAN_IPv4() {
            hdr.ipv4.srcAddr = hdr.ipv4.srcAddr ^ MASK_32;
            hdr.ipv4.srcAddr = hdr.ipv4.srcAddr & 0x7FFFFFFF;

            hdr.ipv4.dstAddr = hdr.ipv4.dstAddr ^ MASK_32;
            hdr.ipv4.dstAddr = hdr.ipv4.dstAddr & 0x7FFFFFFF;
        }

        action cryptoPAN_IPv6() {
            hdr.ipv6.srcAddr = hdr.ipv6.srcAddr ^ MASK_128;
            hdr.ipv6.srcAddr[127:112] = hdr.ipv6.srcAddr[127:112] & 0x7FFF;

            hdr.ipv6.dstAddr = hdr.ipv6.dstAddr ^ MASK_128;
            hdr.ipv6.dstAddr[127:112] = hdr.ipv6.dstAddr[127:112] & 0x7FFF;
        }
        
        table filter_tcp {
            key = {
                hdr.tcp.srcPort : lpm;
                hdr.tcp.dstPort : lpm; 
            }
            
            actions = {
                forward_tcp;
                drop_tcp;
            }

            size = 1024;
            default_action = drop_tcp; 
        }
        
        table filter_udp {
            key = {
                hdr.udp.srcPort : ternary;
                hdr.udp.dstPort : ternary;
            }

            actions = {
                forward_udp;
                drop_udp;
            }
            
            num_masks = 16;
            size = 1024;
            default_action = drop_udp;
        }
        
        table filter_icmp {
            key = {
                hdr.icmp.type : lpm;
                hdr.icmp.code : lpm; 
            }
            
            actions = {
                forward_icmp;
                drop_icmp;
            }
            
            size = 1024;
            default_action = drop_icmp;
        }

        table filter_ssh {
            key = {
                hdr.tcp.dstPort : lpm;
            }
            
            actions = {
                forward_ssh;
                drop_ssh;
            }
            
            size = 1024;
            default_action = drop_ssh;
        }

        table filter_mpls {
            key = {
                hdr.mpls.label : lpm;
            }
            
            actions = {
                forward_mpls;
                drop_mpls;
            }
            
            size = 1024;
            default_action = drop_mpls;
        }

        table filter_pw {
            key = {
                hdr.pw.tag : lpm;
            }
            
            actions = {
                forward_pw;
                drop_pw;
            }
            
            size = 1024;
            default_action = drop_pw;
        }

        table filter_bgp {
            key = {
                hdr.bgp.type : lpm;
                hdr.bgp.length : lpm;
            }
            
            actions = {
                forward_bgp;
                drop_bgp;
            }
            
            size = 1024;
            default_action = drop_bgp;
        }
		
		table mac_change {
			key = {
				sn_meta.egress_port: exact;
				hdr.ethernet.etherType: exact;     // Required due to 10bit minimum limitation for keys
			}

			actions = {
				set_mac;
				NoAction;
			}
			size = 64;
			default_action = NoAction();
		}	
        apply {
            if (smeta.parser_error != error.NoError) {
                drop_packet();
                return;
            }
            
            if (hdr.ethernet.isValid()) {
                    bool isValidIPv4 = hdr.ipv4.isValid();
                bool isValidIPv6 = hdr.ipv6.isValid();

                // Mask IP addresses
                if(isValidIPv4) {
                    cryptoPAN_IPv4();
                } else if (isValidIPv6) {
                    cryptoPAN_IPv6();
                }

                // Sample packets
                bit<32> seed = (bit<32>)hdr.ethernet.srcAddr ^ (bit<32>)hdr.ethernet.dstAddr;
                bit<64> square = (bit<64>)seed * (bit<64>)seed;
                bit<32> random_num = (bit<32>)(square >> 16);

                bit<3> sample_bits = random_num[2:0];
                bool to_sample = sample_bits == 3w0;
                //bool to_sample = false;
                
                if (to_sample) {
                    sample_packet_action();
                }else{
                    if (hdr.mpls.isValid()) {
                        if (hdr.pw.isValid() && hdr.mpls.bos == 1) {
                            filter_pw.apply();
                        } else {
                            filter_mpls.apply();
                        }
						mac_change.apply();
                    }else if (isValidIPv4 || isValidIPv6) {
                        if ((hdr.ipv4.protocol == TCP || hdr.ipv6.nextHdr  == TCP) && hdr.tcp.isValid()) {
                            if (hdr.ssh.isValid() && hdr.tcp.dstPort == SSH_PORT) {
                                filter_ssh.apply();
                            } else if(hdr.bgp.isValid() && hdr.tcp.dstPort == BGP_PORT) {
                                filter_bgp.apply();
                            } else {
                                filter_tcp.apply();
                            }
                        } else if ((hdr.ipv4.protocol == UDP || hdr.ipv6.nextHdr  == UDP) && hdr.udp.isValid()) {
                            filter_udp.apply();
                        } else if ((hdr.ipv4.protocol == ICMP || hdr.ipv6.nextHdr  == ICMP) && hdr.icmp.isValid()) {
                            filter_icmp.apply();
                        } else {
                            drop_packet();
                        }
						mac_change.apply();
                    } else {
                        drop_packet();
                    }
                }
            } else {
                drop_packet();
            }
        }
    }

    // Deparser
    control DeparserImpl(packet_out packet, 
                        in headers_t hdr,
                        inout smartnic_metadata sn_meta,
                        inout standard_metadata_t smeta)
    {
        apply {
            packet.emit(hdr.ethernet);
            packet.emit(hdr.vlan);
            packet.emit(hdr.ipv4);
            packet.emit(hdr.ipv6);
            packet.emit(hdr.tcp);
            packet.emit(hdr.udp);
            packet.emit(hdr.icmp);
            packet.emit(hdr.ssh);
            packet.emit(hdr.mpls);
            packet.emit(hdr.pw);
            packet.emit(hdr.bgp);
        }
    }

    // Pipeline
    XilinxPipeline(
        ParserImpl(),
        MatchActionImpl(), 
        DeparserImpl()
    ) main;

