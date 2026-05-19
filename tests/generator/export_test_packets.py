"""Export test packet binaries to CSV for analysis and visualization."""
import io
from pathlib import Path

import ccsdspy
import pandas as pd


def export_packets_to_csv():
    """Parse test packet files and export to CSV."""
    output_dir = Path(__file__).parent / "output"
    csv_dir = output_dir / "csv"
    csv_dir.mkdir(exist_ok=True)

    # Define packet structures for each test output file
    packets_to_export = [
        # Visualization datasets (large samples)
        {
            "bin_file": "viz_uint16_large.bin",
            "csv_file": "viz_uint16_large.csv",
            "packet": ccsdspy.VariableLength(
                [
                    ccsdspy.PacketField(
                        name="uint16_value", data_type="uint", bit_length=16
                    )
                ],
                apid=2000,
            ),
        },
        {
            "bin_file": "viz_signed_integers_large.bin",
            "csv_file": "viz_signed_integers_large.csv",
            "packet": ccsdspy.VariableLength(
                [
                    ccsdspy.PacketField(name="int8_val", data_type="int", bit_length=8),
                    ccsdspy.PacketField(
                        name="int16_val", data_type="int", bit_length=16
                    ),
                    ccsdspy.PacketField(
                        name="int32_val", data_type="int", bit_length=32
                    ),
                ],
                apid=2001,
            ),
        },
        {
            "bin_file": "viz_float_large.bin",
            "csv_file": "viz_float_large.csv",
            "packet": ccsdspy.VariableLength(
                [
                    ccsdspy.PacketField(
                        name="float_val", data_type="float", bit_length=32
                    )
                ],
                apid=2002,
            ),
        },
        {
            "bin_file": "viz_unsigned_integers_large.bin",
            "csv_file": "viz_unsigned_integers_large.csv",
            "packet": ccsdspy.VariableLength(
                [
                    ccsdspy.PacketField(
                        name="uint8_val", data_type="uint", bit_length=8
                    ),
                    ccsdspy.PacketField(
                        name="uint16_val", data_type="uint", bit_length=16
                    ),
                    ccsdspy.PacketField(
                        name="uint32_val", data_type="uint", bit_length=32
                    ),
                ],
                apid=2003,
            ),
        },
        # Test output files (smaller samples)
        {
            "bin_file": "single_packet_zeros.bin",
            "csv_file": "single_packet_zeros.csv",
            "packet": ccsdspy.VariableLength(
                [
                    ccsdspy.PacketField(name="field1", data_type="uint", bit_length=8),
                    ccsdspy.PacketField(name="field2", data_type="uint", bit_length=16),
                ],
                apid=100,
            ),
        },
        {
            "bin_file": "multiple_packets_random.bin",
            "csv_file": "multiple_packets_random.csv",
            "packet": ccsdspy.VariableLength(
                [ccsdspy.PacketField(name="data", data_type="uint", bit_length=8)],
                apid=100,
            ),
        },
        {
            "bin_file": "large_array_random.bin",
            "csv_file": "large_array_random.csv",
            "packet": ccsdspy.VariableLength(
                [
                    ccsdspy.PacketField(
                        name="counter", data_type="uint", bit_length=16
                    ),
                    ccsdspy.PacketArray(
                        name="large_data",
                        data_type="uint",
                        bit_length=16,
                        array_shape=10000,
                    ),
                ],
                apid=400,
            ),
        },
        {
            "bin_file": "signed_integers_random.bin",
            "csv_file": "signed_integers_random.csv",
            "packet": ccsdspy.VariableLength(
                [
                    ccsdspy.PacketField(name="int8_val", data_type="int", bit_length=8),
                    ccsdspy.PacketField(
                        name="int16_val", data_type="int", bit_length=16
                    ),
                    ccsdspy.PacketField(
                        name="int32_val", data_type="int", bit_length=32
                    ),
                ],
                apid=800,
            ),
        },
        {
            "bin_file": "float_fields_zeros.bin",
            "csv_file": "float_fields_zeros.csv",
            "packet": ccsdspy.VariableLength(
                [
                    ccsdspy.PacketField(
                        name="temperature", data_type="float", bit_length=32
                    ),
                    ccsdspy.PacketField(
                        name="pressure", data_type="float", bit_length=32
                    ),
                ],
                apid=300,
            ),
        },
    ]

    for pkt_config in packets_to_export:
        bin_path = output_dir / pkt_config["bin_file"]
        csv_path = csv_dir / pkt_config["csv_file"]

        if not bin_path.exists():
            print(f"Skipping {bin_path.name} - file not found")
            continue

        try:
            # Parse the binary file
            with open(bin_path, "rb") as f:
                parsed = pkt_config["packet"].load(f, include_primary_header=True)

            # For large arrays, flatten the array column to separate rows
            if "large_data" in parsed:
                # Extract first packet's large_data for distribution analysis
                large_data = parsed["large_data"][0]
                flat_df = pd.DataFrame({"large_data_value": large_data})
                flat_df.to_csv(csv_path, index=False)
                print(f"Exported {bin_path.name} -> {csv_path.name} (flattened)")
            else:
                # Convert to DataFrame for other packets
                df = pd.DataFrame(parsed)
                df.to_csv(csv_path, index=False)
                print(f"Exported {bin_path.name} -> {csv_path.name}")

        except Exception as e:
            print(f"Error exporting {bin_path.name}: {e}")

    print(f"\nCSV files saved to: {csv_dir}")


if __name__ == "__main__":
    export_packets_to_csv()
