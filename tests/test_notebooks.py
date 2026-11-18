"""Every Python cell in the notebooks must at least compile.

GPU notebooks only run on Kaggle, so a syntax error there costs a session.
Shell lines (`!...`) and %%bash cells are skipped.
"""

import json
from pathlib import Path

import pytest

NOTEBOOKS = sorted((Path(__file__).parent.parent / "notebooks").glob("*.ipynb"))


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.name)
def test_python_cells_compile(path):
    nb = json.loads(path.read_text(encoding="utf-8"))
    for i, cell in enumerate(nb["cells"]):
        src = "".join(cell["source"])
        if cell["cell_type"] != "code" or src.startswith("%%"):
            continue
        lines = ["pass" if line.lstrip().startswith("!") else line for line in src.splitlines()]
        compile("\n".join(lines), f"{path.name} cell {i}", "exec")
