import re
import sys
from pathlib import Path

# ------------ CONFIG ------------
GXT_FILE = "./needed_for_import_export/american_full.txt"              # original [SECTION] style file
SCRIPT_FILE = "./needed_for_import_export/crc32_dictionary.txt"           # file containing //Cretaceous Runner Start
EXPORT_FILE = "cretaceous_runner.txt"  # exported list
# --------------------------------

# Precompute CRC32 table for GTA style
CRC32_TABLE = []
for i in range(256):
    crc = i
    for _ in range(8):
        if crc & 1:
            crc = (crc >> 1) ^ 0xEDB88320
        else:
            crc >>= 1
    CRC32_TABLE.append(crc)


def gta_crc32(text: str) -> int:
    """Calculate GTA SA CRC32 (uppercase, no final XOR)."""
    crc = 0xFFFFFFFF
    for ch in text.upper():
        b = ord(ch) & 0xFF
        crc = ((crc >> 8) & 0x00FFFFFF) ^ CRC32_TABLE[(crc ^ b) & 0xFF]
    return crc


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


def import_strings(gxt_path, export_path, out_path, mission_file):
    """Rebuild GXT file with edited values from export + add new keys to [MAIN] and mission.txt"""
    # load edits
    edits = {}
    current_key = None
    with open(export_path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("[") and line.endswith("]"):
                current_key = line[1:-1]
            elif current_key is not None:
                edits[current_key] = line
                current_key = None

    # parse original file into dict
    gxt = parse_gxt(gxt_path)

    # track which keys were replaced
    replaced = set()

    # rebuild file
    out_lines = []
    current_section = None
    for raw in open(gxt_path, encoding="utf-8"):
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
                replaced.add(k)
            out_lines.append(f"{k}={v}")
        else:
            out_lines.append(line)

    # find new keys that weren’t in original
    new_keys = [k for k in edits if k not in replaced]

    if new_keys:
        print(f"Adding {len(new_keys)} new keys into [MAIN]...")
        # sort by GTA CRC32
        new_keys_sorted = sorted(new_keys, key=lambda k: gta_crc32(k))
        # build lines for new keys
        new_lines = [f"{k}={edits[k]}" for k in new_keys_sorted]

        # insert into [MAIN] section
        result_lines = []
        inserted = False
        for line in out_lines:
            result_lines.append(line)
            if line.strip().upper() == "[MAIN]":
                result_lines.extend(new_lines)
                inserted = True
        out_lines = result_lines
        if not inserted:
            # if no MAIN section existed, create it
            out_lines.append("[MAIN]")
            out_lines.extend(new_lines)

        # Append keys to mission.txt safely without duplicates
        with open(mission_file, "a+", encoding="utf-8") as f:
            f.seek(0)
            existing_keys = set(line.strip() for line in f if line.strip())
            # ensure last line is empty before appending if needed
            f.seek(0, 2)
            f_end = f.tell()
            if f_end > 0:
                f.seek(f_end - 1)
                if f.read(1) != "\n":
                    f.write("\n")
            # write only new keys not already present
            new_to_add = [k for k in new_keys_sorted if k not in existing_keys]
            for k in new_to_add:
                f.write(k + "\n")
        print(f"Added {len(new_to_add)} new keys to {mission_file}")



    # write output
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
        import_strings(GXT_FILE, EXPORT_FILE, "./needed_for_import_export/strings_edited.txt",SCRIPT_FILE)
    else:
        print("Usage: python tool.py [export|import]")
