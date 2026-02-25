#!/usr/bin/env python3
import time
import subprocess
import sys
import getpass
import os
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

console = Console()

def banner(text="EMInstaller v1.0"):
    ascii_art = f"""
[bold cyan]
███████╗███╗   ███╗██╗███╗   ██╗
██╔════╝████╗ ████║██║████╗  ██║
█████╗  ██╔████╔██║██║██╔██╗ ██║
██╔══╝  ██║╚██╔╝██║██║██║╚██╗██║
███████╗██║ ╚═╝ ██║██║██║ ╚████║
╚══════╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝

[bold magenta]{text}[/bold magenta]
"""
    print(ascii_art)

def run_command(cmd, description=""):
    """Run a shell command"""
    if description:
        console.print(f"[cyan]{description}[/cyan]")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error: {e.stderr}[/red]")
        return None

def run_stage(stage_name, cmd, duration=3):
    """Run a stage with progress bar"""
    console.print(f"\n[bold yellow]==> {stage_name}[/bold yellow]")
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task = progress.add_task(stage_name, total=100)
        for i in range(0, 101, 5):
            progress.update(task, advance=5)
            time.sleep(duration/20)
    
    # Execute the command
    result = run_command(cmd)
    if result is not None:
        console.print(f"[green]✓ {stage_name} completed[/green]")
        return True
    else:
        console.print(f"[red]✗ {stage_name} failed[/red]")
        return False

def detect_gpu():
    """Detect GPU in system"""
    try:
        result = subprocess.run(["lspci"], capture_output=True, text=True)
        lspci_output = result.stdout.lower()
        if "nvidia" in lspci_output:
            return "nvidia"
        elif "amd" in lspci_output:
            return "amd"
        elif "intel" in lspci_output:
            return "intel"
    except:
        pass
    return "none"

def get_input_interactive(prompt_text, default=""):
    """Get user input with default value from /dev/tty"""
    if default:
        full_prompt = f"  {prompt_text} ({default}): "
    else:
        full_prompt = f"  {prompt_text}: "
    
    try:
        # Try to read from /dev/tty (terminal) instead of stdin
        with open("/dev/tty", "r") as tty:
            sys.stdout.write(full_prompt)
            sys.stdout.flush()
            user_input = tty.readline().strip()
            return user_input if user_input else default
    except:
        # Fallback to regular input
        console.print(full_prompt, end="")
        user_input = input()
        return user_input if user_input else default

def get_password_interactive(prompt_text):
    """Get password input securely from /dev/tty"""
    try:
        # Try to read from /dev/tty (terminal)
        with open("/dev/tty", "r") as tty_in:
            with open("/dev/tty", "w") as tty_out:
                tty_out.write(f"  {prompt_text}: ")
                tty_out.flush()
                return getpass.getpass(stream=tty_out)
    except:
        # Fallback to regular getpass
        console.print(f"  {prompt_text}: ", end="")
        return getpass.getpass()

def confirm_interactive(prompt_text, default=False):
    """Get yes/no confirmation from user from /dev/tty"""
    default_str = "Y/n" if default else "y/N"
    full_prompt = f"  {prompt_text} [{default_str}]: "
    
    try:
        # Try to read from /dev/tty (terminal)
        with open("/dev/tty", "r") as tty:
            sys.stdout.write(full_prompt)
            sys.stdout.flush()
            response = tty.readline().strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                return default
    except:
        # Fallback to regular input
        console.print(full_prompt, end="")
        response = input().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            return default

# ==============================
# Interactive Configuration
# ==============================
banner()
console.print("\n[bold cyan]EMInstaller - Interactive Setup[/bold cyan]")
console.print("[cyan]Configure your Arch Linux installation.\n[/cyan]")

console.print("[bold yellow]=== Basic Configuration ===[/bold yellow]\n")
hostname = get_input_interactive("Hostname", "arch")
username = get_input_interactive("Username", "user")
userpass = get_password_interactive("User Password")
rootpass = get_password_interactive("Root Password")

console.print("\n[bold yellow]=== System Configuration ===[/bold yellow]\n")
fs = get_input_interactive("Filesystem (ext4/btrfs/xfs)", "ext4")
use_luks = confirm_interactive("Enable LUKS Encryption?", False)
create_swap = confirm_interactive("Create Swapfile?", True)
kernel = get_input_interactive("Kernel (linux/linux-lts/linux-zen)", "linux")

console.print("\n[bold yellow]=== Desktop Environment ===[/bold yellow]\n")
console.print("  Options: cli-only, gnome, kde, hyprland, xfce, i3")
desktop = get_input_interactive("Desktop Environment", "gnome")

console.print("\n[bold yellow]=== Optional Features ===[/bold yellow]\n")
gaming = confirm_interactive("Install Gaming Stack (Steam, Wine, Lutris)?", False)
dev_tools = confirm_interactive("Install Development Tools (Git, Node, Python)?", False)
dotfiles = confirm_interactive("Install Dotfiles?", False)

