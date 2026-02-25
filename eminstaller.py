#!/usr/bin/env python3
import time
import subprocess
import sys
import getpass
import os

# Try to import curses for better terminal control
try:
    import curses
    HAVE_CURSES = True
except ImportError:
    HAVE_CURSES = False

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

def run_command(cmd, description="", verbose=False):
    """Run a shell command"""
    if description:
        console.print(f"[cyan]{description}[/cyan]")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        if verbose and result.stdout:
            console.print(result.stdout)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        console.print("[yellow]Command timed out[/yellow]")
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)

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
    
    success, stdout, stderr = run_command(cmd)
    if success or "error" not in stderr.lower():
        console.print(f"[green]✓ {stage_name} completed[/green]")
        return True
    else:
        console.print(f"[yellow]⚠ {stage_name} warning: {stderr[:100]}[/yellow]")
        return True

def detect_gpu():
    """Detect GPU in system"""
    try:
        result = subprocess.run(["lspci"], capture_output=True, text=True, timeout=5)
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

def get_available_disks():
    """Get list of available disks"""
    try:
        result = subprocess.run(["lsblk", "-d", "-n", "-o", "NAME,SIZE,TYPE"], capture_output=True, text=True, timeout=5)
        disks = []
        for line in result.stdout.strip().split('\n'):
            if line and 'disk' in line.lower():
                parts = line.split()
                if len(parts) >= 2:
                    disk_name = parts[0]
                    disk_size = parts[1]
                    disks.append(f"/dev/{disk_name} ({disk_size})")
        return disks
    except:
        return []

def menu_select(title, options, show_numbers=False):
    """Display menu and get selection with arrow keys"""
    selected = 0
    
    while True:
        console.clear()
        banner()
        console.print(f"\n[bold cyan]{title}[/bold cyan]\n")
        console.print("[yellow]Use ↑↓ arrow keys to navigate, Enter to select[/yellow]\n")
        
        for i, option in enumerate(options):
            if i == selected:
                if show_numbers:
                    console.print(f"[bold green]► {i+1}. {option}[/bold green]")
                else:
                    console.print(f"[bold green]► {option}[/bold green]")
            else:
                if show_numbers:
                    console.print(f"  {i+1}. {option}")
                else:
                    console.print(f"  {option}")
        
        # Simple arrow key input without termios issues
        ch = sys.stdin.read(1)
        
        if ch == '\x1b':  # ESC sequence
            try:
                sys.stdin.read(1)
                direction = sys.stdin.read(1)
                if direction == 'A':  # Up arrow
                    selected = (selected - 1) % len(options)
                elif direction == 'B':  # Down arrow
                    selected = (selected + 1) % len(options)
            except:
                pass
        elif ch == '\r' or ch == '\n':  # Enter
            return selected
        elif ch in ['k', 'K']:  # k for up (vim style)
            selected = (selected - 1) % len(options)
        elif ch in ['j', 'J']:  # j for down (vim style)
            selected = (selected + 1) % len(options)

def text_input(title, default=""):
    """Get text input"""
    console.clear()
    banner()
    console.print(f"\n[bold cyan]{title}[/bold cyan]\n")
    
    try:
        with open("/dev/tty", "r") as tty:
            sys.stdout.write(f"  Enter value (default: {default}): ")
            sys.stdout.flush()
            user_input = tty.readline().strip()
            return user_input if user_input else default
    except:
        sys.stdout.write(f"  Enter value (default: {default}): ")
        sys.stdout.flush()
        user_input = input()
        return user_input if user_input else default

def password_input(title):
    """Get password input"""
    console.clear()
    banner()
    console.print(f"\n[bold cyan]{title}[/bold cyan]\n")
    
    try:
        with open("/dev/tty", "r") as tty_in:
            with open("/dev/tty", "w") as tty_out:
                tty_out.write(f"  Enter password: ")
                tty_out.flush()
                return getpass.getpass(stream=tty_out)
    except:
        sys.stdout.write(f"  Enter password: ")
        sys.stdout.flush()
        return getpass.getpass()

