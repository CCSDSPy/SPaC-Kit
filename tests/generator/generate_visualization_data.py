"""Generate large packet datasets specifically for distribution visualization.

This script generates packets with large sample sizes to demonstrate the
quality of random data generation for PR visualization. Not part of the
automated test suite - run manually for PR/documentation purposes.
"""
from pathlib import Path

import ccsdspy
from spac_kit.generator.packet_generator import PacketGenerator


def generate_large_samples():
    """Generate large sample datasets for distribution plots."""
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    print("Generating large sample datasets for visualization...")

    # 1. Large uint16 dataset - 5000 packets with single uint16 field
    print("\n1. Generating uint16 distribution (5000 packets)...")
    fields = [ccsdspy.PacketField(name="uint16_value", data_type="uint", bit_length=16)]
    packet = ccsdspy.VariableLength(fields, apid=2000, name="Uint16Viz")
    generator = PacketGenerator(packet)

    with open(output_dir / "viz_uint16_large.bin", "wb") as f:
        generator.write_packet(f, count=5000, use_random=True)
    print(f"   Saved: viz_uint16_large.bin (5000 packets)")

    # 2. Signed integers - 1000 packets with int8, int16, int32
    print("\n2. Generating signed integer distributions (1000 packets)...")
    fields = [
        ccsdspy.PacketField(name="int8_val", data_type="int", bit_length=8),
        ccsdspy.PacketField(name="int16_val", data_type="int", bit_length=16),
        ccsdspy.PacketField(name="int32_val", data_type="int", bit_length=32),
    ]
    packet = ccsdspy.VariableLength(fields, apid=2001, name="SignedIntViz")
    generator = PacketGenerator(packet)

    with open(output_dir / "viz_signed_integers_large.bin", "wb") as f:
        generator.write_packet(f, count=1000, use_random=True)
    print(f"   Saved: viz_signed_integers_large.bin (1000 packets)")

    # 3. Float distribution - 2000 packets
    print("\n3. Generating float distributions (2000 packets)...")
    fields = [
        ccsdspy.PacketField(name="float_val", data_type="float", bit_length=32),
    ]
    packet = ccsdspy.VariableLength(fields, apid=2002, name="FloatViz")
    generator = PacketGenerator(packet)

    with open(output_dir / "viz_float_large.bin", "wb") as f:
        generator.write_packet(f, count=2000, use_random=True)
    print(f"   Saved: viz_float_large.bin (2000 packets)")

    # 4. Mixed unsigned integers - 1000 packets with uint8, uint16, uint32
    print("\n4. Generating unsigned integer distributions (1000 packets)...")
    fields = [
        ccsdspy.PacketField(name="uint8_val", data_type="uint", bit_length=8),
        ccsdspy.PacketField(name="uint16_val", data_type="uint", bit_length=16),
        ccsdspy.PacketField(name="uint32_val", data_type="uint", bit_length=32),
    ]
    packet = ccsdspy.VariableLength(fields, apid=2003, name="UnsignedIntViz")
    generator = PacketGenerator(packet)

    with open(output_dir / "viz_unsigned_integers_large.bin", "wb") as f:
        generator.write_packet(f, count=1000, use_random=True)
    print(f"   Saved: viz_unsigned_integers_large.bin (1000 packets)")

    print(f"\n✓ All visualization datasets generated in: {output_dir}")
    print("\nNext steps:")
    print("  1. Run: poetry run python tests/generator/export_test_packets.py")
    print(
        "  2. Run: /tmp/viz_venv/bin/python tests/generator/visualize_distributions.py"
    )


if __name__ == "__main__":
    generate_large_samples()
