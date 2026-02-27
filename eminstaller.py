#!/usr/bin/env python3
import getpass
import os
import re
import shutil
import subprocess
import sys
from rich.console import Console

console = Console()

VALID_FILESYSTEMS = {"ext4", "btrfs", "xfs"}
VALID_KERNELS = {"linux", "linux-lts", "linux-zen"}
VALID_DESKTOPS = {"cli-only", "gnome", "kde", "hyprland", "xfce", "i3"}
VALID_GPUS = {"none", "nvidia", "amd", "intel"}
VALID_VM = {"none", "qemu", "vmware", "virtualbox", "hyper-v"}
RE_USERNAME = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")
RE_HOSTNAME = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9-]{0,62}$")


def banner(text="EMInstaller v1.1"):
    ascii_art = f"""
[cyan]
███████╗███╗   ███╗██╗███╗   ██╗
██╔════╝████╗ ████║██║████╗  ██║
█████╗  ██╔████╔██║██║██╔██╗ ██║
██╔══╝  ██║╚██╔╝██║██║██║╚██╗██║
███████╗██║ ╚═╝ ██║██║██║ ╚████║
╚══════╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝
[/cyan]
[magenta]{text}[/magenta]
"""
    console.print(ascii_art)


def run_command(cmd, description="", timeout=600, input_text=None):
    if description:
        console.print(f"[cyan]{description}[/cyan]")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            input=input_text,
            check=False,
        )
    except subprocess.TimeoutExpired:
        console.print("[red]Command timed out[/red]")
        return False, "", "Timeout"
    except Exception as exc:
        return False, "", str(exc)
    return result.returncode == 0, result.stdout, result.stderr


def run_stage(stage_name, cmd, timeout=600, input_text=None):
    console.print(f"\n[bold yellow]==> {stage_name}[/bold yellow]")
    success, stdout, stderr = run_command(cmd, timeout=timeout, input_text=input_text)
    if not success:
        error_msg = (stderr or stdout or "Unknown error").strip()
        console.print(f"[red]Failed: {stage_name}[/red]")
        console.print(f"[red]{error_msg[:400]}[/red]")
        raise RuntimeError(f"{stage_name} failed")
    console.print(f"[green]{stage_name} completed[/green]")


def require_root():
    if os.geteuid() != 0:
        console.print("[red]This installer must be run as root.[/red]")
        sys.exit(1)


def require_tools():
    required = [
        "lsblk",
        "wipefs",
        "parted",
        "mkfs.fat",
        "mount",
        "pacstrap",
        "genfstab",
        "arch-chroot",
        "grub-install",
        "grub-mkconfig",
    ]
    missing = [tool for tool in required if shutil.which(tool) is None]
    if missing:
        console.print(f"[red]Missing required tools: {', '.join(missing)}[/red]")
        sys.exit(1)


def detect_gpu():
    try:
        result = subprocess.run(["lspci"], capture_output=True, text=True, timeout=5, check=False)
        output = result.stdout.lower()
        if "nvidia" in output:
            return "nvidia"
        if "amd" in output:
            return "amd"
        if "intel" in output:
            return "intel"
    except Exception:
        pass
    return "none"


