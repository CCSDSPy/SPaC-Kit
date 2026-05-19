"""Command-line interface for packet generation."""
import argparse
import sys
from collections import Counter

import numpy as np
from scipy import stats
from spac_kit.generator.packet_generator import PacketGenerator
from spac_kit.parser.util import import_ccsds_packet_packages


def calculate_shannon_entropy(data: bytes) -> float:
    """Calculate Shannon entropy of binary data in bits per byte.

    Args:
        data: Binary data to analyze

    Returns:
        Entropy value from 0.0 (all same byte) to 8.0 (perfectly random)
    """
    if not data:
        return 0.0

    # Count occurrences of each byte value
    byte_counts = Counter(data)
    total_bytes = len(data)

    # Calculate Shannon entropy
    entropy = 0.0
    for count in byte_counts.values():
        probability = count / total_bytes
        entropy -= probability * np.log2(probability)

    return entropy


def calculate_chi_squared(data: bytes) -> tuple[float, float]:
    """Perform chi-squared test for uniform byte distribution.

    Args:
        data: Binary data to analyze

    Returns:
        Tuple of (chi_squared_statistic, p_value)
        p_value > 0.05 suggests data looks uniformly distributed
    """
    if not data:
        return 0.0, 1.0

    # Count occurrences of each byte value (0-255)
    byte_counts = Counter(data)
    observed = np.array([byte_counts.get(i, 0) for i in range(256)])

    # Expected count for uniform distribution
    expected = len(data) / 256.0

    # Chi-squared test
    chi2_stat = np.sum((observed - expected) ** 2 / expected)

    # Calculate p-value (255 degrees of freedom)
    p_value = 1 - stats.chi2.cdf(chi2_stat, df=255)

    return chi2_stat, p_value


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

    # Calculate entropy and chi-squared stats
    with open(args.output, "rb") as f:
        file_data = f.read()

    file_size = len(file_data)
    entropy = calculate_shannon_entropy(file_data)
    chi2_stat, p_value = calculate_chi_squared(file_data)

    # Format output
    entropy_pct = (entropy / 8.0) * 100
    uniformity = "uniform" if p_value > 0.05 else "non-uniform"

    print(f"\nSuccess! Generated packets written to {args.output}")
    print(
        f"  {file_size:,} bytes, "
        f"entropy: {entropy:.2f} bits/byte ({entropy_pct:.1f}%), "
        f"chi-squared: p={p_value:.2f} ({uniformity})"
    )


if __name__ == "__main__":
    main()
