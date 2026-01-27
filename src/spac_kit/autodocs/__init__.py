import importlib.metadata
import os
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
    app.connect("builder-inited", generate_packet_stubs)
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
    TOCTREE_FILE = os.path.join(app.srcdir, "packet_index.rst")

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

        # if not (page_title == packet.name):
        signature_node = addnodes.desc_signature("", "")
        signature_node += addnodes.desc_name(packet.name, packet.name)
        # Add the type info inline after the name
        type_inline = nodes.inline(
            "", f" (Type: {type(packet).__name__})", classes=["packet-type"]
        )
        signature_node += type_inline
        desc_node.append(signature_node)

        content_node = addnodes.desc_content()

        # Bullet list of internal links to each packet field section
        if packet._fields:
            bullet_list = nodes.bullet_list()
            for field in packet._fields:
                # Create a hyperlink to the anchor for each field section
                ref_uri = f"#{field._name}"
                ref_node = nodes.reference("", "", refuri=ref_uri)
                ref_node += nodes.Text(field._name)
                para = nodes.paragraph()
                para += ref_node
                item = nodes.list_item()
                item += para
                bullet_list += item
            content_node += bullet_list

        desc_node.append(content_node)
        result.append(desc_node)

        # Dedicated section for each packet field
        for field in packet._fields:
            section = nodes.section(ids=[field._name])
            section += nodes.title(text=field._name)
            field_table = nodes.table()
            tgroup = nodes.tgroup(cols=5)
            field_table += tgroup
            for colwidth in [20, 20, 10, 10, 10]:
                tgroup += nodes.colspec(colwidth=colwidth)
            thead = nodes.thead()
            tgroup += thead
            header_row = nodes.row()
            for header in ["Name", "DataType", "BitLength", "BitOffset", "ByteOrder"]:
                entry = nodes.entry()
                entry += nodes.paragraph(text=header)
                header_row += entry
            thead += header_row
            tbody = nodes.tbody()
            tgroup += tbody
            row = nodes.row()
            for value in [
                field._name,
                field._data_type,
                field._bit_length,
                field._bit_offset,
                field._byte_order,
            ]:
                entry = nodes.entry()
                entry += nodes.paragraph(text=str(value))
                row += entry
            tbody += row
            section += field_table
            result.append(section)
        return result

    def run(self):
        packet_obj_name = self.arguments[0]
        packet = self._load_packet(packet_obj_name)
        if packet is None:
            return []
        return self._gen_nodes(packet)
