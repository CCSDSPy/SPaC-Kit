# pylint: disable=invalid-name
"""CCSDSpy packet specialized for configurable APID parsing."""
from typing import Callable

import ccsdspy


class SimpleAPIDPacket(ccsdspy.VariableLength):
    """Simple Packet definition, with name and associated APID."""

    def __init__(self, fields: list[ccsdspy.PacketField], name: str, apid: int):
        """Constructor."""
        super().__init__(fields, apid=apid, name=name)


class PreParserAPIDPacket(SimpleAPIDPacket):
    """Packet definition used to pre-parse packets.

    This is used when the structure vary for a single APID
    depending on one field in this packet.
    """

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(
        self,
        fields: list[ccsdspy.PacketField],
        name: str,
        apid: int,
        decision_field: str = None,
        decision_fun: Callable = lambda x: x,
    ):
        """Constructor."""
        super().__init__(fields, apid=apid, name=name)
        self.decision_field = decision_field
        self.decision_fun = decision_fun


class ParserSubAPIDPacket(SimpleAPIDPacket):
    """Packet definition associated to a specific flavor
    of structure within a single APID."""

    def __init__(
        self, fields: list[ccsdspy.PacketField], name: str, apid: int, sub_apid: int
    ):
        """Constructor."""
        super().__init__(fields, apid=apid, name=name)
        self.sub_apid = sub_apid
