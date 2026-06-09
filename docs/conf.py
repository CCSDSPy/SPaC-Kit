import importlib.metadata

# Project information
metadata = importlib.metadata.metadata("spac-kit")
project = "SPaC-Kit"
author = metadata["Author"]
release = metadata["Version"]

import sys
import os

# Add the src directory to the path so Sphinx can find the modules
sys.path.insert(0, os.path.abspath("../src"))

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
]

autosummary_generate = True

# Napoleon settings for parsing docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True

html_theme = "alabaster"

html_theme_options = {
    "description": "A collection of tools for working with CCSDS Space Packets",
    "show_related": True,
    "github_banner": False,
    "github_button": False,
    "github_user": "ccsdspy",
    "github_repo": "spac-kit",
}
