#!/usr/bin/env python3
"""Inspect an Adobe MOGRT safely, without promising After Effects rendering.

Usage: python scripts/tools/inspeccionar_mogrt.py plantilla.mogrt
"""
import argparse
import json
import pathlib
import zipfile

def inspect(path: pathlib.Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        files = archive.infolist()
        if len(files) > 3000 or sum(f.file_size for f in files) > 1024 * 1024 * 1024:
            raise ValueError("Plantilla excesivamente grande")
        for entry in files:
            parts = pathlib.PurePosixPath(entry.filename).parts
            if entry.filename.startswith("/") or ".." in parts:
                raise ValueError("Ruta interna insegura")
        metadata = []
        for entry in files:
            if entry.filename.lower().endswith((".json", ".xml")) and entry.file_size < 2_000_000:
                metadata.append(entry.filename)
        return {
            "archivo": path.name,
            "es_zip_valido": True,
            "total_archivos": len(files),
            "archivos_metadata": metadata,
            "advertencia": "Inspección solamente: Concat no puede renderizar ni editar proyectos After Effects (.mogrt).",
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archivo", type=pathlib.Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.archivo), ensure_ascii=False, indent=2))
