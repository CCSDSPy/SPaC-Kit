# Packet Generator

The Packet Generator module creates CCSDS space packets with zero/blank-initialized fields from packet definitions. This is useful for:

- Testing packet parsing and processing pipelines
- Creating template packets for documentation
- Generating sample data for testing
- Creating reference packets with known structures

## Features

- Generates valid CCSDS primary headers
- Initializes all packet fields to zero/blank values
- Supports all CCSDSpy field types (uint, int, float, arrays)
- Can generate multiple packets with incrementing sequence counts
- CLI tool for easy packet generation from installed packet definitions
- Python API for programmatic use

## Installation

The generator is included with SPaC-Kit. No additional installation is needed.

## Usage

### Command-Line Interface

#### List available packet definitions

Use the `spac-ls` command to view all available packet definitions from installed plugins:

```bash
spac-ls
```

#### Generate packets for all APIDs

```bash
poetry run python -m spac_kit.generator.cli --output packets.bin
```

#### Generate packets for specific APID(s)

```bash
poetry run python -m spac_kit.generator.cli --output packets.bin --apid 100 200
```

#### Generate multiple packets per APID

```bash
poetry run python -m spac_kit.generator.cli --output packets.bin --count 10
```

This generates 10 packets for each APID with incrementing sequence counts (0-9).

### Python API

#### Basic usage

```python
import ccsdspy
from spac_kit.generator import PacketGenerator

# Define packet structure
fields = [
    ccsdspy.PacketField(name="status", data_type="uint", bit_length=8),
    ccsdspy.PacketField(name="counter", data_type="uint", bit_length=16),
    ccsdspy.PacketField(name="temperature", data_type="float", bit_length=32),
]

packet_def = ccsdspy.VariableLength(fields, apid=100, name="SensorPacket")

# Create generator
generator = PacketGenerator(packet_def)

# Generate a single packet
packet_bytes = generator.generate_packet(sequence_count=0)

# Write multiple packets to a file
with open("output.bin", "wb") as f:
    generator.write_packet(f, count=5)
```

#### Generate from installed packet definitions

```python
from spac_kit.parser.util import import_ccsds_packet_packages
from spac_kit.generator import PacketGenerator

# Load all packet definitions from plugins
packets = import_ccsds_packet_packages()

# Generate packets for each definition
with open("all_packets.bin", "wb") as f:
    for pkt_info in packets:
        generator = PacketGenerator(pkt_info["packet"])
        generator.write_packet(f, count=1)
```

#### Working with arrays

```python
import ccsdspy
from spac_kit.generator import PacketGenerator

fields = [
    ccsdspy.PacketField(name="header", data_type="uint", bit_length=8),
    ccsdspy.PacketArray(
        name="data_array",
        data_type="uint",
        bit_length=8,
        array_shape=10
    ),
    ccsdspy.PacketField(name="footer", data_type="uint", bit_length=16),
]

packet_def = ccsdspy.VariableLength(fields, apid=200, name="ArrayPacket")
generator = PacketGenerator(packet_def)

packet_bytes = generator.generate_packet()
```

## Packet Structure

Generated packets follow the CCSDS Space Packet Protocol standard:

### CCSDS Primary Header (6 bytes)

| Field | Bits | Description |
|-------|------|-------------|
| Version | 3 | Always 0 |
| Type | 1 | 0 = telemetry, 1 = command |
| Secondary Header Flag | 1 | 0 = not present |
| APID | 11 | Application Process Identifier |
| Sequence Flags | 2 | 3 = standalone packet |
| Sequence Count | 14 | Packet sequence counter |
| Packet Length | 16 | Data field length - 1 |

### Data Field

All fields are initialized to zero:
- **uint/int**: 0
- **float/double**: 0.0
- **arrays**: All elements set to 0
- **fill**: Zero bytes

## Examples

See `examples/generate_packets_example.py` for a complete working example.

## Testing

Run the test suite:

```bash
poetry run pytest tests/generator/ -v
```

## Integration with SPaC-Kit Parser

Generated packets can be parsed using SPaC-Kit's parser:

```python
from spac_kit.generator import PacketGenerator
from spac_kit.parser import parse_ccsds_file
import ccsdspy

# Generate packets
fields = [
    ccsdspy.PacketField(name="data", data_type="uint", bit_length=8),
]
packet_def = ccsdspy.VariableLength(fields, apid=100, name="Test")
generator = PacketGenerator(packet_def)

with open("test.bin", "wb") as f:
    generator.write_packet(f, count=5)

# Parse them back
with open("test.bin", "rb") as f:
    dataframes = parse_ccsds_file(f)
    print(dataframes)
```

## Limitations

- Only supports packet definitions that inherit from `ccsdspy.packet_types._BasePacket`
- Expandable arrays (`array_shape="expand"`) are generated as empty arrays
- Secondary headers are not generated (flag is set to 0)
- CRC/checksums are not calculated (would need to be added separately if required)

## Future Enhancements

Potential improvements:
- Support for custom field values (not just zeros)
- CRC/checksum calculation
- Secondary header support
- Template-based generation with value ranges
- Random data generation options
