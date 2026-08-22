"""Sector diagram (indicator tree) rendering.

Requires a system Graphviz install (the `dot` executable) -- the Python
`graphviz` package only shells out to it. On Windows, install from
https://graphviz.org/download/ and ensure `dot` is on PATH; on most Linux
distros, `apt install graphviz` / `dnf install graphviz`.
"""
from __future__ import annotations

import io
from pathlib import Path

import graphviz
import pandas as pd
from PIL import Image


def gerar_diagrama_setor(
    data: pd.DataFrame,
    setor_e: str,
    output_file: str | Path = "diagrama.png",
    width: int = 1600,
    height: int = 1000,
) -> None:
    """Renders one box per distinct `Pai` (parent group), listing its `Code`s, under a root node.

    `data` must have `Pai` and `Code` columns (the metadata table).
    """
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    elementos = list(pd.unique(data["Pai"]))

    g = graphviz.Digraph(graph_attr={"layout": "dot", "rankdir": "TB", "nodesep": "0.5", "ranksep": "0.3"})
    g.attr(
        "node",
        shape="box",
        style="filled",
        fontsize="20",
        width=str(round(9.14 / len(elementos), 2)),
        height="1.2",
    )
    g.node("node0", label=setor_e)

    for i, elemento in enumerate(elementos, start=1):
        codes = data.loc[data["Pai"] == elemento, "Code"]
        nomes1 = "\\n ".join(codes.astype(str))
        with g.subgraph(name=f"cluster_{i}") as c:
            c.attr(label=str(elemento), style="filled", fillcolor="cyan2")
            c.attr("node", style="filled", fillcolor="white", fontsize="12")
            c.node(f"node{i}", label=nomes1)
        g.edge("node0", f"node{i}", style="invis")

    png_bytes = g.pipe(format="png")
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    img = img.resize((width, height))
    img.save(path)
