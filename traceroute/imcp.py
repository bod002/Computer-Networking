# -*- coding: utf-8 -*-
"""
Created on Mon Mar 20 21:13:34 2023

@author: footf
"""

import struct
class icmp_packet:
	# ref https://en.wikipedia.org/wiki/Internet_Control_Message_Protocol
	type_code = {
		(0, 0): "Echo Reply",
		(3, 0): "Destination Network Unreachable",
		(3, 1): "Destination Host Unreachable",
		(3, 2): "Destination Protocol Unreachable",
		(3, 3): "Destination Port Unreachable",
		(3, 4): "Fragmentation Required, and DF flag set",
		(3, 5): "Source Route Failed",
		(3, 6): "Destination Network Unknown",
		(3, 7): "Destination Host Unknown",
		(3, 8): "Source Host Isolated",
		(3, 9): "Network Administratively Prohibited",
		(3, 10): "Host Administratively Prohibited",
		(3, 11): "Network Unreachable for Type of Service",
		(3, 12): "Host Unreachable for Type of Service",
		(3, 13): "Communication Administratively Prohibited",
		(3, 14): "Host Precedence Violation",
		(3, 15): "Precedence cutoff in effect",
		(4, 0): "Source Quench",
		(5, 0): "Redirect Datagram for the Network",
		(5, 1): "Redirect Datagram for the Host",
		(5, 2): "Redirect Datagram for the Type of Service and Network",
		(5, 3): "Redirect Datagram for the Type of Service and Host",
		(8, 0): "Echo Request",
		(9, 0): "Router Advertisement",
		(10, 0): "Router Solicitation",
		(11, 0): "TTL expired in transit",
		(11, 1): "Fragment reassembly time exceeded",
		(12, 0): "IP header bad (catchall error)",
		(12, 1): "Required options missing",
		(13, 0): "Timestamp Request",
		(14, 0): "Timestamp Reply",
		(15, 0): "Information Request",
		(16, 0): "Information Reply",
		(17, 0): "Address Mask Request",
		(18, 0): "Address Mask Reply",
		(30, 0): "Traceroute"
	}
	
	def __init__(self, icmp_type = 0, icmp_code = 0, icmp_payload = b""):
		self.type = icmp_type
		self.code = icmp_code
		self.checksum = 0
		self.payload = icmp_payload
		self.calc_checksum()

	def calc_checksum(self):
		data = self.to_bytes()
		sum = 0
		# make 16 bit words out of every two adjacent 8 bit words in the packet
		for i in range(0, len(data), 2):
			if i + 1 < len(data):
				sum += (data[i] << 8) + data[i+1]
			else:
				sum += data[i] << 8
		# take only 16 bits out of the 32 bit sum and add up the carries
		sum = (sum >> 16) + (sum & 0xffff)
		sum += (sum >> 16)
		
		# one's complement
		self.checksum = ~sum & 0xffff
	def from_bytes(data):
		# parse the data into an icmp_packet
		icmp_type, icmp_code, icmp_checksum = struct.unpack("!BBH", data[:4])

		return icmp_packet(icmp_type, icmp_code, data[4:])

	def to_bytes(self):
		# convert the packet into bytes
		return struct.pack("!BBH", self.type, self.code, self.checksum) + self.payload
	
	def __str__(self):
		tc = (self.type, self.code)
		if tc in icmp_packet.type_code:
			return f"ICMP {icmp_packet.type_code[tc]}"
		else:
			return f"ICMP {tc}"