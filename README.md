[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)

# SPaC-Kit

## ✨ Introduction

**SpaC-Kit** is a collection of Python tools for working with **CCSDS Space Packet**. It can generically:

- Parse data files into **Pandas DataFrames** or **Excel spreadsheets**
- **(Scheduled Feb 2026)** – Generate documentation in multiple formats (**HTML**, **Markdown**, **reStructuredText**, **PDF**)
- **(Scheduled Apr 2026)** – Generate simulated packets

SpaC-Kit supports mission or instrument-specific CCSDS packet structures via plugin packages built on the [**CCSDSPy** library](https://docs.ccsdspy.org/).

> [!IMPORTANT]
> **This library is currently in active development.**
>
> Some functions are placeholders and may not yet have full implementations. Expect ongoing updates and new features as the library evolves.

### 🔌 Available Plugins

- [Europa Clipper CCSDS packet definitions](https://github.com/joshgarde/europa-cliper-ccsds-plugin)
- Want to define your own CCSDS packets? [Open a ticket](https://github.com/CCSDSPy/SPaC-Kit/issues) to start the discussion.

## Acknowledgments

The work being done here heavily relies on the [CCSDSpy library](https://docs.ccsdspy.org/).
It has been started as part of the NASA Europa Clipper mission Science Data System development and it is being now funded by a NASA ROSES grant.



## Users

### Requirement

Tested with `python 3.9`.

Optionnally, but recommended, create a virtual environment:

    python3 -m venv my_virtual_env
    sournce my_virtual_env/bin/activate


### Install

Install you plugin library first, for example Europa-Clipper CCSDS packets definitions:

    git clone https://github.com/joshgarde/europa-cliper-ccsds-plugin.git
    cd europa-cliper-ccsds-plugin
    pip install .

Install the SPaC-Kit package:

    pip install spac-kit

### Use

    parse-downlink --file {your ccsds file}

See more options with:

    parse-downlink --help


## Developers

### Requirements

#### Python 3.9

#### Create a virtual environment

For example in command line:

    python3 -m venv venv
    source venv/bin/activate

#### Install CCSDSPy

To install the latest version of CCSDSPy:

    pip install git+https://github.com/CCSDSPy/ccsdspy.git


#### Deploy the project, for developers

Clone the repository

Install the package

    pip install -e '.[dev]'
    pre-commit install && pre-commit install -t pre-push

Run an example:

    python src/spa_kit/parse/downlink_to_excel.py

or

    spac-parse --help

or

    spac-parse --file ./data/ecm_mag_testcase6_cmds_split_out.log --bdsem --header


#### Build and publish the package

Update the version number in file `setup.cfg`

Create a tag in the repository

Build the project:

    python3 -m pip install --upgrade build
    rm -rf dist/
    python3 -m build


Publish the project:

    twine upload dist/*



## Acknowledgment

This package heavily relies on `ccsdspy` library (see https://github.com/CCSDSPy/ccsdspy).
