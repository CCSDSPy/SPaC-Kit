"""Command-line interface for packet generation."""
import argparse
import sys

from spac_kit.generator.packet_generator import PacketGenerator
from spac_kit.parser.util import import_ccsds_packet_packages


def main():
    """Main entry point for packet generator CLI."""
    parser = argparse.ArgumentParser(
        description="Generate CCSDS packets from packet definitions"
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file path for generated packets",
    )
    parser.add_argument(
        "-a",
        "--apid",
        type=int,
        nargs="+",
        help=(
            "Generate packets for specific APID(s). "
            "If not specified, generates for all APIDs."
        ),
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=1,
        help="Number of packets to generate per APID (default: 1)",
    )
    parser.add_argument(
        "-z",
        "--zeros",
        action="store_true",
        help=(
            "Generate packets with zero-initialized data instead of random data "
            "(default: random)"
        ),
    )

    args = parser.parse_args()

    try:
        packets = import_ccsds_packet_packages()
    except ImportError:
        print(
            "Error: No CCSDS packet definitions found. "
            "Please install a packet definition plugin.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not packets:
        print(
            "Error: No packet definitions found. "
            "Please install a packet definition plugin. "
            "Use 'spac-ls' to list available packet definitions.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not args.output:
        print("Error: --output is required when generating packets", file=sys.stderr)
        sys.exit(1)

    selected_packets = packets
    if args.apid:
        selected_packets = [p for p in packets if p["packet"].apid in args.apid]
        if not selected_packets:
            print(
                f"Error: No packets found with APID(s): {args.apid}",
                file=sys.stderr,
            )
            sys.exit(1)

    use_random = not args.zeros  # Default True (random), False if --zeros flag

    print(f"Generating packets to: {args.output}")
    with open(args.output, "wb") as f:
        for pkt_info in selected_packets:
            generator = PacketGenerator(pkt_info["packet"])
            generator.write_packet(f, count=args.count, use_random=use_random)
            print(
                f"  Generated {args.count} packet(s) for APID {generator.apid} "
                f"({generator.name})"
            )

    print(f"\nSuccess! Generated packets written to {args.output}")


if __name__ == "__main__":
    main()
