"""Utilities shared."""
import importlib
import inspect
import os
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


def import_ccsds_packet_packages(extra_namespaces=None):
    """Import subpackages of ccsds.packets containing CCSDSpy definitions.

    Stolen from https://packaging.python.org/en/latest/guides/
    creating-and-discovering-plugins/#using-namespace-packages

    Args:
        extra_namespaces: Optional list of additional Python namespace strings
            to search (e.g. ["my.packets"]). Also reads the
            EXTRA_PACKET_NAMESPACES environment variable (comma-separated).

    Returns:
        List of dictionaries with keys: 'packet' (the packet object),
        'variable_name', 'module_path'
    """

    namespaces_to_add = list(extra_namespaces or [])
    env_val = os.environ.get("EXTRA_PACKET_NAMESPACES", "")
    if env_val:
        namespaces_to_add.extend(ns.strip() for ns in env_val.split(",") if ns.strip())

    namespace_modules = []

    try:
        # TODO: use a constant for ccsds.packets
        import ccsds.packets  # pylint: disable=import-outside-toplevel,import-error

        namespace_modules.append(ccsds.packets)
    except ImportError:
        if not namespaces_to_add:
            raise

    for ns_name in namespaces_to_add:
        namespace_modules.append(
            importlib.import_module(ns_name)  # pylint: disable=import-outside-toplevel
        )

    parsers = []

    def is_ccsds_packet(attr):
        return isinstance(
            attr,
            ccsdspy.packet_types._BasePacket,  # pylint: disable=protected-access # noqa: E501
        )

    for ns in namespace_modules:
        for _, name, _ in pkgutil.walk_packages(ns.__path__, ns.__name__ + "."):
            module = importlib.import_module(name)
            members = inspect.getmembers(module, is_ccsds_packet)
            for var_name, member in members:
                if hasattr(member, "apid"):
                    parsers.append(
                        {
                            "packet": member,
                            "variable_name": var_name,
                            "module_path": name,
                        }
                    )

    return parsers
