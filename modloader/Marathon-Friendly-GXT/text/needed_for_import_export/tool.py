import re
import sys
from pathlib import Path

# ------------ CONFIG ------------
GXT_FILE = "./needed_for_import_export/american_full.txt"              # original [SECTION] style file
SCRIPT_FILE = "./needed_for_import_export/crc32_dictionary.txt"           # file containing //Cretaceous Runner Start
EXPORT_FILE = "cretaceous_runner.txt"  # exported list
# --------------------------------

def parse_gxt(path):
    """Parse GXT-style file into dict[section][key] = value"""
    data = {}
    current_section = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(";"):
                continue
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
                data.setdefault(current_section, {})
            else:
                if "=" in line and current_section:
                    k, v = line.split("=", 1)
                    data[current_section][k.strip()] = v.strip()
    return data

def find_keys_after_marker(path, marker="//Cretaceous Runner Start"):
    """Return all keys mentioned in SCRIPT_FILE after the marker line"""
    found = []
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    start = False
    for line in lines:
        if marker in line:
            start = True
            continue
        if start:
            found += re.findall(r"\b[A-Z0-9_]+\b", line)
    return set(found)

def export_strings(gxt_data, keys, out_path):
    """Export keys with values sorted alphabetically"""
    lookup = {k: v for section, kv in gxt_data.items() for k, v in kv.items()}

    # add CRC_* keys
    for key in lookup:
        if key.startswith("CRC_"):
            keys.add(key)

    exported = []
    for key in sorted(keys):
        if key in lookup:
            val = lookup[key]
            exported.append(f"[{key}]\n{val}")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(exported))
    print(f"Exported {len(exported)} strings → {out_path}")

def import_strings(gxt_path, export_path, out_path):
    """Rebuild GXT file with edited values from export"""
    # load edits
    edits = {}
    current_key = None
    with open(export_path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("[") and line.endswith("]"):
                current_key = line[1:-1]
            elif current_key:
                edits[current_key] = line
                current_key = None

    # rebuild original file with replaced values
    out_lines = []
    current_section = None
    with open(gxt_path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                current_section = stripped[1:-1]
                out_lines.append(line)
            elif "=" in stripped and current_section:
                k, v = stripped.split("=", 1)
                k = k.strip()
                if k in edits:
                    v = edits[k]
                out_lines.append(f"{k}={v}")
            else:
                out_lines.append(line)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))
    print(f"Rebuilt file with edits → {out_path}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "export"
    if mode == "export":
        gxt = parse_gxt(GXT_FILE)
        keys = find_keys_after_marker(SCRIPT_FILE)
        export_strings(gxt, keys, EXPORT_FILE)
    elif mode == "import":
        import_strings(GXT_FILE, EXPORT_FILE, "./needed_for_import_export/strings_edited.txt")
    else:
        print("Usage: python tool.py [export|import]")