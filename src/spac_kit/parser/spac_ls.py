"""Command line utility to list available CCSDS packet packages."""
import argparse
import sys

from spac_kit.parser.util import import_ccsds_packet_packages


def format_packet_info(packet_info, long_format=False):
    """Format packet information into a row for display.

    Args:
        packet_info: Either a dict with 'packet', 'variable_name', 'module_path' keys,
                     or a packet object for backward compatibility
        long_format: If True, include additional fields like packet type and field count
    """
    # Handle new dict format from import_ccsds_packet_packages
    if isinstance(packet_info, dict):
        parser = packet_info["packet"]
        variable_name = packet_info.get("variable_name")
        module_path = packet_info.get("module_path")

        # Build packet identifier using variable name
        if variable_name and module_path:
            # Remove the redundant "ccsds.packets." prefix
            trimmed_path = module_path.removeprefix("ccsds.packets.")
            packet_id = f"{trimmed_path}.{variable_name}"
        else:
            # Fallback
            module = parser.__class__.__module__.removeprefix("ccsds.packets.")
            packet_id = f"{module}.{parser.__class__.__name__}"
    else:
        # Backward compatibility: packet_info is a packet object
        parser = packet_info
        module = parser.__class__.__module__.removeprefix("ccsds.packets.")
        packet_id = f"{module}.{parser.__class__.__name__}"

    apid = getattr(parser, "apid", "N/A")
    name = getattr(parser, "name", "")
    description = getattr(parser, "description", "")

    # Handle None values - convert to empty strings
    if name is None:
        name = ""
    if description is None:
        description = ""

    result = {
        "apid": apid,
        "packet": packet_id,
        "name": name,
        "description": description,
    }

    # Add extra fields for long format
    if long_format:
        # Get packet type
        packet_type = parser.__class__.__name__
        result["type"] = packet_type

        # Get field count
        fields = getattr(parser, "_fields", [])
        result["fields"] = len(fields)

        # Get field names
        field_names = [getattr(f, "_name", "?") for f in fields]
        result["field_names"] = ", ".join(field_names) if field_names else ""

    return result


def _print_delimited(packet_info, delimiter, long_format):
    headers = ["APID", "PACKET", "NAME", "DESCRIPTION"]
    if long_format:
        headers.extend(["TYPE", "FIELDS", "FIELD_NAMES"])
    print(delimiter.join(headers))
    for info in packet_info:
        row = [str(info["apid"]), info["packet"], info["name"], info["description"]]
        if long_format:
            row.extend([info["type"], str(info["fields"]), info["field_names"]])
        print(delimiter.join(row))


def _print_table(packet_info, total, long_format):  # pylint: disable=too-many-locals
    apid_width = max(max(len(str(p["apid"])) for p in packet_info), len("APID"))
    packet_width = max(max(len(p["packet"]) for p in packet_info), len("PACKET"))
    name_width = max(max(len(p["name"]) for p in packet_info), len("NAME"))
    description_width = max(
        max(len(p["description"]) for p in packet_info), len("DESCRIPTION")
    )

    if long_format:
        type_width = max(max(len(p["type"]) for p in packet_info), len("TYPE"))
        fields_width = max(
            max(len(str(p["fields"])) for p in packet_info), len("FIELDS")
        )
        header = (
            f"{'APID':<{apid_width}}  {'PACKET':<{packet_width}}  "
            f"{'NAME':<{name_width}}  {'DESCRIPTION':<{description_width}}  "
            f"{'TYPE':<{type_width}}  {'FIELDS':<{fields_width}}  FIELD_NAMES"
        )
    else:
        header = (
            f"{'APID':<{apid_width}}  {'PACKET':<{packet_width}}  "
            f"{'NAME':<{name_width}}  DESCRIPTION"
        )

    print(header)
    print("-" * len(header))

    apid_seen = set()
    for info in packet_info:
        apid_str = str(info["apid"])
        if apid_str in apid_seen:
            continue
        apid_seen.add(apid_str)
        if long_format:
            line = (
                f"{apid_str:<{apid_width}}  {info['packet']:<{packet_width}}  "
                f"{info['name']:<{name_width}}  "
                f"{info['description']:<{description_width}}  "
                f"{info['type']:<{type_width}}  {info['fields']:<{fields_width}}  "
                f"{info['field_names']}"
            )
        else:
            line = (
                f"{apid_str:<{apid_width}}  {info['packet']:<{packet_width}}  "
                f"{info['name']:<{name_width}}  {info['description']}"
            )
        print(line)

    print(f"\nTotal: {total} packet definition(s)")


# pylint: disable=too-many-branches
def list_packages(delimiter=None, long_format=False, extra_namespaces=None):
    """List all available CCSDS packet packages.

    Args:
        delimiter: If specified, output as delimited format
                   (e.g., ',' for CSV, '\t' for TSV)
        long_format: If True, display additional fields like
                     packet type and field information
        extra_namespaces: Additional Python namespace strings to search
    """
    try:
        parsers = import_ccsds_packet_packages(extra_namespaces=extra_namespaces)

        if not parsers:
            print("No CCSDS packet packages found.")
            print(
                "Ensure that packet definitions are available in the "
                "ccsds.packets namespace."
            )
            return 1

        # Collect packet information
        packet_info = [
            format_packet_info(parser, long_format=long_format) for parser in parsers
        ]

        # Sort by APID
        packet_info.sort(
            key=lambda x: (x["apid"] if isinstance(x["apid"], int) else float("inf"))
        )

        if delimiter:
            _print_delimited(packet_info, delimiter, long_format)
        else:
            _print_table(packet_info, len(parsers), long_format)

        return 0

    except ImportError as e:
        print(f"Error: Unable to import packet namespace: {e}", file=sys.stderr)
        print(
            "Ensure that packet definitions are installed and available.",
            file=sys.stderr,
        )
        return 1
    except Exception as e:  # pylint: disable=broad-exception-caught
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
  spac-ls -l             List with additional packet details (type, fields)
  spac-ls -d ","         Output as CSV format
  spac-ls -l -d ","      Output as CSV with additional fields
  spac-ls -d $'\\t'      Output as TSV (tab-separated) format
  spac-ls -d "," > out.csv  Save CSV output to file
        """,
    )
    parser.add_argument(
        "-l",
        "--long",
        action="store_true",
        help="Display additional fields including packet type, field count, "
        "and field names",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Reserved for future use"
    )
    parser.add_argument(
        "-d",
        "--delimiter",
        type=str,
        help="Output as delimited format with specified delimiter "
        "(e.g., ',' for CSV, '\\t' for TSV)",
    )
    parser.add_argument(
        "--extra-packet-namespaces",
        type=str,
        nargs="+",
        help="Additional Python namespaces to search for CCSDS packet definitions, "
        "in addition to the default ccsds.packets namespace. "
        "Can also be set via the EXTRA_PACKET_NAMESPACES environment variable "
        "(comma-separated).",
    )
    return parser


def main():
    """Command line interface to list CCSDS packet packages."""
    parser = get_parser()
    args = parser.parse_args()

    sys.exit(
        list_packages(
            delimiter=args.delimiter,
            long_format=args.long,
            extra_namespaces=args.extra_packet_namespaces,
        )
    )


if __name__ == "__main__":
    main()