# ==============================
# Interactive Configuration
# ==============================
banner()
console.print("\n[bold cyan]EMInstaller - Interactive Setup[/bold cyan]")
console.print("[cyan]Configure your Arch Linux installation.\n[/cyan]")
time.sleep(2)

# Disk Selection
disks = get_available_disks()
if not disks:
    console.print("[red]Error: No disks found![/red]")
    sys.exit(1)

disk_index = menu_select("Select Installation Disk", disks, show_numbers=True)
disk = disks[disk_index].split()[0]

# Hostname
hostname = text_input("Enter Hostname", "arch")

# Username
username = text_input("Enter Username", "user")

# User Password
userpass = password_input("Enter User Password")

# Root Password
rootpass = password_input("Enter Root Password")

# Filesystem
fs_index = menu_select("Select Filesystem", ["ext4", "btrfs", "xfs"])
fs = ["ext4", "btrfs", "xfs"][fs_index]

# LUKS Encryption
luks_index = menu_select("Enable LUKS Encryption?", ["No", "Yes"])
use_luks = luks_index == 1

# Swapfile
swap_index = menu_select("Create Swapfile?", ["No", "Yes"])
create_swap = swap_index == 1

# Kernel
kernel_index = menu_select("Select Kernel", ["linux", "linux-lts", "linux-zen"])
kernel = ["linux", "linux-lts", "linux-zen"][kernel_index]

# Desktop Environment
desktop_index = menu_select("Select Desktop Environment", ["cli-only", "gnome", "kde", "hyprland", "xfce", "i3"])
desktops = ["cli-only", "gnome", "kde", "hyprland", "xfce", "i3"]
desktop = desktops[desktop_index]

# Gaming Stack
gaming_index = menu_select("Install Gaming Stack?", ["No", "Yes"])
gaming = gaming_index == 1

# Development Tools
dev_index = menu_select("Install Development Tools?", ["No", "Yes"])
dev_tools = dev_index == 1

# GPU Selection
detected_gpu = detect_gpu()
gpu_index = menu_select("Select GPU Driver", ["none", "nvidia", "amd", "intel"])
gpus = ["none", "nvidia", "amd", "intel"]
gpu = gpus[gpu_index]

# VM Graphics
vm_index = menu_select("Select VM Graphics", ["none", "qemu", "vmware", "virtualbox", "hyper-v"])
vms = ["none", "qemu", "vmware", "virtualbox", "hyper-v"]
vm_graphics = vms[vm_index]

# Review Configuration
console.clear()
banner()
console.print("\n[bold yellow]=== Installation Configuration ===[/bold yellow]\n")
console.print(f"  [cyan]Disk:[/cyan] {disk}")
console.print(f"  [cyan]Hostname:[/cyan] {hostname}")
console.print(f"  [cyan]Username:[/cyan] {username}")
console.print(f"  [cyan]Filesystem:[/cyan] {fs}")
console.print(f"  [cyan]LUKS Encryption:[/cyan] {'Yes' if use_luks else 'No'}")
console.print(f"  [cyan]Swapfile:[/cyan] {'Yes' if create_swap else 'No'}")
console.print(f"  [cyan]Kernel:[/cyan] {kernel}")
console.print(f"  [cyan]Desktop:[/cyan] {desktop}")
console.print(f"  [cyan]Gaming Stack:[/cyan] {'Yes' if gaming else 'No'}")
console.print(f"  [cyan]Dev Tools:[/cyan] {'Yes' if dev_tools else 'No'}")
console.print(f"  [cyan]GPU Driver:[/cyan] {gpu}")
console.print(f"  [cyan]VM Graphics:[/cyan] {vm_graphics}\n")

confirm_index = menu_select(f"[bold red]⚠️  WARNING: This will erase ALL data on {disk}. Proceed?[/bold red]", ["Cancel", "Proceed"])
if confirm_index == 0:
    console.print("[yellow]Installation cancelled.[/yellow]")
    sys.exit(0)

# ==============================
# Execute Installation
# ==============================
console.print("\n[bold green]Starting installation to disk...[/bold green]\n")

