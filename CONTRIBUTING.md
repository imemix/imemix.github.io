# Contributing to EMInstaller & imemix.github.io

```
	____  __  __ ___ _  _ 
 |  _ \|  \/  |_ _| \| |
 | | | | |\/| || || .` |
 |_| |_|_|  |_|___|_|\_|
 EMInstaller — Arch Linux Terminal Installer
```

Thank you for your interest in contributing.

This repository (`https://github.com/imemix/imemix.github.io`) serves two primary purposes:

1\. It hosts the **EMInstaller** Arch Linux installation script (`eminstaller.py`).\
2\. It powers the **GitHub Pages website and documentation** for the project.


Contributions may involve installer logic, documentation, website content, or security improvements. Because this project performs destructive system operations, changes must prioritize safety, clarity, and correctness.

---

# ⚠️ Safety First


EMInstaller performs:

- Disk wiping via `wipefs`\
- GPT partition creation via `parted`\
- Filesystem formatting\
- Base system installation via `pacstrap`\
- System configuration inside `arch-chroot`\
- Password configuration\
- Bootloader installation (GRUB)\
- GPU driver installation\
- Service enablement

Mistakes can result in:

- Data loss\
- Unbootable systems\
- Broken sudo access\
- Incorrect locale configuration\
- Security regressions

All code contributions must assume the script will be executed on real hardware.

Test thoroughly.

---

# 🧠 Project Philosophy

EMInstaller aims to:

- Provide a fully interactive Arch Linux installation experience\
- Keep logic readable and approachable\
- Avoid unnecessary abstraction\
- Remain dependency-light\
- Preserve clarity over cleverness

This is an installer, not a framework. Improvements should respect that.

---

# 📌 Repository Scope

This repository contains:

- `eminstaller.py` (installer logic)\
- GitHub Pages website content (HTML, Markdown)\
- Documentation files\
- `SECURITY.md`\
- `CODE_OF_CONDUCT.md`

Contributions may target:

- Installer behavior\
- Documentation clarity\
- Security hardening\
- User experience improvements

---

# 🚀 Getting Started

1\. Fork the repository.\
2\. Clone your fork locally.

```bash\
git clone https://github.com/imemix/imemix.github.io\
cd imemix.github.io
```
1.  Create a feature branch.

```bash
git checkout -b feature/your-change
```
1.  Make your changes.

2.  Test thoroughly.

3.  Submit a pull request.

* * * * *

🧪 Testing Requirements (Installer Changes)
===========================================

If modifying `eminstaller.py`, you must test inside:

-   QEMU/KVM

-   VirtualBox

-   VMware

-   Or other disposable environments

Never test destructive changes on production hardware.

If you modify:

Partition Logic
---------------

-   Test NVMe (`nvme0n1p1`) devices

-   Test SATA (`sda1`) devices

-   Confirm correct partition naming

Bootloader Logic
----------------

-   Confirm system boots successfully

User Creation / Sudo Logic
--------------------------

-   Verify login works

-   Verify sudo works

GPU Logic
---------

-   Verify detection fallback

-   Verify selected driver installs properly

Desktop Selection
-----------------

-   Test at least one desktop option

-   Test `cli-only` mode

Your pull request must describe:

-   Environment used

-   What was tested

-   What scenario was verified

* * * * *

🛠 Code Style Guidelines
========================

Keep It Clear
-------------

The installer is structured in three main phases:

1.  Helper functions

2.  Interactive configuration

3.  Execution stages

Avoid:

-   Deep nesting

-   Over-abstraction

-   Unnecessary class hierarchies

-   Major architectural rewrites without discussion

Clarity is more important than cleverness.

* * * * *

Console Output
--------------

The script uses `rich` for:

-   Styled console output

-   Progress bars

-   Status messages

Maintain visual consistency.

Warnings must remain clearly visible.

Do not clutter output unnecessarily.

* * * * *

🔒 Security Guidelines
======================

Be extremely cautious when modifying:

-   Password handling

-   `sudoers` configuration

-   Any use of `shell=True`

-   Command construction using user input

Never introduce:

-   Hardcoded credentials

-   Logged passwords

-   Insecure temp files

-   Silent failure behavior

-   Weak privilege handling

Security regressions will not be merged.

If you discover a vulnerability, follow responsible disclosure as described in `SECURITY.md`.

* * * * *

📦 Package Management Guidelines
================================

When modifying install packages:

-   Keep base install minimal

-   Avoid opinionated additions

-   Ensure packages exist in official Arch repositories

-   Do not introduce AUR dependencies into base installation

Optional stacks (gaming, dev tools, etc.) must remain conditional.

* * * * *

🌐 Website & Documentation Contributions
========================================

This repository also powers the GitHub Pages site.

Documentation contributions are highly encouraged:

-   Clarify install instructions

-   Improve navigation

-   Fix grammar or formatting

-   Add screenshots or usage examples

-   Improve structure and readability

Documentation should reflect actual installer behavior.

Never document functionality that does not exist.

* * * * *

🧱 Disk Logic Rules
===================

Partitioning logic must:

-   Handle NVMe naming correctly

-   Handle SATA naming correctly

-   Preserve EFI partition creation

-   Avoid assumptions about existing state

Disk logic changes must be tested thoroughly before submission.

* * * * *

📝 Commit Message Guidelines
============================

Use descriptive commit messages.

Examples:

feat: add validation for filesystem selection\
fix: correct NVMe partition naming logic\
refactor: simplify GPU detection\
docs: improve installation walkthrough

Avoid vague messages like:

update\
fix stuff\
changes

Clear history matters.

* * * * *

🔄 Pull Request Guidelines
==========================

Each pull request should include:

-   Clear summary of changes

-   Reason for change

-   Testing description

-   Screenshots (if UI-related)

-   Linked issue (if applicable)

Keep PRs focused. One logical change per PR.

Large architectural proposals must be discussed in an issue first.

* * * * *

❌ What Will Not Be Accepted
===========================

-   Untested partition logic changes

-   Untested bootloader changes

-   Hardcoded values

-   Major structural rewrites without discussion

-   Security regressions

-   Opinionated distro-level changes without consensus

* * * * *

🤝 Code of Conduct
==================

Please follow the `CODE_OF_CONDUCT.md`.

Be respectful and constructive.

This project operates at system level. Mistakes happen. Collaboration improves outcomes.

* * * * *

🧠 Final Note
=============

An installer script is not just code.

It is a trust contract between the maintainer and the user.

Every contribution should assume someone's only machine may depend on it.

Contribute carefully.\
---
