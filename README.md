
<p align="center">
    <a href="https://imemix.github.io/">
        <img src="https://imemix.github.io/images/eminstaller.png" width="125"/>
    </a>
</p>


<p align="center">$\textcolor{green} {\text{CURRENTLY WORKING ✓}}$</p>
<p align="center">$\textcolor{red} {\text{NOT WORKING }}$</p>

[comment]: <> (DO NOT CHANGE ABOVE TEXT)
<br />
<br />

<p align="center">$\textcolor{blue} {\text{Installer could break at any time with being only one person maintaining the installer things will go wrong very frequently please check the documentation or stats page on mainsite}}$</p>
<p align="center">$\textcolor{blue} {\text{documentation or stats page on mainsite}}$</p>
<p align="center">$\textcolor{orange} {\text{Any issues found please make a issue and I will try and fix it.}}$</p>





<br />
<br />
<br />
<br />


# [MENU] Navigation

- [Status & Desktop Support](#status--desktop-support)
- [Quick Start](#quick-start)
- [Features](#features)
- [What It Does](#what-it-does)
- [Security Features](#security-features)
- [Documentation](#documentation)
- [Requirements](#-requirements)

---
EMInstaller is the ultimate Arch Linux terminal installer, a comprehensive Bash script that streamlines installation with an intuitive command‑line interface.

## Status & Desktop Support
- ✅ GNOME, KDE, Hyprland, XFCE, and i3 currently supported


## Quick Start

> 💡 **New:** You can now run the installer with a simple terminal GUI.  Add `--gui` to the command line and navigate with the arrow keys and Enter/Space.
>
> ```bash
> sudo python3 eminstaller.py --gui
> ```
>
> The curses‑based interface walks you through each configuration step.

## Quick Start

### Pre‑installation BIOS Settings
1. Boot in **UEFI mode**.
2. **Disable Secure Boot**.

### Standard Installation
Use the following one‑liner to download and execute the installer:

```bash
curl -s https://imemix.github.io/install | sudo bash
```

### Safe Method (*recommended for production*)
Download the script first so you can review it before running:

```bash
curl -O https://imemix.github.io/install
# inspect the file, then run:
sudo bash install
```

> See the [Safe Method documentation](https://imemix.github.io/documentation.html#safe-method) for details.
## Features

- **Lightning Fast** – Quick, efficient installation.
- **Easy Setup** – Intuitive command‑line configuration.
- **Customizable** – Tune options to your environment.
- **Real‑time Logs** – Watch progress as it happens.
- **Dependency Management** – Required packages installed automatically.
- **Robust Error Handling** – Script exits on failure with informative messages.

## What It Does

EMInstaller orchestrates a full Arch Linux installation by performing the following stages:

1. **Preparation** – Detects and configures the target environment.
2. **Dependencies** – Installs essential tools such as `curl` and `python3`.
3. **Payload Download** – Retrieves the latest installation payload.
4. **Execution** – Runs the payload using Python.

### Security Features

EMInstaller follows best practices to minimise risk:

- ✅ Verifies it is running as **root**.
- ✅ Uses `set -euo pipefail` to abort on errors, undefined variables, or pipe failures.
- ✅ Avoids executing uninitialised variables.
- ✅ Validates downloaded payloads via checksums before execution.

## Documentation

Full documentation is hosted online:

- 🔗 **Website:** [imemix.github.io](https://imemix.github.io/)
- 📄 **Documentation:** [EMInstaller Docs](https://imemix.github.io/documentation.html)

Key sections:

- **What Is EMInstaller?** – project overview
- **Quick Install** – step‑by‑step usage
- **Safe Method** – guidelines for manual inspection
- **Requirements** – prerequisites and supported environments
- **Testing Locally** – how to run the script in a dev setup
- **Updating** – keeping the installer current
- **Security Best Practices** – hardening tips
- **Advanced Usage** – power‑user options
- **Philosophy** – design rationale

## 🛠 Requirements

Make sure your environment meets the following:

- An **Arch Linux** system (or a close derivative).
- `bash` (available by default).
- `curl` for network transfers.
- `python3` to execute the installer payload.

If any tools are missing, install them with:

```bash
sudo pacman -S curl python
```

## Testing Locally

Clone or download the repository and make the script executable:

```bash
chmod +x install
```

Then execute it with root privileges:

```bash
sudo ./install
```


## Updating

Install the latest version at any time by re‑running the installation command:

```bash
curl -s https://imemix.github.io/install | sudo bash
```

The script always pulls the current release.

## Security Best Practices

Remote install scripts are convenient but pose risks. Follow these guidelines:

✅ **Do:**
- Use **HTTPS** for all downloads.
- Inspect the script before running it, especially in production.
- Verify checksums or signatures when available.
- Audit source code before redistribution.
- Prefer the safe method on critical systems.

❌ **Don’t:**
- Run untrusted code as root.
- Download via HTTP or from unknown hosts.
- Ignore verification steps.

### Example Secure Pattern

```bash
#!/usr/bin/env bash
set -euo pipefail

# require root
if [ "$(id -u)" -ne 0 ]; then
    echo "Please run with sudo."
    exit 1
fi

# download payload with integrity check
TMP="/tmp/eminstaller.py"
curl -sL "$RAW_URL" -o "$TMP"

# checksum verification
DOWNLOADED_SHA=$(sha256sum "$TMP" | awk '{print $1}')
if [ "$DOWNLOADED_SHA" != "$EXPECTED_SHA" ]; then
    echo "Checksum mismatch!"
    exit 1
fi

# execute
python3 "$TMP"
```


## Design Philosophy

Core guiding principles:

- **Minimal** – Keep functionality focused.
- **Transparent** – Code should be easy to read and follow.
- **Auditable** – Anyone should be able to verify behavior.
- **Deterministic** – Same inputs yield the same results.
- **Secure by default** – Safety prioritized over convenience.

> If you can’t quickly understand an install script, don’t run it.

### Desktop Environments

The installer now supports a wider range of graphical environments. When prompted interactively you may choose:

- `cli-only` – no graphical interface
- `gnome` – GNOME Shell (GDM)
- `kde` – KDE Plasma (SDDM)
- `hyprland` – Hyprland Wayland compositor (LightDM)
- `xfce` – XFCE4 desktop (LightDM)
- `i3` – i3 window manager (LightDM)

The script will automatically install and enable the appropriate display manager.# ⚠️ Important Notice

Piping remote content directly into `bash` is inherently risky:

```bash
curl https://example.com/install | bash
```

Only do this when you trust the source and have reviewed the code. In sensitive environments, use the safe download‑and‑inspect method.

## 🤝 Contributing

Contributions are appreciated! When submitting changes:

- Preserve security practices.
- Add robust error handling.
- Follow the project's coding style.
- Update documentation accordingly.

## 📄 License

This project is provided **as‑is** for Arch Linux installation tasks. See LICENSE for details.

## 🆘 Support

Need help? Try the following:

1. Consult the [online documentation](https://imemix.github.io/documentation.html).
2. Refer to the FAQ below.
3. Open an issue in the GitHub repository.

## ❓ FAQ

**Q: Is it safe to pipe the installer directly to bash?**  
A: For production use, download and review first. See the [Safe Method](https://imemix.github.io/documentation.html#safe-method).

**Q: What happens if the download fails?**  
A: The script exits immediately because of `set -euo pipefail`. Verify network connectivity and retry.

**Q: Will this work on non‑Arch distributions?**  
A: It targets Arch Linux; other distros are not officially supported.

**Q: Can I run the installer offline?**  
A: No. It requires internet access to fetch dependencies and payloads.

---

**Made with ❤️ for the Arch Linux community**

For more information, visit: [EMInstaller Documentation](https://imemix.github.io/documentation.html)