def get_available_disks():
    try:
        result = subprocess.run(
            ["lsblk", "-d", "-n", "-o", "NAME,SIZE,TYPE"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return []

    disks = []
    for line in result.stdout.strip().splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[2].lower() == "disk":
            disk_name, disk_size = parts[0], parts[1]
            path = f"/dev/{disk_name}"
            if os.path.exists(path):
                disks.append((path, disk_size))
    return disks


def display_disks():
    disks = get_available_disks()
    if not disks:
        console.print("[yellow]No disks found[/yellow]")
        return None
    console.print("[bold yellow]Available Disks:[/bold yellow]\n")
    for i, (disk, size) in enumerate(disks, 1):
        console.print(f"  {i}. {disk} ({size})")
    console.print()
    return disks


def get_input_interactive(prompt_text, default=""):
    prompt = f"  {prompt_text}" + (f" ({default})" if default else "") + ": "
    try:
        with open("/dev/tty", "r", encoding="utf-8") as tty:
            sys.stdout.write(prompt)
            sys.stdout.flush()
            user_input = tty.readline().strip()
            return user_input if user_input else default
    except Exception:
        console.print(prompt, end="")
        user_input = input().strip()
        return user_input if user_input else default


def get_password_interactive(prompt_text):
    try:
        with open("/dev/tty", "w", encoding="utf-8") as tty_out:
            tty_out.write(f"  {prompt_text}: ")
            tty_out.flush()
            return getpass.getpass("")
    except Exception:
        console.print(f"  {prompt_text}: ", end="")
        return getpass.getpass("")


def confirm_interactive(prompt_text, default=False):
    default_str = "Y/n" if default else "y/N"
    prompt = f"  {prompt_text} [{default_str}]: "
    try:
        with open("/dev/tty", "r", encoding="utf-8") as tty:
            sys.stdout.write(prompt)
            sys.stdout.flush()
            response = tty.readline().strip().lower()
    except Exception:
        console.print(prompt, end="")
        response = input().strip().lower()

    if response in {"y", "yes"}:
        return True
    if response in {"n", "no"}:
        return False
    return default


def get_disk_selection():
    disks = display_disks()
    if not disks:
        console.print("[red]Error: No disks available[/red]")
        sys.exit(1)
    while True:
        choice = get_input_interactive("Select disk number", "1")
        try:
            idx = int(choice)
        except ValueError:
            console.print("[red]Invalid input. Enter a number.[/red]")
            continue
        if 1 <= idx <= len(disks):
            selected_disk = disks[idx - 1][0]
            console.print(f"[green]Selected: {selected_disk}[/green]\n")
            return selected_disk
        console.print(f"[red]Invalid choice. Select 1-{len(disks)}[/red]")


def get_choice(prompt, valid_options, default):
    valid_text = "/".join(sorted(valid_options))
    while True:
        value = get_input_interactive(f"{prompt} ({valid_text})", default).strip().lower()
        if value in valid_options:
            return value
        console.print(f"[red]Invalid value: {value}[/red]")


def validate_identity(hostname, username):
    if not RE_HOSTNAME.fullmatch(hostname):
        raise ValueError("Hostname must be 1-63 chars: letters, digits, hyphen")
    if not RE_USERNAME.fullmatch(username):
        raise ValueError("Username must match Linux user naming rules")


def filesystem_mkfs_cmd(fs, root_part):
    if fs == "ext4":
        return ["mkfs.ext4", "-F", "-L", "arch", root_part]
    if fs == "btrfs":
        return ["mkfs.btrfs", "-f", "-L", "arch", root_part]
    if fs == "xfs":
        return ["mkfs.xfs", "-f", "-L", "arch", root_part]
    raise ValueError(f"Unsupported filesystem: {fs}")


def build_packages(kernel, desktop, gaming, dev_tools):
    packages = ["base", "linux-firmware", "grub", "efibootmgr", kernel, "networkmanager", "vim", "sudo"]
    if desktop != "cli-only":
        packages.append("xorg")
        if desktop == "gnome":
            packages.extend(["gnome", "gnome-extra", "gdm", "network-manager-applet"])
        elif desktop == "kde":
            packages.extend(["plasma", "sddm"])
        elif desktop == "hyprland":
            packages.extend(["hyprland", "hyprpaper", "waybar", "greetd", "greetd-tuigreet", "kitty", "wofi", "dolphin"])
        elif desktop == "xfce":
            packages.extend(["xfce4", "xfce4-goodies", "lightdm", "lightdm-gtk-greeter", "network-manager-applet"])
        elif desktop == "i3":
            packages.extend(["i3-wm", "i3status", "dmenu", "lightdm", "lightdm-gtk-greeter", "network-manager-applet"])
    if gaming:
        packages.extend(["steam", "wine", "lutris"])
    if dev_tools:
        packages.extend(["git", "base-devel", "npm", "python"])
    return list(dict.fromkeys(packages))


def write_text(path, content, mode="w"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, mode, encoding="utf-8") as f:
        f.write(content)


def main():
    require_root()
    require_tools()

    banner()
    console.print("\n[bold cyan]EMInstaller - Interactive Setup[/bold cyan]")
    console.print("[cyan]Configure your Arch Linux installation.\n[/cyan]")

    console.print("[bold yellow]=== Disk Selection ===[/bold yellow]\n")
    disk = get_disk_selection()

    console.print("[bold yellow]=== Basic Configuration ===[/bold yellow]\n")
    hostname = get_input_interactive("Hostname", "arch")
    username = get_input_interactive("Username", "user")
    userpass = get_password_interactive("User Password")
    rootpass = get_password_interactive("Root Password")
    validate_identity(hostname, username)

    console.print("\n[bold yellow]=== System Configuration ===[/bold yellow]\n")
    fs = get_choice("Filesystem", VALID_FILESYSTEMS, "ext4")
    use_luks = confirm_interactive("Enable LUKS Encryption?", False)
    create_swap = confirm_interactive("Create Swapfile?", True)
    kernel = get_choice("Kernel", VALID_KERNELS, "linux")

    console.print("\n[bold yellow]=== Desktop Environment ===[/bold yellow]\n")
    desktop = get_choice("Desktop Environment", VALID_DESKTOPS, "gnome")

    console.print("\n[bold yellow]=== Optional Features ===[/bold yellow]\n")
    gaming = confirm_interactive("Install Gaming Stack (Steam, Wine, Lutris)?", False)
    dev_tools = confirm_interactive("Install Development Tools (Git, Node, Python)?", False)
    dotfiles = confirm_interactive("Install Dotfiles?", False)

    detected_gpu = detect_gpu()
    console.print("\n[bold yellow]=== GPU/Virtualization ===[/bold yellow]\n")
    gpu = get_choice("GPU Driver", VALID_GPUS, detected_gpu)
    vm_graphics = get_choice("VM Graphics", VALID_VM, "none")

    console.print("\n[bold yellow]=== Installation Configuration ===[/bold yellow]\n")
    console.print(f"  [cyan]Disk:[/cyan] {disk}")
    console.print(f"  [cyan]Hostname:[/cyan] {hostname}")
    console.print(f"  [cyan]Username:[/cyan] {username}")
    console.print(f"  [cyan]Filesystem:[/cyan] {fs}")
    console.print(f"  [cyan]LUKS Encryption:[/cyan] {use_luks}")
    console.print(f"  [cyan]Swapfile:[/cyan] {create_swap}")
    console.print(f"  [cyan]Kernel:[/cyan] {kernel}")
    console.print(f"  [cyan]Desktop:[/cyan] {desktop}")
    console.print(f"  [cyan]GPU Driver:[/cyan] {gpu}")
    console.print(f"  [cyan]VM Graphics:[/cyan] {vm_graphics}")
    console.print(f"  [cyan]Gaming Stack:[/cyan] {gaming}")
    console.print(f"  [cyan]Dev Tools:[/cyan] {dev_tools}")
    console.print(f"  [cyan]Dotfiles:[/cyan] {dotfiles}\n")

    if use_luks:
        console.print("[yellow]LUKS selected, but LUKS setup is not implemented yet.[/yellow]")
        if not confirm_interactive("Continue without LUKS?", False):
            sys.exit(0)

    if not confirm_interactive(f"WARNING: This will erase ALL data on {disk}. Proceed?", False):
        console.print("[yellow]Installation cancelled.[/yellow]")
        sys.exit(0)

    console.print("\n[bold green]Starting installation to disk...[/bold green]\n")

    if "nvme" in disk:
        efi_part = f"{disk}p1"
        root_part = f"{disk}p2"
    else:
        efi_part = f"{disk}1"
        root_part = f"{disk}2"

    try:
        run_stage("Wiping disk", ["wipefs", "-af", disk])
        run_stage("Creating GPT partition table", ["parted", "-s", disk, "mklabel", "gpt"])
        run_stage("Creating EFI partition", ["parted", "-s", disk, "mkpart", "primary", "fat32", "1MiB", "513MiB"])
        run_stage("Setting EFI boot flag", ["parted", "-s", disk, "set", "1", "esp", "on"])
        run_stage("Creating root partition", ["parted", "-s", disk, "mkpart", "primary", fs, "513MiB", "100%"])

        run_stage("Formatting EFI partition", ["mkfs.fat", "-F32", "-n", "EFI", efi_part])
        run_stage(f"Formatting root partition ({fs})", filesystem_mkfs_cmd(fs, root_part))

        run_stage("Mounting root partition", ["mount", root_part, "/mnt"])
        run_stage("Creating mount directories", ["mkdir", "-p", "/mnt/boot/efi"])
        run_stage("Mounting EFI partition", ["mount", efi_part, "/mnt/boot/efi"])

        if create_swap:
            run_stage("Creating swapfile", ["arch-chroot", "/mnt", "bash", "-lc", "dd if=/dev/zero of=/swapfile bs=1M count=2048"])
            run_stage("Securing swapfile", ["arch-chroot", "/mnt", "chmod", "600", "/swapfile"])
            run_stage("Formatting swapfile", ["arch-chroot", "/mnt", "mkswap", "/swapfile"])
            fstab_swap = "/swapfile none swap defaults 0 0\n"
            write_text("/mnt/etc/fstab", fstab_swap, mode="a")

        packages = build_packages(kernel, desktop, gaming, dev_tools)
        run_stage("Installing base packages", ["pacstrap", "/mnt", *packages], timeout=1800)

        success, fstab_out, fstab_err = run_command(["genfstab", "-U", "/mnt"])
        if not success:
            raise RuntimeError(f"genfstab failed: {fstab_err}")
        write_text("/mnt/etc/fstab", fstab_out, mode="a")
        console.print("[green]Generated fstab[/green]")

        run_stage("Setting timezone", ["arch-chroot", "/mnt", "ln", "-sf", "/usr/share/zoneinfo/UTC", "/etc/localtime"])
        write_text("/mnt/etc/locale.gen", "en_US.UTF-8 UTF-8\n")
        run_stage("Generating locale", ["arch-chroot", "/mnt", "locale-gen"])
        write_text("/mnt/etc/locale.conf", "LANG=en_US.UTF-8\n")
        write_text("/mnt/etc/hostname", f"{hostname}\n")
        write_text(
            "/mnt/etc/hosts",
            "127.0.0.1 localhost\n::1 localhost\n"
            f"127.0.1.1 {hostname}.localdomain {hostname}\n",
        )

        run_stage("Setting root password", ["arch-chroot", "/mnt", "chpasswd"], input_text=f"root:{rootpass}\n")
        run_stage("Creating user", ["arch-chroot", "/mnt", "useradd", "-m", "-s", "/bin/bash", username])
        run_stage("Setting user password", ["arch-chroot", "/mnt", "chpasswd"], input_text=f"{username}:{userpass}\n")

        run_stage("Configuring sudoers", ["arch-chroot", "/mnt", "bash", "-lc", f"echo '{username} ALL=(ALL) ALL' > /etc/sudoers.d/{username}"])
        run_stage("Fixing sudoers permissions", ["arch-chroot", "/mnt", "chmod", "0440", f"/etc/sudoers.d/{username}"])
        run_stage("Enabling NetworkManager", ["arch-chroot", "/mnt", "systemctl", "enable", "NetworkManager"])

        if desktop == "gnome":
            run_stage("Enabling GDM", ["arch-chroot", "/mnt", "systemctl", "enable", "gdm"])
        elif desktop == "kde":
            run_stage("Enabling SDDM", ["arch-chroot", "/mnt", "systemctl", "enable", "sddm"])
        elif desktop == "hyprland":
            run_stage("Enabling greetd", ["arch-chroot", "/mnt", "systemctl", "enable", "greetd"])
        elif desktop in {"xfce", "i3"}:
            run_stage("Enabling LightDM", ["arch-chroot", "/mnt", "systemctl", "enable", "lightdm"])

        run_stage(
            "Installing GRUB",
            ["arch-chroot", "/mnt", "grub-install", "--target=x86_64-efi", "--efi-directory=/boot/efi", "--bootloader-id=GRUB"],
        )
        run_stage("Generating GRUB config", ["arch-chroot", "/mnt", "grub-mkconfig", "-o", "/boot/grub/grub.cfg"])

        if gpu == "nvidia":
            run_stage("Installing NVIDIA drivers", ["arch-chroot", "/mnt", "pacman", "-S", "--noconfirm", "nvidia", "nvidia-utils"])
        elif gpu == "amd":
            run_stage("Installing AMD drivers", ["arch-chroot", "/mnt", "pacman", "-S", "--noconfirm", "xf86-video-amdgpu"])
        elif gpu == "intel":
            run_stage("Installing Intel drivers", ["arch-chroot", "/mnt", "pacman", "-S", "--noconfirm", "xf86-video-intel"])

        if vm_graphics == "qemu":
            run_stage("Installing QEMU graphics drivers", ["arch-chroot", "/mnt", "pacman", "-S", "--noconfirm", "xf86-video-qxl", "spice-vdagent"])
        elif vm_graphics == "vmware":
            run_stage("Installing VMware graphics drivers", ["arch-chroot", "/mnt", "pacman", "-S", "--noconfirm", "xf86-video-vmware", "open-vm-tools"])
        elif vm_graphics == "virtualbox":
            run_stage("Installing VirtualBox guest tools", ["arch-chroot", "/mnt", "pacman", "-S", "--noconfirm", "virtualbox-guest-utils"])
        elif vm_graphics == "hyper-v":
            run_stage("Installing Hyper-V graphics drivers", ["arch-chroot", "/mnt", "pacman", "-S", "--noconfirm", "xf86-video-fbdev"])

        run_stage("Unmounting partitions", ["umount", "-R", "/mnt"])
    except Exception as exc:
        console.print(f"\n[red]Installation failed: {exc}[/red]")
        run_command(["umount", "-R", "/mnt"])
        sys.exit(1)

    console.print()
    banner("INSTALLATION COMPLETE")
    console.print(f"[bold green]Arch Linux has been successfully installed on {disk}![/bold green]\n")
    console.print("[bold cyan]Next Steps:[/bold cyan]")
    console.print("  1. Eject the Arch Linux ISO")
    console.print("  2. Reboot your system: reboot")
    console.print(f"  3. Boot from {disk}")
    console.print(f"  4. Login with username: [green]{username}[/green]")


if __name__ == "__main__":
    main()