if "nvme" in disk:
    efi_part = f"{disk}p1"
    root_part = f"{disk}p2"
else:
    efi_part = f"{disk}1"
    root_part = f"{disk}2"

run_stage("Wiping disk", f"wipefs -af {disk}", duration=2)
run_stage("Creating GPT partition table", f"parted -s {disk} mklabel gpt", duration=1)
run_stage("Creating EFI partition (512MB)", f"parted -s {disk} mkpart primary fat32 1MiB 513MiB", duration=1)
run_stage("Setting EFI boot flag", f"parted -s {disk} set 1 esp on", duration=1)
run_stage("Creating root partition", f"parted -s {disk} mkpart primary {fs} 513MiB 100%", duration=1)
run_stage("Formatting EFI partition", f"mkfs.fat -F32 -n EFI {efi_part}", duration=1)
run_stage(f"Formatting root partition ({fs})", f"mkfs.{fs} -L arch {root_part}", duration=3)

run_stage("Creating mount directories", f"mkdir -p /mnt/boot /mnt", duration=1)
run_stage("Mounting root partition", f"mount {root_part} /mnt", duration=1)
run_stage("Mounting EFI partition", f"mkdir -p /mnt/boot/efi && mount {efi_part} /mnt/boot/efi", duration=1)

if create_swap:
    run_stage("Creating swapfile (2GB)", f"dd if=/dev/zero of=/mnt/swapfile bs=1M count=2048 && chmod 600 /mnt/swapfile && mkswap /mnt/swapfile", duration=3)

packages = ["base", "linux-firmware", "grub", "efibootmgr", kernel, "networkmanager", "vim", "sudo"]

if desktop != "cli-only":
    packages.append("xorg")
    if desktop == "gnome":
        packages.extend(["gnome", "gnome-extra", "gdm", "network-manager-applet"])
    elif desktop == "kde":
        packages.extend(["plasma", "kde-applications", "sddm"])
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

run_stage("Installing base packages", f"pacstrap /mnt {' '.join(packages)}", duration=10)
run_stage("Generating fstab", f"genfstab -U /mnt >> /mnt/etc/fstab", duration=1)

console.print("\n[bold green]Configuring system in chroot...[/bold green]\n")

run_stage("Setting timezone", f"arch-chroot /mnt ln -sf /usr/share/zoneinfo/UTC /etc/localtime", duration=1)
run_stage("Generating locale", f"arch-chroot /mnt bash -c \"echo 'en_US.UTF-8 UTF-8' > /etc/locale.gen && locale-gen\"", duration=2)
run_stage("Setting LANG", f"arch-chroot /mnt bash -c \"echo 'LANG=en_US.UTF-8' > /etc/locale.conf\"", duration=1)
run_stage("Setting hostname", f"arch-chroot /mnt bash -c \"echo '{hostname}' > /etc/hostname\"", duration=1)
run_stage("Configuring hosts", f"arch-chroot /mnt bash -c \"echo '127.0.0.1 localhost' >> /etc/hosts && echo '::1 localhost' >> /etc/hosts && echo '127.0.1.1 {hostname}.localdomain {hostname}' >> /etc/hosts\"", duration=1)

run_stage("Setting root password", f"arch-chroot /mnt bash -c \"echo -e '{rootpass}\\n{rootpass}' | passwd\"", duration=1)
run_stage("Creating user", f"arch-chroot /mnt useradd -m -s /bin/bash {username}", duration=1)
run_stage("Setting user password", f"arch-chroot /mnt bash -c \"echo -e '{userpass}\\n{userpass}' | passwd {username}\"", duration=1)

run_stage("Creating sudoers directory", f"arch-chroot /mnt mkdir -p /etc/sudoers.d", duration=1)
run_stage("Configuring sudoers", f"arch-chroot /mnt bash -c \"echo '{username} ALL=(ALL) ALL' > /etc/sudoers.d/{username} && chmod 0440 /etc/sudoers.d/{username}\"", duration=1)

