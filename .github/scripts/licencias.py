"""Writes LICENCIAS.txt for the Forja release from engine/data/assets.toml."""
import sys
import tomllib

manifest, out = sys.argv[1], sys.argv[2]
with open(manifest, "rb") as f:
    assets = tomllib.load(f)["asset"]

lines = [
    "FORJA - LICENCIAS",
    "=================",
    "",
    "Codigo de Forja: MIT o Apache-2.0.",
    "",
    "Contenido de terceros que el juego puede descargar (data/assets.toml).",
    "Tras la primera descarga, assets/downloaded/ATTRIBUTION.md lista lo",
    "descargado realmente. Los creditos CC-BY se mantienen aqui y alli.",
    "",
]
for a in assets:
    if a.get("sketchfab") or a.get("manual"):
        continue
    credit = "requiere atribucion" if a["license"].strip().upper() != "CC0-1.0" else "sin atribucion obligatoria"
    lines.append(f"- {a['name']}")
    lines.append(f"    {a['author']} - {a['license']} ({credit}) - {a['homepage']}")
with open(out, "w", encoding="utf-8", newline="\r\n") as f:
    f.write("\n".join(lines) + "\n")
