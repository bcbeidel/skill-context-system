"""Root conftest — add all plugin scripts directories to sys.path.

Without __init__.py (which breaks plugin skill discovery), we cannot use
package imports like ``from skills.init.scripts.templates import ...``.
Instead, each scripts/ directory is added directly so tests can use
``from templates import ...``, ``from scaffold import ...``, etc.
"""

import sys
from pathlib import Path

_plugin_root = Path(__file__).resolve().parent / "dewey"

for scripts_dir in sorted(_plugin_root.rglob("scripts")):
    if scripts_dir.is_dir():
        path_str = str(scripts_dir)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
