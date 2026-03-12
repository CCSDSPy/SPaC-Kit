"""Unit tests for SpacDocsDirective node generation methods."""
from docutils import nodes
from sphinx import addnodes


class TestCreateNameEntryWithTooltip:
    """Tests for _create_name_entry_with_tooltip method."""

    def test_create_name_without_description(self, mock_directive):
        """Test creating a name entry without description (no tooltip)."""
        result = mock_directive._create_name_entry_with_tooltip("my_field", None)

        # Should be a paragraph with a reference
        assert isinstance(result, nodes.paragraph)
        assert len(result) == 1
        assert isinstance(result[0], nodes.reference)
        assert result[0].astext() == "my_field"
        assert result[0]["refuri"] == "#field-my_field"

    def test_create_name_with_description(self, mock_directive):
        """Test creating a name entry with description (includes tooltip)."""
        result = mock_directive._create_name_entry_with_tooltip(
            "status_code", "Status indicator for health monitoring"
        )

        # Should be a paragraph with a reference and raw HTML
        assert isinstance(result, nodes.paragraph)
        assert len(result) == 2
        assert isinstance(result[0], nodes.reference)
        assert result[0].astext() == "status_code"
        assert isinstance(result[1], nodes.raw)
        assert "tooltiptext" in result[1].astext()
        assert "Status indicator for health monitoring" in result[1].astext()

    def test_description_escaping_quotes(self, mock_directive):
        """Test that quotes in descriptions are properly escaped."""
        result = mock_directive._create_name_entry_with_tooltip(
            "field", "Description with \"quotes\" and 'apostrophes'"
        )

        # Check that the raw HTML has escaped quotes
        raw_html = result[1].astext()
        assert "&quot;" in raw_html or "&#39;" in raw_html


class TestCreateSummaryTableRow:
    """Tests for _create_summary_table_row method."""

    def test_create_row_simple_field(self, mock_directive, mock_packet_field):
        """Test creating a summary table row for a simple field."""
        field = mock_packet_field(
            name="temp", data_type="float", bit_length=32, byte_order="big"
        )

        row = mock_directive._create_summary_table_row(field, running_offset=0)

        # Should be a nodes.row with entries for each summary column
        assert isinstance(row, nodes.row)
        # Count summary columns: Name, DataType, BitLength, BitOffset, ByteOrder (5)
        assert len(row.children) == 5

    def test_create_row_with_description(self, mock_directive, mock_packet_field):
        """Test that row includes tooltip when field has description."""
        field = mock_packet_field(
            name="status",
            data_type="uint",
            bit_length=8,
            description="System status code",
        )

        row = mock_directive._create_summary_table_row(field, running_offset=0)

        # First entry should be the name with tooltip
        first_entry = row.children[0]
        assert isinstance(first_entry, nodes.entry)
        # Should contain paragraph with reference and raw HTML
        assert len(first_entry.children) > 0

    def test_create_row_uses_running_offset(self, mock_directive, mock_packet_field):
        """Test that running offset is used when bit_offset is None."""
        field = mock_packet_field(
            name="field1", data_type="uint", bit_length=16, bit_offset=None
        )

        row = mock_directive._create_summary_table_row(field, running_offset=128)

        # Fourth entry should be BitOffset
        offset_entry = row.children[3]
        assert isinstance(offset_entry, nodes.entry)
        # Should contain paragraph with text "128"
        assert offset_entry.children[0].astext() == "128"


class TestCreateDetailSectionRow:
    """Tests for _create_detail_section_row method."""

    def test_create_detail_row(self, mock_directive):
        """Test creating a detail section row."""
        row = mock_directive._create_detail_section_row("DataType", "uint")

        # Should be a row with two entries
        assert isinstance(row, nodes.row)
        assert len(row.children) == 2

        # First entry is the label
        assert row.children[0].children[0].astext() == "DataType"

        # Second entry is the value
        assert row.children[1].children[0].astext() == "uint"


class TestCreateFieldDetailSection:
    """Tests for _create_field_detail_section method."""

    def test_create_detail_section_simple_field(
        self, mock_directive, mock_packet_field
    ):
        """Test creating detail section for a simple (non-array) field."""
        field = mock_packet_field(
            name="temperature",
            data_type="float",
            bit_length=32,
            byte_order="big",
            description="Temperature in Kelvin",
        )

        section = mock_directive._create_field_detail_section(field, running_offset=0)

        # Should be a section with an ID
        assert isinstance(section, nodes.section)
        assert section["ids"] == ["field-temperature"]

        # Should have a title
        assert section.children[0].astext() == "temperature"

        # Should have a description paragraph
        assert any("Temperature in Kelvin" in str(child) for child in section.children)

        # Should have a table
        has_table = any(isinstance(child, nodes.table) for child in section.children)
        assert has_table

    def test_create_detail_section_array_field(self, mock_directive, mock_packet_field):
        """Test creating detail section for an array field."""
        field = mock_packet_field(
            name="data_array",
            data_type="uint",
            bit_length=8,
            array_shape="expand",
            array_order="C",
        )

        section = mock_directive._create_field_detail_section(field, running_offset=0)

        # Should include array-specific attributes
        assert isinstance(section, nodes.section)

        # Find the table and check it has array attributes
        table = None
        for child in section.children:
            if isinstance(child, nodes.table):
                table = child
                break

        assert table is not None

    def test_create_detail_section_without_description(
        self, mock_directive, mock_packet_field
    ):
        """Test creating detail section for field without description."""
        field = mock_packet_field(
            name="counter", data_type="uint", bit_length=16, description=None
        )

        section = mock_directive._create_field_detail_section(field, running_offset=0)

        # Should still create section, just without description paragraph
        assert isinstance(section, nodes.section)
        assert section["ids"] == ["field-counter"]