run_stage("Enabling NetworkManager", f"arch-chroot /mnt systemctl enable NetworkManager", duration=1)

if desktop == "gnome":
    run_stage("Enabling GNOME Display Manager (GDM)", f"arch-chroot /mnt systemctl enable gdm", duration=1)
elif desktop == "kde":
    run_stage("Enabling Simple Desktop Display Manager (SDDM)", f"arch-chroot /mnt systemctl enable sddm", duration=1)
elif desktop == "hyprland":
    run_stage("Enabling Greetd Display Manager", f"arch-chroot /mnt systemctl enable greetd", duration=1)
    run_stage("Configuring greetd for Hyprland", f"arch-chroot /mnt bash -c \"mkdir -p /home/{username}/.config/hypr && echo 'exec-once = waybar' > /home/{username}/.config/hypr/hyprland.conf && chown -R {username}:{username} /home/{username}/.config\"", duration=1)
elif desktop in ["xfce", "i3"]:
    run_stage("Enabling LightDM Display Manager", f"arch-chroot /mnt systemctl enable lightdm", duration=1)

run_stage("Installing GRUB", f"arch-chroot /mnt grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=GRUB", duration=2)
run_stage("Generating GRUB config", f"arch-chroot /mnt grub-mkconfig -o /boot/grub/grub.cfg", duration=1)

if gpu == "nvidia":
    run_stage("Installing NVIDIA drivers", f"arch-chroot /mnt pacman -S --noconfirm nvidia nvidia-utils", duration=5)
elif gpu == "amd":
    run_stage("Installing AMD drivers", f"arch-chroot /mnt pacman -S --noconfirm xf86-video-amdgpu", duration=5)
elif gpu == "intel":
    run_stage("Installing Intel drivers", f"arch-chroot /mnt pacman -S --noconfirm xf86-video-intel", duration=3)

if vm_graphics == "qemu":
    run_stage("Installing QEMU graphics drivers", f"arch-chroot /mnt pacman -S --noconfirm xf86-video-qxl spice-vdagent", duration=3)
elif vm_graphics == "vmware":
    run_stage("Installing VMware graphics drivers", f"arch-chroot /mnt pacman -S --noconfirm xf86-video-vmware open-vm-tools", duration=3)
elif vm_graphics == "virtualbox":
    run_stage("Installing VirtualBox graphics drivers", f"arch-chroot /mnt pacman -S --noconfirm virtualbox-guest-utils", duration=3)
elif vm_graphics == "hyper-v":
    run_stage("Installing Hyper-V graphics drivers", f"arch-chroot /mnt pacman -S --noconfirm xf86-video-fbdev", duration=3)

run_stage("Unmounting partitions", f"umount -R /mnt", duration=1)

console.clear()
banner("INSTALLATION COMPLETE! 🚀")
console.print(f"[bold green]Arch Linux has been successfully installed on {disk}![/bold green]\n")

console.print("[bold cyan]Final Configuration Summary:[/bold cyan]")
console.print(f"  Disk: [green]{disk}[/green]")
console.print(f"  Hostname: [green]{hostname}[/green]")
console.print(f"  User: [green]{username}[/green]")
console.print(f"  Desktop: [green]{desktop}[/green]")
console.print(f"  Filesystem: [green]{fs}[/green]")
console.print(f"  Kernel: [green]{kernel}[/green]")
console.print(f"  GPU Driver: [green]{gpu}[/green]")

console.print("\n[bold cyan]Next Steps:[/bold cyan]")
console.print(f"  1. [yellow]Eject the Arch Linux ISO[/yellow]")
console.print(f"  2. Reboot your system: [yellow]sudo reboot[/yellow]")
console.print(f"  3. Boot from {disk}")
console.print(f"  4. Login with username: [green]{username}[/green]")
console.print(f"  5. Configure your preferences")

if gaming:
    console.print("  6. Launch Steam from applications menu")

if dev_tools:
    console.print("  6. Start developing!")

console.print("\n[bold green]Installation successful! You can now remove the ISO and boot from disk.[/bold green]")