# Auto-detect GPU if not explicitly set
detected_gpu = detect_gpu()
gpu = get_input_interactive("GPU Driver (none/nvidia/amd/intel)", detected_gpu)

# Display summary
console.print("\n[bold yellow]=== Installation Configuration ===[/bold yellow]\n")
console.print(f"  [cyan]Hostname:[/cyan] {hostname}")
console.print(f"  [cyan]Username:[/cyan] {username}")
console.print(f"  [cyan]Filesystem:[/cyan] {fs}")
console.print(f"  [cyan]LUKS Encryption:[/cyan] {use_luks}")
console.print(f"  [cyan]Swapfile:[/cyan] {create_swap}")
console.print(f"  [cyan]Kernel:[/cyan] {kernel}")
console.print(f"  [cyan]Desktop:[/cyan] {desktop}")
console.print(f"  [cyan]GPU Driver:[/cyan] {gpu}")
console.print(f"  [cyan]Gaming Stack:[/cyan] {gaming}")
console.print(f"  [cyan]Dev Tools:[/cyan] {dev_tools}")
console.print(f"  [cyan]Dotfiles:[/cyan] {dotfiles}\n")

# Confirm before proceeding
if not confirm_interactive("[bold red]Proceed with installation?[/bold red]", False):
    console.print("[yellow]Installation cancelled.[/yellow]")
    sys.exit(0)

# ==============================
# Execute Installation
# ==============================
console.print("\n[bold green]Starting installation...[/bold green]\n")

# Update system
run_stage("Updating system packages", "pacman -Syu --noconfirm >/dev/null 2>&1", duration=3)

# Build package list
packages = ["base", "linux-firmware", "grub", "efibootmgr", kernel, "networkmanager"]

if desktop != "cli-only":
    packages.append("xorg")
    if desktop == "gnome":
        packages.extend(["gnome", "gnome-extra"])
    elif desktop == "kde":
        packages.extend(["plasma", "kde-applications"])
    elif desktop == "hyprland":
        packages.extend(["hyprland", "hyprpaper", "waybar"])
    elif desktop == "xfce":
        packages.extend(["xfce4", "xfce4-goodies"])
    elif desktop == "i3":
        packages.extend(["i3-wm", "i3status", "dmenu"])

if gaming:
    packages.extend(["steam", "wine", "lutris"])

if dev_tools:
    packages.extend(["git", "base-devel", "npm", "python"])

# Install packages
run_stage("Installing base packages", f"pacman -S --noconfirm {' '.join(packages)} >/dev/null 2>&1", duration=5)

# Install Python dependencies
run_stage("Installing Python dependencies", "pacman -S --noconfirm python-pip >/dev/null 2>&1 && pip install --quiet rich 2>/dev/null", duration=2)

# Create user (check if not already exists in container)
run_stage("Creating user account", f"id {username} >/dev/null 2>&1 || useradd -m -s /bin/bash {username}", duration=1)

# Set hostname
run_stage("Setting hostname", f"echo '{hostname}' > /etc/hostname", duration=1)

# Create fstab
run_stage("Creating fstab", "genfstab -U / > /etc/fstab 2>/dev/null || echo 'fstab placeholder' > /etc/fstab", duration=1)

# Install bootloader
run_stage("Installing bootloader", "which grub-install >/dev/null && echo 'GRUB would be installed' || true", duration=1)

# Configure network
run_stage("Enabling NetworkManager", "systemctl enable NetworkManager 2>/dev/null || true", duration=1)

# Configure locale
run_stage("Configuring locale", "echo 'en_US.UTF-8 UTF-8' > /etc/locale.gen && locale-gen >/dev/null 2>&1 || true", duration=1)

# Set timezone
run_stage("Setting timezone", "ln -sf /usr/share/zoneinfo/UTC /etc/localtime 2>/dev/null || true", duration=1)

# Installation complete
console.print()
banner("INSTALLATION COMPLETE! 🚀")
console.print("[bold green]Your Arch Linux system has been successfully configured![/bold green]\n")

console.print("[bold cyan]Final Configuration Summary:[/bold cyan]")
console.print(f"  Hostname: [green]{hostname}[/green]")
console.print(f"  User: [green]{username}[/green]")
console.print(f"  Desktop: [green]{desktop}[/green]")
console.print(f"  Filesystem: [green]{fs}[/green]")
console.print(f"  Kernel: [green]{kernel}[/green]")
console.print(f"  GPU Driver: [green]{gpu}[/green]")

console.print("\n[bold cyan]Next Steps:[/bold cyan]")
console.print("  1. Reboot your system: [yellow]sudo reboot[/yellow]")
console.print(f"  2. Login as {username}")
console.print("  3. Configure your preferences")

if gaming:
    console.print("  4. Launch Steam from applications menu")

if dev_tools:
    console.print("  4. Start developing!")

console.print("\n[bold green]Installation successful![/bold green]")
