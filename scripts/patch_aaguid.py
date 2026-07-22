#!/usr/bin/env python3
"""
Dynamic AAGUID Replacer for KeePassXC

This script dynamically searches a KeePassXC source tree for references
to the default KeePassXC Authenticator Attestation GUID (AAGUID) and replaces
them with a target AAGUID (such as the Apple iCloud Keychain AAGUID).

It dynamically computes all necessary representations:
 - Hyphenated UUID (lowercase and uppercase)
 - Unhyphenated Hex string (lowercase and uppercase)
 - Base64 and Base64URL representations (padded and unpadded)
 - Embedded binary AAGUIDs inside Base64 / Base64URL encoded test fixtures (e.g., attestationObject)

Usage:
    python3 patch_aaguid.py [--src-dir PATH] [--old-aaguid UUID] [--new-aaguid UUID]
"""

import argparse
import base64
import os
import re
import sys
import uuid

DEFAULT_OLD_AAGUID = "fdb141b2-5d84-443e-8a35-4698c205a502"
DEFAULT_NEW_AAGUID = "dd4ec289-e01d-41c9-bb89-70fa845d4bf2"  # Apple iCloud Keychain AAGUID

TEXT_EXTENSIONS = {
    ".cpp", ".h", ".hpp", ".c", ".cc", ".txt", ".json", ".cmake",
    ".ui", ".md", ".yml", ".yaml", ".in", ".pro", ".pri", ".qrc"
}


def parse_uuid(uuid_str: str) -> uuid.UUID:
    clean = uuid_str.replace("-", "").strip()
    if len(clean) != 32:
        raise ValueError(f"Invalid UUID string format: {uuid_str}")
    return uuid.UUID(clean)


def generate_replacements(old_u: uuid.UUID, new_u: uuid.UUID):
    old_bytes = old_u.bytes
    new_bytes = new_u.bytes

    replacements = []

    # 1. Hyphenated lower and upper
    replacements.append((str(old_u).lower(), str(new_u).lower()))
    replacements.append((str(old_u).upper(), str(new_u).upper()))

    # 2. Unhyphenated lower and upper
    replacements.append((old_u.hex.lower(), new_u.hex.lower()))
    replacements.append((old_u.hex.upper(), new_u.hex.upper()))

    # 3. Base64 & Base64URL representations of the 16-byte AAGUID
    b64_old = base64.b64encode(old_bytes).decode("ascii")
    b64_new = base64.b64encode(new_bytes).decode("ascii")
    replacements.append((b64_old, b64_new))
    replacements.append((b64_old.rstrip("="), b64_new.rstrip("=")))

    b64u_old = base64.urlsafe_b64encode(old_bytes).decode("ascii")
    b64u_new = base64.urlsafe_b64encode(new_bytes).decode("ascii")
    replacements.append((b64u_old, b64u_new))
    replacements.append((b64u_old.rstrip("="), b64u_new.rstrip("=")))

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for o, n in replacements:
        if o not in seen and o != n:
            seen.add(o)
            deduped.append((o, n))

    return old_bytes, new_bytes, deduped


def patch_content(content: str, old_bytes: bytes, new_bytes: bytes, replacements: list) -> tuple[str, int]:
    total_modifications = 0

    # 1. Direct text replacements
    for old_str, new_str in replacements:
        count = content.count(old_str)
        if count > 0:
            content = content.replace(old_str, new_str)
            total_modifications += count

    # 2. Base64 / Base64URL encoded structures matching
    def replace_b64_token(match):
        nonlocal total_modifications
        token = match.group(0)
        padding = len(token) % 4
        padded = token + ("=" * (4 - padding) if padding else "")
        try:
            data = base64.urlsafe_b64decode(padded)
            if old_bytes in data:
                patched_data = data.replace(old_bytes, new_bytes)
                res = base64.urlsafe_b64encode(patched_data).decode("ascii")
                if padding:
                    res = res[:-(4 - padding)]
                total_modifications += 1
                return res
        except Exception:
            pass
        return token

    content = re.sub(r"[A-Za-z0-9_-]{40,}", replace_b64_token, content)
    return content, total_modifications


def patch_directory(target_dir: str, old_aaguid: str, new_aaguid: str) -> int:
    old_u = parse_uuid(old_aaguid)
    new_u = parse_uuid(new_aaguid)

    print(f"[*] Target Directory: {target_dir}")
    print(f"[*] Upstream AAGUID: {old_u} ({old_u.hex})")
    print(f"[*] Replacement AAGUID: {new_u} ({new_u.hex})")

    old_bytes, new_bytes, replacements = generate_replacements(old_u, new_u)

    files_modified = 0
    total_replacements = 0

    for root, dirs, files in os.walk(target_dir):
        # Ignore hidden directories, build output, git internal state
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("build", "node_modules", "out")]

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext not in TEXT_EXTENSIONS and file not in ("CMakeLists.txt", "Makefile"):
                continue

            filepath = os.path.join(root, file)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                patched_content, mod_count = patch_content(content, old_bytes, new_bytes, replacements)

                if mod_count > 0 and patched_content != content:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(patched_content)
                    files_modified += 1
                    total_replacements += mod_count
                    rel_path = os.path.relpath(filepath, target_dir)
                    print(f"  [+] Patched: {rel_path} ({mod_count} replacement(s))")
            except Exception as e:
                print(f"  [!] Error processing {filepath}: {e}", file=sys.stderr)

    print(f"\n[*] Patch Summary: Modified {files_modified} file(s) with {total_replacements} total replacement(s).")
    return files_modified


def main():
    parser = argparse.ArgumentParser(description="Dynamically replace KeePassXC AAGUID in source tree.")
    parser.add_argument("--src-dir", default=".", help="Path to KeePassXC repository root (default: current directory)")
    parser.add_argument("--old-aaguid", default=DEFAULT_OLD_AAGUID, help=f"Upstream AAGUID (default: {DEFAULT_OLD_AAGUID})")
    parser.add_argument("--new-aaguid", default=DEFAULT_NEW_AAGUID, help=f"Replacement AAGUID (default: {DEFAULT_NEW_AAGUID})")

    args = parser.parse_args()

    if not os.path.isdir(args.src-dir if hasattr(args, "src-dir") else args.src_dir):
        print(f"[!] Error: Directory '{args.src_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    modified = patch_directory(args.src_dir, args.old_aaguid, args.new_aaguid)
    if modified == 0:
        print("[!] Warning: No AAGUID occurrences were found to replace. Check if upstream already changed or path is wrong.")


if __name__ == "__main__":
    main()
