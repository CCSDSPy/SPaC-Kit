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


# pylint: disable=too-many-locals,too-many-branches
def list_packages(delimiter=None, long_format=False):
    """List all available CCSDS packet packages.

    Args:
        delimiter: If specified, output as delimited format
                   (e.g., ',' for CSV, '\t' for TSV)
        long_format: If True, display additional fields like
                     packet type and field information
    """
    try:
        parsers = import_ccsds_packet_packages()

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
            # CSV/delimited output format
            headers = ["APID", "PACKET", "NAME", "DESCRIPTION"]
            if long_format:
                headers.extend(["TYPE", "FIELDS", "FIELD_NAMES"])
            print(delimiter.join(headers))

            for info in packet_info:
                row = [
                    str(info["apid"]),
                    info["packet"],
                    info["name"],
                    info["description"],
                ]
                if long_format:
                    row.extend([info["type"], str(info["fields"]), info["field_names"]])
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

            description_width = max(len(p["description"]) for p in packet_info)
            description_width = max(description_width, len("DESCRIPTION"))

            if long_format:
                type_width = max(len(p["type"]) for p in packet_info)
                type_width = max(type_width, len("TYPE"))

                fields_width = max(len(str(p["fields"])) for p in packet_info)
                fields_width = max(fields_width, len("FIELDS"))

                # Print header
                header = (
                    f"{'APID':<{apid_width}}  {'PACKET':<{packet_width}}  "
                    f"{'NAME':<{name_width}}  "
                    f"{'DESCRIPTION':<{description_width}}  "
                    f"{'TYPE':<{type_width}}  "
                    f"{'FIELDS':<{fields_width}}  FIELD_NAMES"
                )
            else:
                # Print header
                header = (
                    f"{'APID':<{apid_width}}  {'PACKET':<{packet_width}}  "
                    f"{'NAME':<{name_width}}  DESCRIPTION"
                )

            print(header)
            print("-" * len(header))

            # Print each packet
            apid_seen = set()
            for info in packet_info:
                apid_str = str(info["apid"])
                if apid_str not in apid_seen:
                    apid_seen.add(apid_str)
                    if long_format:
                        line = (
                            f"{apid_str:<{apid_width}}  "
                            f"{info['packet']:<{packet_width}}  "
                            f"{info['name']:<{name_width}}  "
                            f"{info['description']:<{description_width}}  "
                            f"{info['type']:<{type_width}}  "
                            f"{info['fields']:<{fields_width}}  "
                            f"{info['field_names']}"
                        )
                    else:
                        line = (
                            f"{apid_str:<{apid_width}}  "
                            f"{info['packet']:<{packet_width}}  "
                            f"{info['name']:<{name_width}}  "
                            f"{info['description']}"
                        )
                    print(line)

            print(f"\nTotal: {len(parsers)} packet definition(s)")

        return 0

    except ImportError as e:
        print(f"Error: Unable to import ccsds.packets namespace: {e}", file=sys.stderr)
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
    return parser


def main():
    """Command line interface to list CCSDS packet packages."""
    parser = get_parser()
    args = parser.parse_args()

    sys.exit(list_packages(delimiter=args.delimiter, long_format=args.long))


if __name__ == "__main__":
    main()
