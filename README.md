[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)

# SPaC-Kit

## ✨ Introduction

**SpaC-Kit** is a collection of Python tools for working with **CCSDS Space Packets**. It can generically:

- Parses data files into **Pandas DataFrames** or **Excel spreadsheets**
- Generates CCSDS packets with zero/blank-initialized fields for testing
- **(Scheduled Feb 2026)** – Generates documentation in multiple formats (**HTML**, **Markdown**, **reStructuredText**, **PDF**)

SpaC-Kit supports mission or instrument-specific CCSDS packet structures via **plugin** packages built on the [**CCSDSPy** library](https://docs.ccsdspy.org/).

> [!IMPORTANT]
> **This library is currently in active development.**
>
> Some functions are placeholders and may not yet have full implementations. Expect ongoing updates and new features as the library evolves.

### 🔌 Available Mission/Instrument Plugins

- [Europa Clipper CCSDS packet definitions](https://github.com/nasa-jpl/spac-kit-europa-clipper)
- Want to define your own CCSDS packets? [Open a ticket](https://github.com/CCSDSPy/SPaC-Kit/issues) to start the discussion.


## Users

### Requirement

Tested with `python 3.12`.

Optionally, but recommended, create a virtual environment:

    python3 -m venv .venv
    source .venv/bin/activate


### Install

Install your plugin library first, for example Europa-Clipper CCSDS packets definitions:

    git clone https://github.com/nasa-jpl/spac-kit-europa-clipper.git
    cd spac-kit-europa-clipper
    pip install .

Install the SPaC-Kit package:

    pip install spac-kit

### Use

#### Parse CCSDS packets

    spac-parse --file {your ccsds file}

See more options with:

    spac-parse --help

#### Generate CCSDS packets

Generate packets for all installed packet definitions:

    spac-generate --output packets.bin

Generate packets for specific APID(s):

    spac-generate --output packets.bin --apid 100 200

Generate multiple packets per APID:

    spac-generate --output packets.bin --count 10

List available packet definitions:

    spac-ls

See more options with:

    spac-generate --help

#### Programmatic usage

The packet generator creates valid CCSDS packets with all fields initialized to zero/blank values, useful for testing packet parsing pipelines.

```python
import ccsdspy
from spac_kit.generator import PacketGenerator

# Define packet structure
fields = [
    ccsdspy.PacketField(name="status", data_type="uint", bit_length=8),
    ccsdspy.PacketField(name="temperature", data_type="float", bit_length=32),
]
packet_def = ccsdspy.VariableLength(fields, apid=100, name="SensorPacket")

# Generate packets
generator = PacketGenerator(packet_def)
with open("packets.bin", "wb") as f:
    generator.write_packet(f, count=5)  # Generate 5 packets
```


## Developers

### Requirements

#### Python 3.12

#### Create a virtual environment

SPaC-Kit handles development primarily via Poetry. To setup the repo, run:

    poetry env use python3.12
    poetry install --with dev

Then prefix your commands with `poetry run` to use the virtual environment, for example:

    poetry run spac-parse --help


#### Deploy the project, for developers

Clone the repository

Install the package


    pre-commit install && pre-commit install -t pre-push

Run an example:

    python src/spac_kit/parser/downlink_to_excel.py

or

    spac-parse --help

With poetry, update the `poetry.lock` before commiting and pushing to the github repository:

    poetry lock


#### Build and publish the package

Update the version number in file `pyproject.toml`

Create a tag in the repository and push the changes.

    git tag vX.Y.Z
    git push origin main --tags

Locally, you can do the following steps to build and publish the package.

    python3 -m pip install --upgrade build
    rm -rf dist/
    python3 -m build


Publish the project:

    pip install twine
    twine upload dist/*


### Other reference information for developers

- The package is released following [Semantic Versioning](https://semver.org/).
- We follow the [trunk-based branching strategy](https://www.atlassian.com/continuous-delivery/continuous-integration/trunk-based-development) since the development team is current reduced and we want to favor efficient of the releases. That mean we don't have a 'develop' branch.
- TO BE DONE: Continuous integration using GitHub Actions. It runs linting, unit test and code coverage on each Pull Request.
- The code follows the [PEP-8](https://peps.python.org/pep-0008/) style guide using [black](https://black.readthedocs.io/en/stable/) for formatting and [flake8](https://flake8.pycqa.org/en/latest/) for linting.



## Acknowledgments

The work being done here heavily relies on the [CCSDSpy library](https://docs.ccsdspy.org/).
It has been started as part of the NASA Europa Clipper mission Science Data System development and it is being now funded by a NASA ROSES grant.
