import importlib.metadata
import os
import shutil
from collections import defaultdict

from ccsdspy.packet_types import _BasePacket
from docutils import nodes
from sphinx import addnodes
from sphinx.directives import ObjectDescription
from sphinx.util import logging

logger = logging.getLogger(__name__)


def setup(app):
    app.add_directive("spacdocs", SpacDocsDirective)
    app.add_config_value("spacdocs_packet_modules", [], "env")
    app.add_config_value("spacdocs_exclude_columns", [], "env")
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
    def _load_packet(self, packet_obj_name):
        module_name, var_name = packet_obj_name.rsplit(".", 1)
        module = importlib.import_module(module_name)
        packet = getattr(module, var_name, None)
        if not isinstance(packet, _BasePacket):
            return None
        return packet

    def _gen_nodes(self, packet):
        result = []

        desc_node = addnodes.desc()
        desc_node["domain"] = "py"
        desc_node["objtype"] = "data"
        desc_node["noindex"] = False

        signature_node = addnodes.desc_signature("", "")
        signature_node += addnodes.desc_name(packet.name, packet.name)

        # Add the type info inline after the name
        type_inline = nodes.inline(
            "", f" (Type: {type(packet).__name__})", classes=["packet-type"]
        )
        signature_node += type_inline
        desc_node.append(signature_node)

        # Define all columns to show
        columns = [
            ("Name", "_name"),
            ("DataType", "_data_type"),
            ("BitLength", "_bit_length"),
            ("BitOffset", "_bit_offset"),
            ("ByteOrder", "_byte_order"),
            ("FieldType", "_field_type"),
            ("ArrayShape", "_array_shape"),
            ("ArrayOrder", "_array_order"),
        ]

        # Get columns to exclude from config
        exclude_columns = []
        if (
            hasattr(self, "state")
            and hasattr(self.state, "document")
            and hasattr(self.state.document, "settings")
            and hasattr(self.state.document.settings, "env")
        ):
            env = self.state.document.settings.env
            if hasattr(env, "config") and hasattr(
                env.config, "spacdocs_exclude_columns"
            ):
                exclude_columns = env.config.spacdocs_exclude_columns or []

        logger.info("[spacdocs] Excluding columns: %s", exclude_columns)
        filtered_columns = [col[0] for col in columns if col[0] not in exclude_columns]
        logger.info("[spacdocs] Using columns: %s", filtered_columns)

        content_node = addnodes.desc_content()
        field_sections = []

        # Table of all packet fields with all parameters, and sections for each field
        if packet._fields:
            fields_table = nodes.table()
            tgroup = nodes.tgroup(cols=len(filtered_columns))
            fields_table += tgroup

            for _ in filtered_columns:
                tgroup += nodes.colspec(colwidth=15)

            # --- Build header row ---
            thead = nodes.thead()
            tgroup += thead

            header_row = nodes.row()
            for header in filtered_columns:
                entry = nodes.entry()
                entry += nodes.paragraph(text=header)
                header_row += entry

            thead += header_row
            tbody = nodes.tbody()
            tgroup += tbody

            # Calculate dynamic bit offsets if not set
            running_offset = 0

            for field in packet._fields:
                section = nodes.section(ids=[f"field-{field._name}"])
                field_sections.append(section)
                section += nodes.title(text=field._name)

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

                row = nodes.row()

                for (colname, attr) in columns:
                    entry = nodes.entry()
                    value = getattr(field, attr, "")

                    # Special handling for Name column
                    if attr == "_name":
                        desc = getattr(field, "_description", None)

                        para = nodes.paragraph()
                        # Make the field name a reference link to the section below
                        ref_uri = f"#field-{value}"
                        ref = nodes.reference("", str(value), refuri=ref_uri)
                        para += ref

                        if desc:
                            # Add tooltip if description exists
                            safe_desc = (
                                str(desc).replace('"', "&quot;").replace("'", "&#39;")
                            )

                            # Inline SVG for Font Awesome info-circle (fa-info-circle)
                            svg_icon = (
                                '<span class="field-name-tooltip" style="margin-left:0.4em; vertical-align:middle; display:inline-block; cursor:pointer;">'
                                '<img src="/_static/circle-info.svg" alt="info" style="width:1em;height:1em;vertical-align:middle;display:inline-block;">'
                                f'<span class="tooltiptext">{safe_desc}</span>'
                                "</span>"
                            )
                            para += nodes.raw("", svg_icon, format="html")

                            # Also add description below the name in the section
                            section += nodes.paragraph(text=str(desc))

                        entry += para
                    else:
                        section_row = nodes.row()
                        section_col_name_entry = nodes.entry()
                        section_col_value_entry = nodes.entry()

                        section_tbody += section_row
                        section_row += section_col_name_entry
                        section_row += section_col_value_entry
                        section_col_name_entry += nodes.paragraph(text=colname)

                        # Special handling for BitOffset to show calculated offset
                        if attr == "_bit_offset":
                            if value is None or value == "":
                                value = running_offset
                            else:
                                value = value

                            value = str(value)
                        else:
                            # Format None as empty string
                            if value is None:
                                value = ""
                            else:
                                value = str(value)

                        section_col_value_entry += nodes.paragraph(text=value)
                        entry += nodes.paragraph(text=value)

                    if colname not in exclude_columns:
                        row += entry

                # After row, increment running_offset by this field's bit length
                bitlen = getattr(field, "_bit_length", 0)
                if bitlen is None:
                    bitlen = 0
                running_offset += int(bitlen)

                tbody += row
                section += section_table

            content_node += fields_table

            for field_section in field_sections:
                content_node += field_section

        desc_node.append(content_node)
        result.append(desc_node)

        return result

    def run(self):
        packet_obj_name = self.arguments[0]
        packet = self._load_packet(packet_obj_name)
        if packet is None:
            return []
        return self._gen_nodes(packet)
