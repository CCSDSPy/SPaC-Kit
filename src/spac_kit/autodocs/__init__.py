import importlib.metadata
import os
import shutil
from collections import defaultdict
from collections import namedtuple

from ccsdspy.packet_types import _BasePacket
from docutils import nodes
from sphinx import addnodes
from sphinx.directives import ObjectDescription
from sphinx.util import logging

logger = logging.getLogger(__name__)


def setup(app):
    app.add_directive("spacdocs", SpacDocsDirective)
    app.add_config_value("spacdocs_packet_modules", [], "env")
    app.add_css_file("spac-kit.css")

    app.connect("builder-inited", generate_packet_stubs)
    app.connect("config-inited", copy_static_css)

    return {
        "version": importlib.metadata.version("spac_kit"),
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


# --- Stub generation for packets ---
def generate_packet_stubs(app):
    """
    Scan for all _BasePacket instances in a configured module, generate .rst stubs for each,
    and update a master toctree file.
    """
    # --- Configuration ---
    # You may want to make this configurable via conf.py
    PACKET_MODULES = getattr(app.config, "spacdocs_packet_modules", [])
    STUB_DIR = os.path.join(app.srcdir, "_autopackets")
    TOCTREE_FILE = os.path.join(app.srcdir, "_packet_index.rst")

    logger.info("[spacdocs] generate_packet_stubs running, srcdir=%s", app.srcdir)
    logger.info("[spacdocs] PACKET_MODULES: %s", PACKET_MODULES)
    if not PACKET_MODULES:
        logger.warning(
            "[spacdocs] No PACKET_MODULES configured, skipping stub generation."
        )
        return

    os.makedirs(STUB_DIR, exist_ok=True)
    stub_infos = []  # List of dicts: {module_path, packet_name, stub_relpath}

    for modpath in PACKET_MODULES:
        logger.info("[spacdocs] Importing module: %s", modpath)
        try:
            module = importlib.import_module(modpath)
        except Exception as e:
            logger.error("[spacdocs] Failed to import %s: %s", modpath, e)
            continue
        found_packet = False
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, _BasePacket):
                found_packet = True
                full_var_path = f"{modpath}.{attr_name}"
                modpath_parts = modpath.split(".")
                last_modpart = modpath_parts[-1] if modpath_parts else ""

                # Avoid repeating the last module part if attr_name matches
                if attr_name == last_modpart:
                    stub_name = f"{modpath.replace('.', '_')}.rst"
                else:
                    stub_name = f"{modpath.replace('.', '_')}_{attr_name}.rst"
                stub_path = os.path.join(STUB_DIR, stub_name)

                # No toctree for fields; field listing is handled by the directive
                stub_content = f"{attr_name}\n{'='*len(attr_name)}\n\n.. spacdocs:: {full_var_path}\n\n"
                write_stub = True
                if os.path.exists(stub_path):
                    with open(stub_path, "r") as f:
                        existing = f.read()
                    if existing == stub_content:
                        write_stub = False
                if write_stub:
                    logger.info("[spacdocs] Writing stub: %s", stub_path)
                    with open(stub_path, "w") as f:
                        f.write(stub_content)
                stub_relpath = f"_autopackets/{stub_name}"
                stub_infos.append(
                    {
                        "module_path": modpath,
                        "packet_name": attr_name,
                        "stub_relpath": stub_relpath,
                    }
                )
        if not found_packet:
            logger.warning("[spacdocs] No _BasePacket instances found in %s", modpath)

    # Group stubs by parent module, child module, then packets
    # Build a 3-level hierarchy: parent module, child module, packet
    # parent = first N-1 parts, child = last part, packet = packet name
    # We'll use the module_path for parent/child splitting
    parent_to_child = defaultdict(lambda: defaultdict(list))
    for info in stub_infos:
        mod_parts = info["module_path"].split(".")
        if len(mod_parts) < 2:
            parent_mod = info["module_path"]
            child_mod = ""
        else:
            parent_mod = ".".join(mod_parts[:-1])
            child_mod = mod_parts[-1]
        parent_to_child[parent_mod][child_mod].append(
            (info["packet_name"], info["stub_relpath"])
        )

    toctree_content = ""
    for parent_mod, child_dict in parent_to_child.items():
        toctree_content += f"{parent_mod}\n{'='*len(parent_mod)}\n\n"
        for child_mod, packets in child_dict.items():
            child_header = child_mod if child_mod else "packets"
            toctree_content += f"{child_header}\n{'-'*len(child_header)}\n\n.. toctree::\n   :maxdepth: 2\n\n"
            for packet_name, stub in packets:
                toctree_content += f"   {stub}\n"
            toctree_content += "\n"
        toctree_content += "\n"

    write_toctree = True
    if os.path.exists(TOCTREE_FILE):
        with open(TOCTREE_FILE, "r") as f:
            existing = f.read()
        if existing == toctree_content:
            write_toctree = False
    if write_toctree:
        logger.info("[spacdocs] Writing toctree file: %s", TOCTREE_FILE)
        with open(TOCTREE_FILE, "w") as f:
            f.write(toctree_content)
    logger.info("[spacdocs] Stub files written: %d", len(stub_infos))
    logger.info("[spacdocs] Done with stub generation.")


