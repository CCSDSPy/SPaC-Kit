"""Example script demonstrating packet generation."""
import ccsdspy
from spac_kit.generator import PacketGenerator

# Define a simple packet structure
fields = [
    ccsdspy.PacketField(name="status", data_type="uint", bit_length=8),
    ccsdspy.PacketField(name="counter", data_type="uint", bit_length=16),
    ccsdspy.PacketField(name="temperature", data_type="float", bit_length=32),
    ccsdspy.PacketArray(
        name="data_array", data_type="uint", bit_length=8, array_shape=10
    ),
]

# Create a packet definition
packet_def = ccsdspy.VariableLength(fields, apid=100, name="SensorPacket")

# Create generator
generator = PacketGenerator(packet_def)

# Generate and write packets to a file
output_file = "example_packets.bin"
with open(output_file, "wb") as f:
    # Generate 5 packets with incrementing sequence counts
    generator.write_packet(f, count=5)

print(f"Generated 5 packets and saved to {output_file}")
print(f"Packet APID: {generator.apid}")
print(f"Packet Name: {generator.name}")

# You can also generate a single packet and inspect it
single_packet = generator.generate_packet(sequence_count=42)
print(f"\nSingle packet size: {len(single_packet)} bytes")
print(f"Header (6 bytes): {single_packet[:6].hex()}")
print(f"Data ({len(single_packet)-6} bytes): {single_packet[6:].hex()}")
