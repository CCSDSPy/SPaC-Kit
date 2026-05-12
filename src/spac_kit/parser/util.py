"""Utilities shared."""
import importlib
import inspect
import pkgutil

import ccsdspy
from ccsdspy.constants import BITS_PER_BYTE

default_pkt = ccsdspy.VariableLength(
    [
        ccsdspy.PacketArray(
            name="data",
            data_type="uint",
            bit_length=BITS_PER_BYTE,
            array_shape="expand",
        )
    ]
)


def import_ccsds_packet_packages():
    """Import subpackages of ccsds.packets containing CCSDSpy definitions.

    Stolen from https://packaging.python.org/en/latest/guides/
    creating-and-discovering-plugins/#using-namespace-packages

    @return: list of dictionaries with keys: 'packet' (the packet object),
             'variable_name', 'module_path'
    """

    # TODO: use a constant for ccsds.packets
    import ccsds.packets  # pylint: disable=import-outside-toplevel,import-error

    parsers = []

    def is_ccsds_packet(attr):
        return isinstance(
            attr, ccsdspy.packet_types._BasePacket
        )  # pylint: disable=protected-access # noqa: E501

    for _, name, _ in pkgutil.walk_packages(
        ccsds.packets.__path__, ccsds.packets.__name__ + "."
    ):
        module = importlib.import_module(name)
        members = inspect.getmembers(module, is_ccsds_packet)
        for var_name, member in members:
            if hasattr(member, "apid"):
                parsers.append(
                    {"packet": member, "variable_name": var_name, "module_path": name}
                )

    return parsers