class TestCreateSummaryTableStructure:
    """Tests for _create_summary_table_structure method."""

    def test_create_table_structure(self, mock_directive):
        """Test creating the summary table structure."""
        table, tbody = mock_directive._create_summary_table_structure()

        # Should return a table and tbody
        assert isinstance(table, nodes.table)
        assert isinstance(tbody, nodes.tbody)

        # Table should have proper structure
        assert len(table.children) == 1  # tgroup
        tgroup = table.children[0]

        # Should have colspecs for summary columns (5 columns)
        colspecs = [
            child for child in tgroup.children if isinstance(child, nodes.colspec)
        ]
        assert len(colspecs) == 5

        # Should have a header
        thead = [child for child in tgroup.children if isinstance(child, nodes.thead)][
            0
        ]
        assert len(thead.children) == 1  # header row

        # Header row should have entries for each summary column
        header_row = thead.children[0]
        assert len(header_row.children) == 5


class TestCreateSummaryAndDetailContent:
    """Tests for _create_summary_and_detail_content method."""

    def test_create_content_for_simple_packet(self, mock_directive, mock_simple_packet):
        """Test creating content for a packet with simple fields."""
        (
            summary_table,
            detail_sections,
        ) = mock_directive._create_summary_and_detail_content(mock_simple_packet)

        # Should return table and list of sections
        assert isinstance(summary_table, nodes.table)
        assert isinstance(detail_sections, list)
        assert len(detail_sections) == 3  # One for each field

        # Each detail section should be a proper section
        for section in detail_sections:
            assert isinstance(section, nodes.section)

    def test_running_offset_calculation(self, mock_directive, mock_simple_packet):
        """Test that running offset is correctly accumulated."""
        (
            summary_table,
            detail_sections,
        ) = mock_directive._create_summary_and_detail_content(mock_simple_packet)

        # Verify table has correct number of rows in tbody
        tgroup = summary_table.children[0]
        tbody = [child for child in tgroup.children if isinstance(child, nodes.tbody)][
            0
        ]
        assert len(tbody.children) == 3  # Three fields

    def test_create_content_for_array_packet(self, mock_directive, mock_array_packet):
        """Test creating content for a packet with array fields."""
        (
            summary_table,
            detail_sections,
        ) = mock_directive._create_summary_and_detail_content(mock_array_packet)

        # Should handle array fields correctly
        assert len(detail_sections) == 3
        assert all(isinstance(section, nodes.section) for section in detail_sections)


class TestGenNodes:
    """Tests for _gen_nodes method."""

    def test_gen_nodes_creates_desc_node(self, mock_directive, mock_simple_packet):
        """Test that _gen_nodes creates proper description node."""
        nodes_list = mock_directive._gen_nodes(mock_simple_packet)

        # Should return a list with one desc node
        assert len(nodes_list) == 1
        assert isinstance(nodes_list[0], addnodes.desc)

        desc_node = nodes_list[0]
        assert desc_node["domain"] == "py"
        assert desc_node["objtype"] == "data"
        assert desc_node["noindex"] is False

    def test_gen_nodes_includes_packet_name(self, mock_directive, mock_simple_packet):
        """Test that generated nodes include packet name."""
        nodes_list = mock_directive._gen_nodes(mock_simple_packet)
        desc_node = nodes_list[0]

        # Find the signature node
        signature = desc_node.children[0]
        assert isinstance(signature, addnodes.desc_signature)

        # Should contain packet name
        assert "TestPacket" in signature.astext()

    def test_gen_nodes_includes_packet_type(self, mock_directive, mock_simple_packet):
        """Test that generated nodes include packet type."""
        nodes_list = mock_directive._gen_nodes(mock_simple_packet)
        desc_node = nodes_list[0]

        signature = desc_node.children[0]
        # Should mention the type
        assert "Type:" in signature.astext() or "MagicMock" in signature.astext()

    def test_gen_nodes_includes_content(self, mock_directive, mock_simple_packet):
        """Test that generated nodes include content section."""
        nodes_list = mock_directive._gen_nodes(mock_simple_packet)
        desc_node = nodes_list[0]

        # Should have content node
        content = desc_node.children[1]
        assert isinstance(content, addnodes.desc_content)

        # Content should have children (table and sections)
        assert len(content.children) > 0
