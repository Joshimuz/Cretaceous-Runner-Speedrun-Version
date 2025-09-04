import struct
import argparse
import binascii
import string
import logging
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Precomputed CRC32 table for GTA SA
def generate_crc32_table() -> List[int]:
    table = []
    for i in range(256):
        crc = i
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xEDB88320
            else:
                crc >>= 1
        table.append(crc)
    return table

CRC32_TABLE = generate_crc32_table()

def gta_crc32(text: str) -> int:
    """Calculate GTA SA CRC32 (uppercase, no final XOR)."""
    crc = 0xFFFFFFFF
    for ch in text.upper():
        b = ord(ch) & 0xFF
        crc = ((crc >> 8) & 0x00FFFFFF) ^ CRC32_TABLE[(crc ^ b) & 0xFF]
    return crc

def load_crc_dict(path: str) -> Tuple[Dict[int, str], Dict[str, int]]:
    """Load CRC dictionary from file."""
    crc_to_name = {}
    name_to_crc = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                name = line.strip()
                if not name:
                    continue
                if not all(c in string.printable for c in name):
                    logging.warning(f"Skipping invalid name in dict: {name}")
                    continue
                crc = gta_crc32(name)
                if crc in crc_to_name:
                    logging.warning(f"Duplicate CRC {crc:08X} for {name}")
                crc_to_name[crc] = name
                name_to_crc[name] = crc
    except FileNotFoundError:
        raise ValueError(f"CRC dictionary file not found: {path}")
    except UnicodeDecodeError:
        raise ValueError(f"CRC dictionary file must be UTF-8: {path}")
    if not crc_to_name:
        raise ValueError(f"CRC dictionary is empty: {path}")
    return crc_to_name, name_to_crc

def export_gxt(gxt_file: str, txt_file: str, crc_to_name: Dict[int, str]) -> None:
    """Export GXT file to TXT."""
    with open(gxt_file, "rb") as f:
        data = f.read()

    # Validate file size
    if len(data) < 12:  # Header (4) + TABL header (8)
        raise ValueError("GXT file too small")

    # Parse header
    version, bits = struct.unpack_from("<HH", data, 0)
    if version != 4 or bits != 8:
        raise ValueError(f"Invalid GXT header: version={version}, bits={bits} (expected 4, 8)")
    offset = 4

    # Parse TABL block
    if data[offset:offset+4] != b"TABL":
        raise ValueError("TABL block not found")
    tabl_size, = struct.unpack_from("<I", data, offset+4)
    if tabl_size % 12 != 0:
        raise ValueError(f"Invalid TABL size: {tabl_size}")
    num_tables = tabl_size // 12
    if num_tables > 200:
        raise ValueError(f"Too many tables: {num_tables} (max 200)")
    offset += 8
    logging.debug(f"Found {num_tables} tables")

    total_entries = 0
    with open(txt_file, "w", encoding="utf-8") as out:
        for i in range(num_tables):
            subname = data[offset:offset+8].decode("ascii", errors="ignore").rstrip("\0")
            if not subname:
                logging.warning(f"Table {i} has empty or invalid name")
            suboff, = struct.unpack_from("<I", data, offset+8)
            offset += 12

            if suboff >= len(data):
                raise ValueError(f"Invalid table offset for {subname}: {suboff}")

            base = suboff
            # Handle MAIN table (points directly to TKEY)
            if subname == "MAIN":
                tkey_base = base
            else:
                # Non-MAIN tables have an 8-byte name before TKEY
                if base + 8 > len(data):
                    raise ValueError(f"Invalid name offset for {subname}")
                table_name = data[base:base+8].decode("ascii", errors="ignore").rstrip("\0")
                if table_name != subname:
                    logging.warning(f"Table name mismatch for {subname}: expected {subname}, found {table_name}")
                tkey_base = base + 8

            # Parse TKEY block
            if tkey_base + 8 > len(data) or data[tkey_base:tkey_base+4] != b"TKEY":
                raise ValueError(f"TKEY not found for {subname}")
            tkey_size, = struct.unpack_from("<I", data, tkey_base+4)
            if tkey_size % 8 != 0:
                raise ValueError(f"Invalid TKEY size for {subname}: {tkey_size}")
            entries = tkey_size // 8
            tkey_base += 8

            # Parse TDAT block
            tdat_off = tkey_base + tkey_size
            if tdat_off + 8 > len(data) or data[tdat_off:tdat_off+4] != b"TDAT":
                raise ValueError(f"TDAT not found after TKEY for {subname}")
            tdat_size, = struct.unpack_from("<I", data, tdat_off+4)
            tdat_base = tdat_off + 8

            if tdat_base + tdat_size > len(data):
                raise ValueError(f"Invalid TDAT size for {subname}")

            # Check TKEY sorting
            crcs = []
            for j in range(entries):
                entry_off, crc = struct.unpack_from("<II", data, tkey_base + j*8)
                crcs.append(crc)
            if crcs != sorted(crcs):
                logging.warning(f"TKEY entries in {subname} are not sorted by CRC32")

            out.write(f"[{subname}]\n")
            total_entries += entries
            for j in range(entries):
                entry_off, crc = struct.unpack_from("<II", data, tkey_base + j*8)
                if tdat_base + entry_off >= len(data):
                    raise ValueError(f"Invalid entry offset in {subname}: {entry_off}")
                text_bytes = data[tdat_base + entry_off:]
                try:
                    text = text_bytes.split(b"\0", 1)[0].decode("cp1252")
                except UnicodeDecodeError:
                    logging.warning(f"Invalid cp1252 encoding for entry {crc:08X} in {subname}")
                    text = "<invalid encoding>"

                key = crc_to_name.get(crc, f"CRC_{crc:08X}")
                out.write(f"{key}={text}\n")
            out.write("\n")

    logging.debug(f"Exported {total_entries} entries across {num_tables} tables")

    # Check if all data was parsed
    expected_size = tdat_base + tdat_size
    if expected_size < len(data):
        logging.warning(f"Unparsed data in GXT: {len(data) - expected_size} bytes remaining")