def copy_static_css(app, _):
    # Dynamically set html_static_path if not set
    static_dirs = app.config.html_static_path
    if not static_dirs:
        app.config.html_static_path = ["_static"]
        static_dirs = ["_static"]

    static_dir = os.path.join(app.srcdir, static_dirs[0])

    # Ensure the static directory exists to avoid Sphinx warning
    os.makedirs(static_dir, exist_ok=True)

    # Find the resources directory in the extension package
    try:
        import pkg_resources

        resources_dir = pkg_resources.resource_filename(
            "spac_kit.autodocs", "resources"
        )
    except Exception:
        resources_dir = os.path.join(os.path.dirname(__file__), "resources")

    if not os.path.isdir(resources_dir):
        logger.warning(
            f"[spacdocs] Could not find resources directory to copy: {resources_dir}"
        )
        return

    for fname in os.listdir(resources_dir):
        src_path = os.path.join(resources_dir, fname)
        dest_path = os.path.join(static_dir, fname)
        if os.path.isfile(src_path):
            need_copy = True
            if os.path.exists(dest_path):
                with open(src_path, "rb") as f1, open(dest_path, "rb") as f2:
                    if f1.read() == f2.read():
                        need_copy = False

            if need_copy:
                shutil.copyfile(src_path, dest_path)
                logger.info(f"[spacdocs] Copied {fname} to {dest_path}")


