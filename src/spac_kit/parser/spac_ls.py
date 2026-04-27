"""Command line utility to list available CCSDS packet packages."""
import argparse
import sys

from spac_kit.parser.util import import_ccsds_packet_packages


def format_packet_info(parser):
    """Format packet information into a row for display."""
    apid = getattr(parser, "apid", "N/A")
    packet_type = parser.__class__.__name__
    name = getattr(parser, "name", "")
    module = parser.__class__.__module__

    # Count fields
    if hasattr(parser, "_fields"):
        num_fields = len(parser._fields)
    else:
        num_fields = 0

    return {
        "apid": apid,
        "type": packet_type,
        "name": name,
        "module": module,
        "fields": num_fields,
    }


def list_packages(verbose=False, delimiter=None):
    """List all available CCSDS packet packages.

    Args:
        verbose: Include module paths in output
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
            if verbose:
                headers = ["APID", "TYPE", "FIELDS", "NAME", "MODULE"]
            else:
                headers = ["APID", "TYPE", "FIELDS", "NAME"]

            print(delimiter.join(headers))

            for info in packet_info:
                if verbose:
                    row = [str(info["apid"]), info["type"], str(info["fields"]), info["name"], info["module"]]
                else:
                    row = [str(info["apid"]), info["type"], str(info["fields"]), info["name"]]
                print(delimiter.join(row))
        else:
            # Table format output
            # Calculate column widths
            apid_width = max(len(str(p["apid"])) for p in packet_info)
            apid_width = max(apid_width, len("APID"))

            type_width = max(len(p["type"]) for p in packet_info)
            type_width = max(type_width, len("TYPE"))

            fields_width = max(len(str(p["fields"])) for p in packet_info)
            fields_width = max(fields_width, len("FIELDS"))

            name_width = max(len(p["name"]) for p in packet_info)
            name_width = max(name_width, len("NAME"))

            # Print header
            if verbose:
                header = f"{'APID':<{apid_width}}  {'TYPE':<{type_width}}  {'FIELDS':<{fields_width}}  {'NAME':<{name_width}}  MODULE"
            else:
                header = f"{'APID':<{apid_width}}  {'TYPE':<{type_width}}  {'FIELDS':<{fields_width}}  NAME"

            print(header)
            print("-" * len(header))

            # Print each packet
            for info in packet_info:
                apid_str = str(info["apid"])
                if verbose:
                    line = f"{apid_str:<{apid_width}}  {info['type']:<{type_width}}  {info['fields']:<{fields_width}}  {info['name']:<{name_width}}  {info['module']}"
                else:
                    line = f"{apid_str:<{apid_width}}  {info['type']:<{type_width}}  {info['fields']:<{fields_width}}  {info['name']}"
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
  spac-ls                    List all available packet definitions
  spac-ls -v                 List with verbose output including module paths
  spac-ls -d ","             Output as CSV format
  spac-ls -d $'\\t'          Output as TSV (tab-separated) format
  spac-ls -v -d "," > out.csv  Save verbose CSV output to file
        """
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show verbose output including module paths"
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

    sys.exit(list_packages(verbose=args.verbose, delimiter=args.delimiter))


if __name__ == "__main__":
    main()