def import_gxt(txt_file: str, gxt_file: str, name_to_crc: Dict[str, int]) -> None:
    """Import TXT file to GXT."""
    sections = {}
    current = None

    # Parse TXT file
    with open(txt_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            if line.startswith("[") and line.endswith("]"):
                current = line[1:-1]
                if len(current.encode("ascii")) > 8:
                    raise ValueError(f"Line {line_num}: Table name too long: {current}")
                if not current:
                    raise ValueError(f"Line {line_num}: Empty table name")
                if not all(c in string.printable for c in current):
                    raise ValueError(f"Line {line_num}: Invalid table name: {current}")
                sections[current] = []
            elif current is None:
                raise ValueError(f"Line {line_num}: Entry outside of section")
            else:
                try:
                    k, v = line.split("=", 1)
                except ValueError:
                    raise ValueError(f"Line {line_num}: Invalid format, expected key=value")
                if k in name_to_crc:
                    crc = name_to_crc[k]
                elif k.startswith("CRC_") and len(k) == 12:
                    try:
                        crc = int(k[4:], 16)
                    except ValueError:
                        raise ValueError(f"Line {line_num}: Invalid CRC format: {k}")
                else:
                    raise ValueError(f"Line {line_num}: Unknown key {k}")
                try:
                    v.encode("cp1252")
                except UnicodeEncodeError:
                    raise ValueError(f"Line {line_num}: Text not encodable in cp1252: {v}")
                sections[current].append((crc, v))

    if not sections:
        raise ValueError("No valid sections found in TXT file")
    if len(sections) > 200:
        raise ValueError(f"Too many tables: {len(sections)} (max 200)")

    total_entries = sum(len(entries) for entries in sections.values())
    logging.debug(f"Importing {total_entries} entries across {len(sections)} tables")

    with open(gxt_file, "wb") as out:
        # Write header
        out.write(struct.pack("<HH", 4, 8))  # Version 4, 8-bit ASCII

        # Write TABL block
        out.write(b"TABL")
        tabl_size = len(sections) * 12
        out.write(struct.pack("<I", tabl_size))

        # Reserve space for table entries (preserve order from TXT)
        subentries = []
        for sub in sections:  # Use insertion order (from TXT/export)
            out.write(sub.encode("ascii").ljust(8, b"\0"))
            subentries.append((sub, out.tell()))
            out.write(struct.pack("<I", 0))  # Placeholder offset

        # Build subtables with correct offset accumulation
        subtable_data = b""
        current_offset = out.tell()  # Start of subtable area
        for sub, pos in subentries:
            entries = sections[sub]
            # Do not sort entries (preserve original order for byte matching)
            table_block = b""
            if sub != "MAIN":
                table_block = sub.encode("ascii").ljust(8, b"\0")
            
            # Build TKEY block
            tkey_block = b"TKEY" + struct.pack("<I", len(entries) * 8)
            # Sort entries by CRC32
            entries_sorted = sorted(entries, key=lambda x: x[0])  # x[0] is crc
            tdat_entries = []
            tdat_data = b""
            for crc, text in entries_sorted:
                off = len(tdat_data)
                enc = text.encode("cp1252") + b"\0"
                tdat_data += enc
                tdat_entries.append((off, crc))
            
            # Append to TKEY in same order
            for off, crc in tdat_entries:
                tkey_block += struct.pack("<II", off, crc)
            
            tdat_block = b"TDAT" + struct.pack("<I", len(tdat_data)) + tdat_data
            
            # Accumulate subtable data
            sub_data = table_block + tkey_block + tdat_block
            subtable_data += sub_data
            
            # Set correct offset for this subtable
            out.seek(pos)
            out.write(struct.pack("<I", current_offset))
            
            # Update for next subtable
            current_offset += len(sub_data)
        
        # Write all subtable data at once
        out.seek(0, 2)
        out.write(subtable_data)
        logging.debug(f"Imported GXT file size: {out.tell()} bytes")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="GXT editor for GTA San Andreas")
    ap.add_argument("mode", choices=["export", "import"], help="Operation mode: export GXT to TXT or import TXT to GXT")
    ap.add_argument("input", help="Input file (GXT for export, TXT for import)")
    ap.add_argument("output", help="Output file (TXT for export, GXT for import)")
    ap.add_argument("--dict", required=True, help="Path to CRC dictionary file (UTF-8, one name per line)")
    ap.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = ap.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    crc_to_name, name_to_crc = load_crc_dict(args.dict)

    try:
        if args.mode == "export":
            export_gxt(args.input, args.output, crc_to_name)
            logging.info(f"Exported {args.input} to {args.output}")
        else:
            import_gxt(args.input, args.output, name_to_crc)
            logging.info(f"Imported {args.input} to {args.output}")
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        exit(1)