class SpacDocsDirective(ObjectDescription):
    _Column = namedtuple("_Column", ["colname", "attr", "show_on_summary"])

    # Column definitions for all field attributes
    ALL_COLUMNS = [
        _Column("Name", "_name", True),
        _Column("DataType", "_data_type", True),
        _Column("BitLength", "_bit_length", True),
        _Column("BitOffset", "_bit_offset", True),
        _Column("ByteOrder", "_byte_order", True),
        _Column("FieldType", "_field_type", False),
        _Column("ArrayShape", "_array_shape", False),
        _Column("ArrayOrder", "_array_order", False),
    ]

    def _load_packet(self, packet_obj_name):
        """Load a packet instance from a module path."""
        module_name, var_name = packet_obj_name.rsplit(".", 1)
        module = importlib.import_module(module_name)
        packet = getattr(module, var_name, None)
        if not isinstance(packet, _BasePacket):
            return None
        return packet

    def _calculate_bit_offset(self, field, running_offset):
        """Calculate the bit offset for a field, using running offset if not explicitly set."""
        value = getattr(field, "_bit_offset", None)
        if value is None or value == "":
            return running_offset
        return value

    def _format_bit_offset(self, field, running_offset):
        """Format the bit offset, using running offset if not explicitly set."""
        value = self._calculate_bit_offset(field, running_offset)
        return str(value)

    def _format_data_type(self, field):
        """Format the data type with array notation if applicable."""
        data_type = getattr(field, "_data_type", None)
        array_shape = getattr(field, "_array_shape", None)

        if array_shape == "expand":
            return f"{str(data_type)}[]"
        elif isinstance(array_shape, tuple):
            return f'{str(data_type)}[{",".join(map(str, array_shape))}]'
        else:
            return str(data_type)

    def _format_field_value(self, field, attr):
        """Format a generic field attribute value for display."""
        value = getattr(field, attr, "")
        if value is None:
            return ""
        return str(value)

    def _get_formatted_value(self, field, attr, running_offset):
        """Route to the appropriate formatter based on the attribute."""
        if attr == "_data_type":
            return self._format_data_type(field)
        elif attr == "_bit_offset":
            return self._format_bit_offset(field, running_offset)
        else:
            return self._format_field_value(field, attr)

    def _create_name_entry_with_tooltip(self, field_name, description):
        """Create a table entry for the Name column with an optional tooltip."""
        para = nodes.paragraph()
        ref_uri = f"#field-{field_name}"
        ref = nodes.reference("", field_name, refuri=ref_uri)
        para += ref

        if description:
            safe_desc = str(description).replace('"', "&quot;").replace("'", "&#39;")
            svg_icon = (
                '<span class="field-name-tooltip" style="margin-left:0.4em; vertical-align:middle; display:inline-block; cursor:pointer;">'
                '<img src="/_static/circle-info.svg" alt="info" style="width:1em;height:1em;vertical-align:middle;display:inline-block;">'
                f'<span class="tooltiptext">{safe_desc}</span>'
                "</span>"
            )
            para += nodes.raw("", svg_icon, format="html")

        return para

    def _create_summary_table_row(self, field, running_offset):
        """Create a single row for the summary table."""
        row = nodes.row()

        for column in self.ALL_COLUMNS:
            # Only add entries for columns that should be shown in summary
            if not column.show_on_summary:
                continue

            entry = nodes.entry()

            if column.attr == "_name":
                field_name = getattr(field, column.attr, "")
                description = getattr(field, "_description", None)
                entry += self._create_name_entry_with_tooltip(field_name, description)
            else:
                value = self._get_formatted_value(field, column.attr, running_offset)
                entry += nodes.paragraph(text=value)

            row += entry

        return row

    def _create_detail_section_row(self, colname, value):
        """Create a single row for a field's detail section table."""
        section_row = nodes.row()
        section_col_name_entry = nodes.entry()
        section_col_value_entry = nodes.entry()

        section_row += section_col_name_entry
        section_row += section_col_value_entry

        section_col_name_entry += nodes.paragraph(text=colname)
        section_col_value_entry += nodes.paragraph(text=value)

        return section_row

    def _create_field_detail_section(self, field, running_offset):
        """Create a detailed section for a single field with all its attributes."""
        field_name = getattr(field, "_name", "")
        description = getattr(field, "_description", None)
        is_array = getattr(field, "_array_shape", None) is not None

        section = nodes.section(ids=[f"field-{field_name}"])
        section += nodes.title(text=field_name)

        if description:
            section += nodes.paragraph(text=str(description))

        # Create table for field attributes
        section_table = nodes.table()
        section_tgroup = nodes.tgroup(cols=2)
        section_table += section_tgroup

        section_tgroup += nodes.colspec(colwidth=30)
        section_tgroup += nodes.colspec(colwidth=70)

        section_thead = nodes.thead()
        section_tgroup += section_thead
        section_header_row = nodes.row()
        section_thead += section_header_row

        section_tbody = nodes.tbody()
        section_tgroup += section_tbody

        # Add rows for each attribute (except Name, which is the title)
        for colname, attr, _ in self.ALL_COLUMNS:
            if attr in ["_name", "_field_type"]:
                continue

            if not is_array and attr in ["_array_shape", "_array_order"]:
                continue

            value = self._get_formatted_value(field, attr, running_offset)
            section_row = self._create_detail_section_row(colname, value)
            section_tbody += section_row

        section += section_table
        return section

    def _create_summary_table_structure(self):
        """Create the structure of the summary table (header and empty body)."""
        # Count columns that should be shown in summary
        summary_columns = [col for col in self.ALL_COLUMNS if col.show_on_summary]
        num_cols = len(summary_columns)

        fields_table = nodes.table()
        tgroup = nodes.tgroup(cols=num_cols)
        fields_table += tgroup

        # Create colspecs only for columns shown in summary
        for _ in summary_columns:
            tgroup += nodes.colspec(colwidth=15)

        # Build header row
        thead = nodes.thead()
        tgroup += thead

        header_row = nodes.row()
        for column in summary_columns:
            entry = nodes.entry()
            entry += nodes.paragraph(text=column.colname)
            header_row += entry

        thead += header_row

        # Create empty body that will be populated
        tbody = nodes.tbody()
        tgroup += tbody

        return fields_table, tbody

    def _create_summary_and_detail_content(self, packet):
        """Create both summary table and detail sections in a single pass through fields."""
        # Create the summary table structure
        summary_table, summary_tbody = self._create_summary_table_structure()

        # Lists to collect detail sections
        detail_sections = []

        # Single loop through all fields
        running_offset = 0
        for field in packet._fields:
            # Create summary table row
            summary_row = self._create_summary_table_row(field, running_offset)
            summary_tbody += summary_row

            # Create detail section
            detail_section = self._create_field_detail_section(field, running_offset)
            detail_sections.append(detail_section)

            # Increment running offset by this field's bit length
            bitlen = getattr(field, "_bit_length", 0)
            if bitlen is None:
                bitlen = 0
            running_offset += int(bitlen)

        return summary_table, detail_sections

    def _gen_nodes(self, packet):
        """Generate documentation nodes for a packet."""
        result = []

        # Create the main description node structure
        desc_node = addnodes.desc()
        desc_node["domain"] = "py"
        desc_node["objtype"] = "data"
        desc_node["noindex"] = False

        # Create signature with packet name and type
        signature_node = addnodes.desc_signature("", "")
        signature_node += addnodes.desc_name(packet.name, packet.name)

        type_inline = nodes.inline(
            "", f" (Type: {type(packet).__name__})", classes=["packet-type"]
        )
        signature_node += type_inline
        desc_node.append(signature_node)

        content_node = addnodes.desc_content()

        # Generate documentation content if fields exist
        if packet._fields:
            # Create both summary table and detail sections in a single pass
            summary_table, detail_sections = self._create_summary_and_detail_content(
                packet
            )

            # Add summary table
            content_node += summary_table

            # Add detail sections
            for detail_section in detail_sections:
                content_node += detail_section

        desc_node.append(content_node)
        result.append(desc_node)

        return result

    def run(self):
        """Main entry point for the directive."""
        packet_obj_name = self.arguments[0]
        packet = self._load_packet(packet_obj_name)
        if packet is None:
            return []
        return self._gen_nodes(packet)
