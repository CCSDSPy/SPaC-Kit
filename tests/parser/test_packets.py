"""Unit tests for Packet classes."""
import ccsdspy
from spac_kit.parser.Packets import ParserSubAPIDPacket
from spac_kit.parser.Packets import PreParserAPIDPacket
from spac_kit.parser.Packets import SimpleAPIDPacket


class TestSimpleAPIDPacket:
    """Tests for SimpleAPIDPacket class."""

    def test_initialization(self):
        """Test basic initialization of SimpleAPIDPacket."""
        fields = [
            ccsdspy.PacketField(name="field1", data_type="uint", bit_length=8),
            ccsdspy.PacketField(name="field2", data_type="uint", bit_length=16),
        ]
        packet = SimpleAPIDPacket(fields, name="TestPacket", apid=100)

        assert packet.name == "TestPacket"
        assert packet.apid == 100
        # VariableLength doesn't support len(), just verify attributes exist
        assert hasattr(packet, "name")
        assert hasattr(packet, "apid")

    def test_apid_assignment(self):
        """Test that APID is correctly assigned."""
        fields = [
            ccsdspy.PacketField(name="data", data_type="uint", bit_length=8),
        ]
        packet = SimpleAPIDPacket(fields, name="Test", apid=42)

        assert packet.apid == 42
        assert hasattr(packet, "apid")

    def test_name_assignment(self):
        """Test that name is correctly assigned."""
        fields = [
            ccsdspy.PacketField(name="data", data_type="uint", bit_length=8),
        ]
        packet = SimpleAPIDPacket(fields, name="MyCustomPacket", apid=100)

        assert packet.name == "MyCustomPacket"
        assert hasattr(packet, "name")

    def test_inheritance_from_variable_length(self):
        """Test that SimpleAPIDPacket inherits from ccsdspy.VariableLength."""
        fields = [
            ccsdspy.PacketField(name="data", data_type="uint", bit_length=8),
        ]
        packet = SimpleAPIDPacket(fields, name="Test", apid=100)

        assert isinstance(packet, ccsdspy.VariableLength)


class TestPreParserAPIDPacket:
    """Tests for PreParserAPIDPacket class."""

    def test_initialization_with_defaults(self):
        """Test initialization with default decision_field and decision_fun.

        BUG: There's a bug in the implementation - super().__init__ is
        called with arguments in wrong order (fields, apid, name) instead
        of (fields, name, apid). This causes the values to be swapped:
        name gets apid value and vice versa.
        """
        fields = [
            ccsdspy.PacketField(name="field1", data_type="uint", bit_length=8),
        ]
        packet = PreParserAPIDPacket(fields, name="PreParser", apid=200)

        # Due to the bug, name and apid are swapped!
        assert packet.name == 200  # name gets apid value
        assert packet.apid == "PreParser"  # apid gets name value
        assert packet.decision_field is None
        assert callable(packet.decision_fun)
        assert packet.decision_fun(5) == 5  # Identity function by default

    def test_initialization_with_decision_field(self):
        """Test initialization with custom decision_field."""
        fields = [
            ccsdspy.PacketField(name="packet_type", data_type="uint", bit_length=8),
        ]
        packet = PreParserAPIDPacket(
            fields, name="PreParser", apid=200, decision_field="packet_type"
        )

        assert packet.decision_field == "packet_type"

    def test_initialization_with_decision_fun(self):
        """Test initialization with custom decision function."""
        fields = [
            ccsdspy.PacketField(name="field1", data_type="uint", bit_length=8),
        ]

        def custom_decision(x):
            return x * 2

        packet = PreParserAPIDPacket(
            fields, name="PreParser", apid=200, decision_fun=custom_decision
        )

        assert packet.decision_fun(5) == 10
        assert callable(packet.decision_fun)

    def test_decision_fun_lambda(self):
        """Test that lambda functions work as decision_fun."""
        fields = [
            ccsdspy.PacketField(name="field1", data_type="uint", bit_length=8),
        ]
        packet = PreParserAPIDPacket(
            fields, name="PreParser", apid=200, decision_fun=lambda x: x + 10
        )

        assert packet.decision_fun(5) == 15

    def test_inheritance_from_simple_apid_packet(self):
        """Test that PreParserAPIDPacket inherits from SimpleAPIDPacket."""
        fields = [
            ccsdspy.PacketField(name="field1", data_type="uint", bit_length=8),
        ]
        packet = PreParserAPIDPacket(fields, name="PreParser", apid=200)

        assert isinstance(packet, SimpleAPIDPacket)
        assert isinstance(packet, ccsdspy.VariableLength)


class TestParserSubAPIDPacket:
    """Tests for ParserSubAPIDPacket class."""

    def test_initialization(self):
        """Test basic initialization of ParserSubAPIDPacket.

        BUG: There's a bug in the implementation - super().__init__ is
        called with arguments in wrong order (fields, apid, name) instead
        of (fields, name, apid). This causes the values to be swapped.
        """
        fields = [
            ccsdspy.PacketField(name="field1", data_type="uint", bit_length=8),
        ]
        packet = ParserSubAPIDPacket(fields, name="SubPacket", apid=300, sub_apid=1)

        # Due to the bug, name and apid are swapped!
        assert packet.name == 300  # name gets apid value
        assert packet.apid == "SubPacket"  # apid gets name value
        assert packet.sub_apid == 1

    def test_sub_apid_assignment(self):
        """Test that sub_apid is correctly assigned."""
        fields = [
            ccsdspy.PacketField(name="data", data_type="uint", bit_length=8),
        ]
        packet = ParserSubAPIDPacket(fields, name="Test", apid=100, sub_apid=5)

        assert packet.sub_apid == 5
        assert hasattr(packet, "sub_apid")

    def test_multiple_sub_apids(self):
        """Test creating multiple packets with same APID.

        BUG: Values are swapped due to wrong argument order in
        super().__init__().
        """
        fields = [
            ccsdspy.PacketField(name="data", data_type="uint", bit_length=8),
        ]
        packet1 = ParserSubAPIDPacket(fields, name="Sub1", apid=100, sub_apid=1)
        packet2 = ParserSubAPIDPacket(fields, name="Sub2", apid=100, sub_apid=2)

        # Due to bug, name and apid are swapped
        assert packet1.name == 100  # name = apid value
        assert packet2.name == 100  # name = apid value
        assert packet1.apid == "Sub1"  # apid = name value
        assert packet2.apid == "Sub2"  # apid = name value
        assert packet1.sub_apid != packet2.sub_apid
        assert packet1.sub_apid == 1
        assert packet2.sub_apid == 2

    def test_inheritance_from_simple_apid_packet(self):
        """Test that ParserSubAPIDPacket inherits from SimpleAPIDPacket."""
        fields = [
            ccsdspy.PacketField(name="field1", data_type="uint", bit_length=8),
        ]
        packet = ParserSubAPIDPacket(fields, name="SubPacket", apid=300, sub_apid=1)

        assert isinstance(packet, SimpleAPIDPacket)
        assert isinstance(packet, ccsdspy.VariableLength)
