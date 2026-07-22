# aaguid-bypass-keepassxc

Overlay repo for building custom [KeePassXC](https://github.com/keepassxreboot/keepassxc) binaries with dynamically patched WebAuthn/FIDO2 AAGUIDs (default: Managed iCloud Keychain).

## Usage

```bash
uv run scripts/patch_aaguid.py --src-dir /path/to/keepassxc-source --new-aaguid dd4ec289-e01d-41c9-bb89-70fa845d4bf2 [or any other "blessed" UUID]
```