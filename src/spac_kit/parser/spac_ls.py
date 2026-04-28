"""Command line utility to list available CCSDS packet packages."""
import argparse
import sys

from spac_kit.parser.util import import_ccsds_packet_packages


def format_packet_info(parser):
    """Format packet information into a row for display."""
    apid = getattr(parser, "apid", "N/A")
    packet_class = parser.__class__.__name__
    name = getattr(parser, "name", "")
    module = parser.__class__.__module__

    # Full packet identifier (module + class)
    packet = f"{module}.{packet_class}"

    # Get the packet definition type (base class)
    definition = parser.__class__.__bases__[0].__name__ if parser.__class__.__bases__ else "Unknown"

    return {
        "apid": apid,
        "packet": packet,
        "name": name,
        "definition": definition,
    }


def list_packages(delimiter=None):
    """List all available CCSDS packet packages.

    Args:
        delimiter: If specified, output as delimited format (e.g., ',' for CSV, '\t' for TSV)
    """
    try:
        parsers = import_ccsds_packet_packages()

        if not parsers:
            print("No CCSDS packet packages found.")
            print("Ensure that packet definitions are available in the ccsds.packets namespace.")
            return 1

        # Collect packet information
        packet_info = [format_packet_info(parser) for parser in parsers]

        # Sort by APID
        packet_info.sort(key=lambda x: (x["apid"] if isinstance(x["apid"], int) else float('inf')))

        if delimiter:
            # CSV/delimited output format
            headers = ["APID", "PACKET", "NAME", "DEFINITION"]
            print(delimiter.join(headers))

            for info in packet_info:
                row = [str(info["apid"]), info["packet"], info["name"], info["definition"]]
                print(delimiter.join(row))
        else:
            # Table format output
            # Calculate column widths
            apid_width = max(len(str(p["apid"])) for p in packet_info)
            apid_width = max(apid_width, len("APID"))

            packet_width = max(len(p["packet"]) for p in packet_info)
            packet_width = max(packet_width, len("PACKET"))

            name_width = max(len(p["name"]) for p in packet_info)
            name_width = max(name_width, len("NAME"))

            definition_width = max(len(p["definition"]) for p in packet_info)
            definition_width = max(definition_width, len("DEFINITION"))

            # Print header
            header = f"{'APID':<{apid_width}}  {'PACKET':<{packet_width}}  {'NAME':<{name_width}}  DEFINITION"

            print(header)
            print("-" * len(header))

            # Print each packet
            for info in packet_info:
                apid_str = str(info["apid"])
                line = f"{apid_str:<{apid_width}}  {info['packet']:<{packet_width}}  {info['name']:<{name_width}}  {info['definition']}"
                print(line)

            print(f"\nTotal: {len(parsers)} packet definition(s)")

        return 0

    except ImportError as e:
        print(f"Error: Unable to import ccsds.packets namespace: {e}", file=sys.stderr)
        print("Ensure that packet definitions are installed and available.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def get_parser():
    """Parser for the command line utility."""
    parser = argparse.ArgumentParser(
        description="List available CCSDS packet packages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  spac-ls                List all available packet definitions
  spac-ls -d ","         Output as CSV format
  spac-ls -d $'\\t'      Output as TSV (tab-separated) format
  spac-ls -d "," > out.csv  Save CSV output to file
        """
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Reserved for future use"
    )
    parser.add_argument(
        "-d", "--delimiter",
        type=str,
        help="Output as delimited format with specified delimiter (e.g., ',' for CSV, '\\t' for TSV)"
    )
    return parser


def main():
    """Command line interface to list CCSDS packet packages."""
    parser = get_parser()
    args = parser.parse_args()

    sys.exit(list_packages(delimiter=args.delimiter))


if __name__ == "__main__":
    main()
