# aaguid-bypass-keepassxc

Overlay repo for building custom [KeePassXC](https://github.com/keepassxreboot/keepassxc) binaries with dynamically patched WebAuthn/FIDO2 AAGUIDs (default: Managed iCloud Keychain).

## Purpose

Passkey providers are uniquely identified by their AAGUID.
This allows relying parties (RP) to filter out undesired clients.
Open source password managers are often disallowed because they do not hide the actual private key string from the user.
This is (erroneously) seen as a security anti-practice by big firms, so they disallow these clients.

This repository automatically builds Linux executables which omit KeePassXC's known AAGUID, allowing you to register with RPs that would have otherwise disallowed passkey registration.

Binaries produced by this repository are known to work with Chase Bank. 

Inspired by this issue: [secure.chase.com can't save passkeys](https://github.com/keepassxreboot/keepassxc-browser/issues/2995)

## Manual Usage

```bash
uv run scripts/patch_aaguid.py --src-dir /path/to/keepassxc-source --new-aaguid dd4ec289-e01d-41c9-bb89-70fa845d4bf2 [or any other "blessed" UUID]
```

## FAQ

> Do I need to replace my main KeePassXC installation with this patched version?

No. You only need to use this binary when registering a new passkey.
Most services only verify the AAGUID during initial setup, not during subsequent logins. Once registered, your passkeys will work normally with standard KeePassXC.