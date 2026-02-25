# $\textrm{\color{red}{THIS IS A MASSIVE WIP* NOT EVERYTHING WORKS.}}$

- GNOME and KDE work
- HYPRLAND, XFCE and i3 does not work


# EMInstaller

> **The Ultimate Arch Linux Terminal Installer**

A comprehensive Bash script designed to streamline and simplify Arch Linux installation with an intuitive command-line interface.

## 🚀 Quick Start

### Installation

Run the installer with a single command:

```bash
curl -s https://imemix.github.io/install | sudo bash
```

### Safe Method (Recommended for Production)

For security-sensitive environments, download and inspect the script before execution:

```bash
# Download the installer
curl -O https://imemix.github.io/install
```

## ✨ Features

- ⚡ **Lightning Fast** - Quick and efficient installation process
- 🎯 **Easy Setup** - Intuitive interface for seamless configuration
- 🔧 **Customizable** - Adjust settings to match your needs
- 📊 **Real-time Logs** - Monitor installation progress live
- 📦 **Dependency Management** - Automatic installation of required packages
- ✅ **Error Handling** - Robust error detection and reporting

## 📋 What It Does

EMInstaller automates the Arch Linux installation process by:

1. **Preparing the System** - Sets up your system environment
2. **Installing Dependencies** - Installs required packages (curl, python, etc.)
3. **Downloading Payload** - Fetches the main installer
4. **Executing Installation** - Launches the installer with Python

### Security Features

- ✅ Mandatory root privilege verification
- ✅ Error-on-failure mode (`set -euo pipefail`)
- ✅ No execution of undefined variables
- ✅ Pipe failure detection

## 📚 Documentation

Comprehensive documentation is available at:

### Online Documentation
- **Full Docs:** [EMInstaller Documentation](https://imemix.github.io/EMInstaller/documentation.html)
- **Website:** [EMInstaller Home](https://imemix.github.io/EMInstaller/)

### Documentation Sections

- [What Is EMInstaller?](https://imemix.github.io/documentation.html#what-is) - Overview and purpose
- [Quick Install](https://imemix.github.io/documentation.html#quick-install) - Standard installation method
- [Safe Method](https://imemix.github.io/documentation.html#safe-method) - Manual inspection approach
- [What It Does](https://imemix.github.io/documentation.html#what-does) - Installation flow and security patterns
- [Requirements](https://imemix.github.io/documentation.html#requirements) - System prerequisites
- [Testing Locally](https://imemix.github.io/documentation.html#testing) - Local script testing
- [Updating](https://imemix.github.io/documentation.html#updating) - Version updates
- [Security Best Practices](https://imemix.github.io/documentation.html#security) - Security guidelines
- [Advanced Usage](https://imemix.github.io/documentation.html#advanced) - Advanced configurations
- [Philosophy](https://imemix.github.io/documentation.html#philosophy) - Design principles

## 🛠 Requirements

Before running EMInstaller, ensure your system has:

- **Arch Linux** (or compatible distribution)
- **curl** - for downloading files
- **bash** - shell environment
- **python3** - Python interpreter

### Install Missing Dependencies

```bash
sudo pacman -S curl python
```

## 🧪 Testing Locally

### Make the Script Executable

```bash
chmod +x install
```

### Run the Installer

```bash
sudo ./install
```

## 🔄 Updating

To update to the latest version, simply re-run the installation command:

```bash
curl -s https://imemix.github.io/install | sudo bash
```

The script automatically fetches the latest version.

## 🔐 Security Best Practices

When using remote install scripts:

✅ **DO:**
- Always use HTTPS for downloads
- Manually inspect scripts in production environments
- Verify checksums before execution
- Audit scripts before distributing
- Use the safe method for sensitive systems

❌ **DON'T:**
- Run untrusted scripts as root
- Use HTTP for script downloads
- Skip security verification steps
- Download from unknown sources

### Security Pattern Used

```bash
#!/usr/bin/env bash
set -euo pipefail

# Verify root
if [ "$(id -u)" -ne 0 ]; then
    echo "Please run with sudo."
    exit 1
fi

# Download with integrity check
TMP="/tmp/eminstaller.py"
curl -sL "$RAW_URL" -o "$TMP"

# Verify checksum
DOWNLOADED_SHA=$(sha256sum "$TMP" | awk '{print $1}')
if [ "$DOWNLOADED_SHA" != "$EXPECTED_SHA" ]; then
    echo "Checksum mismatch!"
    exit 1
fi

# Execute
python3 "$TMP"
```


## 🧠 Design Philosophy

EMInstaller is built on these core principles:

- **Minimal** - Only essential functionality
- **Transparent** - Clear and understandable code
- **Auditable** - Easy to review and verify
- **Deterministic** - Consistent, predictable behavior
- **Secure by Default** - Security-first approach

> If an install script cannot be easily read and understood, it should not be trusted.

## ⚠️ Important Notice

Running scripts via piping to bash carries inherent security risks:

```bash
curl | bash
```

**Only execute installers from trusted, verified sources.**

Review the script before execution whenever possible. Use the safe method for production deployments.

## 🤝 Contributing

Contributions are welcome! Please ensure any changes:

- Maintain security best practices
- Include comprehensive error handling
- Follow the existing code style
- Document all changes

## 📄 License

EMInstaller is provided as-is for Arch Linux installation purposes.

## 🆘 Support

For issues, questions, or documentation clarifications:

1. Check the [online documentation](https://imemix.github.io/documentation.html)
2. Review the [FAQ section](#faq) below
3. Open an issue on GitHub

## ❓ FAQ

**Q: Is it safe to pipe the script directly to bash?**
A: While we implement security best practices, the recommended safe method is to download and inspect first. See [Safe Method](https://imemix.github.io/documentation.html#safe-method).

**Q: What if the download fails?**
A: The script uses `set -euo pipefail`, which will exit on any error. Check your internet connection and try again.

**Q: Can I use this on distributions other than Arch?**
A: EMInstaller is designed for Arch Linux. Compatibility with derivatives is not guaranteed.

**Q: How do I verify the checksum?**
A: The script automatically verifies checksums. Manual verification details are in the [documentation](https://imemix.github.io/documentation.html#security).

**Q: Can I run the installer offline?**
A: No, EMInstaller requires internet connectivity to download dependencies and the main payload.

---

**Made with ❤️ for the Arch Linux community**

For more information, visit: [EMInstaller Documentation](https://imemix.github.io/documentation.html)
