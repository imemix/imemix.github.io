#!/usr/bin/env python3
import argparse
import time
import subprocess
import sys
import getpass
import os
import re
import shutil
import shlex
from rich.console import Console
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    SpinnerColumn,
)

# make sure we're running on linux as this script relies on /dev/tty, lsblk, parted, etc.
def check_platform():
    if not sys.platform.startswith("linux"):
        console.print("[red]Error: this installer must be run on Linux.[/red]")
        sys.exit(1)

# --- curses based GUI helpers ------------------------------------------------
try:
    import curses
except ImportError:
    curses = None


CURSES_COLORS_READY = False
COLOR_TITLE = 1
COLOR_HIGHLIGHT = 2
COLOR_HELP = 3
COLOR_LABEL = 4


def _curses_init_colors():
    """Initialize curses color pairs when terminal supports colors."""
    global CURSES_COLORS_READY
    if curses is None:
        CURSES_COLORS_READY = False
        return

    try:
        if not curses.has_colors():
            CURSES_COLORS_READY = False
            return
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(COLOR_TITLE, curses.COLOR_CYAN, -1)
        curses.init_pair(COLOR_HIGHLIGHT, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(COLOR_HELP, curses.COLOR_MAGENTA, -1)
        curses.init_pair(COLOR_LABEL, curses.COLOR_YELLOW, -1)
        CURSES_COLORS_READY = True
    except curses.error:
        CURSES_COLORS_READY = False


def _open_tty_streams():
    """Return streams bound to /dev/tty when available for interactive prompts."""
    tty_in = None
    tty_out = None
    try:
        tty_in = open("/dev/tty", "r", encoding="utf-8", errors="ignore")
    except OSError:
        tty_in = sys.stdin

    try:
        tty_out = open("/dev/tty", "w", encoding="utf-8", errors="ignore")
    except OSError:
        tty_out = sys.stdout

    return tty_in, tty_out


def prompt_input(prompt):
    """Read user input from /dev/tty (or fallback stdin) to avoid pipe EOF issues."""
    tty_in, tty_out = _open_tty_streams()
    tty_out.write(prompt)
    tty_out.flush()
    line = tty_in.readline()
    if line == "":
        raise EOFError("No interactive input available. Run from a real terminal or use --yes where possible.")
    return line.rstrip("\n")


def prompt_password(prompt):
    """Read password from /dev/tty (or fallback) without echo."""
    _, tty_out = _open_tty_streams()
    return getpass.getpass(prompt, stream=tty_out)


def curses_menu(stdscr, title, options):
    """Display a vertical menu and allow arrow-key movement."""
    curses.curs_set(0)  # Hide cursor
    stdscr.keypad(True)
    stdscr.nodelay(False)
    current = 0
    stdscr.timeout(100)  # 100ms timeout - allows smooth input capture
    
    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        
        # Title
        try:
            if CURSES_COLORS_READY:
                stdscr.attron(curses.color_pair(COLOR_TITLE))
            stdscr.attron(curses.A_BOLD)
            stdscr.addstr(1, 2, title)
            stdscr.attroff(curses.A_BOLD)
            if CURSES_COLORS_READY:
                stdscr.attroff(curses.color_pair(COLOR_TITLE))
        except curses.error:
            pass
        
        # Options
        for idx, opt in enumerate(options):
            y = 3 + idx
            if y < h - 1:  # Stay within bounds
                if idx == current:
                    try:
                        if CURSES_COLORS_READY:
                            stdscr.attron(curses.color_pair(COLOR_HIGHLIGHT))
                        else:
                            stdscr.attron(curses.A_REVERSE)
                        stdscr.addstr(y, 4, str(opt)[:w-6])
                        if CURSES_COLORS_READY:
                            stdscr.attroff(curses.color_pair(COLOR_HIGHLIGHT))
                        else:
                            stdscr.attroff(curses.A_REVERSE)
                    except curses.error:
                        pass
                else:
                    try:
                        stdscr.addstr(y, 4, str(opt)[:w-6])
                    except curses.error:
                        pass
        
        # Help text
        try:
            if CURSES_COLORS_READY:
                stdscr.attron(curses.color_pair(COLOR_HELP))
            stdscr.addstr(h-1, 2, "Use UP/DN arrows, press ENTER to select"[:w-4])
            if CURSES_COLORS_READY:
                stdscr.attroff(curses.color_pair(COLOR_HELP))
        except curses.error:
            pass
        
        stdscr.refresh()
        
        try:
            key = stdscr.getch()
            if key == -1:  # Timeout, no key pressed
                continue
            if key in (curses.KEY_UP, ord('k')):
                current = (current - 1) % len(options)
            elif key in (curses.KEY_DOWN, ord('j')):
                current = (current + 1) % len(options)
            elif key in (curses.KEY_ENTER, ord('\n'), ord('\r'), 32):  # 32 = space
                return options[current]
        except KeyboardInterrupt:
            sys.exit(1)


def curses_input(stdscr, prompt, default="", password=False):
    """Prompt the user for text input."""
    curses.curs_set(1)  # Show cursor
    stdscr.keypad(True)
    stdscr.nodelay(False)
    stdscr.timeout(-1)  # Fully blocking input for reliability

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        input_width = min(50, max(1, w - 4))
        input_x = 2
        input_y = 5

        try:
            if CURSES_COLORS_READY:
                stdscr.attron(curses.color_pair(COLOR_TITLE))
            stdscr.addstr(2, 2, prompt[:w-4])
            if CURSES_COLORS_READY:
                stdscr.attroff(curses.color_pair(COLOR_TITLE))
            default_text = f" (default: {default})" if default else ""
            if CURSES_COLORS_READY:
                stdscr.attron(curses.color_pair(COLOR_LABEL))
            stdscr.addstr(3, 2, f"Enter value{default_text}:"[:w-4])
            if CURSES_COLORS_READY:
                stdscr.attroff(curses.color_pair(COLOR_LABEL))
            stdscr.attron(curses.A_REVERSE)
            stdscr.addstr(input_y, input_x, " " * input_width)
            stdscr.attroff(curses.A_REVERSE)
            if CURSES_COLORS_READY:
                stdscr.attron(curses.color_pair(COLOR_HELP))
            stdscr.addstr(h-1, 2, "Press ENTER to confirm, CTRL+C to cancel"[:w-4])
            if CURSES_COLORS_READY:
                stdscr.attroff(curses.color_pair(COLOR_HELP))
            stdscr.move(input_y, input_x)
            stdscr.refresh()
        except curses.error:
            pass

        try:
            if not password:
                curses.echo()
                raw = stdscr.getstr(input_y, input_x, input_width)
                curses.noecho()
                value = raw.decode(errors="ignore").strip()
            else:
                curses.noecho()
                value_chars = []
                while True:
                    key = stdscr.getch()
                    if key in (curses.KEY_ENTER, 10, 13):
                        break
                    if key in (curses.KEY_BACKSPACE, 127, 8):
                        if value_chars:
                            value_chars.pop()
                    elif 32 <= key <= 126 and len(value_chars) < input_width:
                        value_chars.append(chr(key))

                    try:
                        stdscr.attron(curses.A_REVERSE)
                        stdscr.addstr(input_y, input_x, ("*" * len(value_chars)).ljust(input_width)[:input_width])
                        stdscr.attroff(curses.A_REVERSE)
                        stdscr.move(input_y, min(input_x + len(value_chars), input_x + input_width - 1))
                        stdscr.refresh()
                    except curses.error:
                        pass

                value = "".join(value_chars)

            curses.curs_set(0)
            return value if value else default
        except KeyboardInterrupt:
            sys.exit(1)


def curses_confirm(stdscr, prompt, default=False):
    """Yes/no confirmation via menu."""
    choice = curses_menu(stdscr, prompt, ["Yes", "No"])
    return choice == "Yes"


def collect_configuration_curses():
    """Run the interactive setup using curses-based GUI."""
    cfg = {}

    def _inner(stdscr):
        try:
            _curses_init_colors()
            curses.cbreak()
            curses.noecho()
            stdscr.keypad(True)
            stdscr.timeout(100)  # 100ms timeout for smooth input capture
            # Show intro
            stdscr.erase()
            try:
                if CURSES_COLORS_READY:
                    stdscr.attron(curses.color_pair(COLOR_TITLE))
                stdscr.attron(curses.A_BOLD)
                stdscr.addstr(2, 2, "EMInstaller - GUI Setup")
                stdscr.attroff(curses.A_BOLD)
                if CURSES_COLORS_READY:
                    stdscr.attroff(curses.color_pair(COLOR_TITLE))
            except curses.error:
                pass
            try:
                if CURSES_COLORS_READY:
                    stdscr.attron(curses.color_pair(COLOR_HELP))
                stdscr.addstr(4, 2, "Use arrow keys to move, Enter to select")
                stdscr.addstr(5, 2, "Type to enter text, CTRL+C to cancel")
                if CURSES_COLORS_READY:
                    stdscr.attroff(curses.color_pair(COLOR_HELP))
            except curses.error:
                pass
            stdscr.refresh()
            time.sleep(2)
            
            # Disk selection
            disks = get_available_disks()
            if not disks:
                return {"error": "No disks available"}
            disk = curses_menu(stdscr, "Select installation disk", disks)
            cfg['disk'] = disk.split()[0]
            
            # Basic configuration
            cfg['hostname'] = curses_input(stdscr, "Hostname", "arch")
            cfg['username'] = curses_input(stdscr, "Username", "user")
            cfg['userpass'] = curses_input(stdscr, "User password", "", password=True)
            cfg['rootpass'] = curses_input(stdscr, "Root password", "", password=True)
            
            # System configuration
            cfg['fs'] = curses_menu(stdscr, "Filesystem", ["ext4", "btrfs", "xfs"])
            cfg['use_luks'] = curses_confirm(stdscr, "Enable LUKS Encryption?")
            cfg['create_swap'] = curses_confirm(stdscr, "Create Swapfile?")
            cfg['kernel'] = curses_menu(stdscr, "Kernel", ["linux", "linux-lts", "linux-zen"])
            
            # Desktop
            cfg['desktop'] = curses_menu(stdscr, "Desktop Environment", ["cli-only", "gnome", "kde", "hyprland", "xfce", "i3"])
            
            # Custom packages
            cfg['custom_packages_input'] = curses_input(stdscr, "Additional packages", "")
            
            # Optional features
            cfg['gaming'] = curses_confirm(stdscr, "Install Gaming Stack?")
            cfg['dev_tools'] = curses_confirm(stdscr, "Install Dev Tools?")
            cfg['dotfiles'] = curses_confirm(stdscr, "Install Dotfiles?")
            cfg['detected_gpu'] = detect_gpu()
            
            # Localization
            cfg['timezone'] = curses_input(stdscr, "Timezone", "UTC")
            cfg['language'] = curses_input(stdscr, "Language Code", "en_US")
            cfg['locale_encoding'] = curses_menu(stdscr, "Locale Encoding", ["UTF-8", "ISO-8859-1"])
            
            # GPU/Virtualization
            cfg['gpu'] = curses_menu(stdscr, "GPU Driver", ["none", "nvidia", "nvidia-legacy", "amd", "intel"])
            cfg['vm_graphics'] = curses_menu(stdscr, "VM Graphics", ["none", "qemu", "vmware", "virtualbox", "hyper-v"])
            
        except KeyboardInterrupt:
            sys.exit(1)
        except Exception as e:
            cfg['error'] = str(e)

    if curses is None:
        raise RuntimeError("curses module not available")

    try:
        if sys.stdin.isatty() and sys.stdout.isatty():
            curses.wrapper(_inner)
        else:
            # If launched via a pipe, bind curses to the controlling terminal.
            with open("/dev/tty", "r+", encoding="utf-8", errors="ignore") as tty:
                saved_stdin = os.dup(0)
                saved_stdout = os.dup(1)
                try:
                    os.dup2(tty.fileno(), 0)
                    os.dup2(tty.fileno(), 1)
                    curses.wrapper(_inner)
                finally:
                    os.dup2(saved_stdin, 0)
                    os.dup2(saved_stdout, 1)
                    os.close(saved_stdin)
                    os.close(saved_stdout)
    except Exception as e:
        raise RuntimeError(f"GUI error: {e}")

    if cfg.get('error'):
        raise RuntimeError(cfg['error'])
    
    return cfg


def _prompt_choice(prompt, options, default=None):
    while True:
        console.print(f"\n[cyan]{prompt}[/cyan]")
        for idx, opt in enumerate(options, start=1):
            console.print(f"  {idx}) {opt}")
        hint = f" [{default}]" if default else ""
        raw = prompt_input(f"Select option{hint}: ").strip()
        if not raw and default:
            raw = default

        if raw.isdigit():
            index = int(raw) - 1
            if 0 <= index < len(options):
                return options[index]

        if raw in options:
            return raw

        console.print("[yellow]Invalid choice, please try again.[/yellow]")


def _prompt_yes_no(prompt, default=False):
    suffix = "Y/n" if default else "y/N"
    while True:
        raw = prompt_input(f"{prompt} ({suffix}): ").strip().lower()
        if not raw:
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        console.print("[yellow]Please answer yes or no.[/yellow]")


def collect_configuration_text():
    """Fallback interactive setup without curses."""
    cfg = {}

    disks = get_available_disks()
    if not disks:
        console.print("[red]No disks available.[/red]")
        sys.exit(1)

    selected_disk = _prompt_choice("Select installation disk", disks, default="1")
    cfg['disk'] = selected_disk.split()[0]

    cfg['hostname'] = prompt_input("Hostname [arch]: ").strip() or "arch"
    cfg['username'] = prompt_input("Username [user]: ").strip() or "user"
    cfg['userpass'] = prompt_password("User password: ")
    cfg['rootpass'] = prompt_password("Root password: ")

    cfg['fs'] = _prompt_choice("Filesystem", ["ext4", "btrfs", "xfs"], default="1")
    cfg['use_luks'] = _prompt_yes_no("Enable LUKS Encryption?", default=False)
    cfg['create_swap'] = _prompt_yes_no("Create Swapfile?", default=False)
    cfg['kernel'] = _prompt_choice("Kernel", ["linux", "linux-lts", "linux-zen"], default="1")
    cfg['desktop'] = _prompt_choice(
        "Desktop Environment",
        ["cli-only", "gnome", "kde", "hyprland", "xfce", "i3"],
        default="1",
    )

    cfg['custom_packages_input'] = prompt_input("Additional packages (space-separated, optional): ").strip()
    cfg['gaming'] = _prompt_yes_no("Install Gaming Stack?", default=False)
    cfg['dev_tools'] = _prompt_yes_no("Install Dev Tools?", default=False)
    cfg['dotfiles'] = _prompt_yes_no("Install Dotfiles?", default=False)
    cfg['detected_gpu'] = detect_gpu()

    cfg['timezone'] = prompt_input("Timezone [UTC]: ").strip() or "UTC"
    cfg['language'] = prompt_input("Language Code [en_US]: ").strip() or "en_US"
    cfg['locale_encoding'] = _prompt_choice("Locale Encoding", ["UTF-8", "ISO-8859-1"], default="1")
    cfg['gpu'] = _prompt_choice("GPU Driver", ["none", "nvidia", "nvidia-legacy", "amd", "intel"], default="1")
    cfg['vm_graphics'] = _prompt_choice(
        "VM Graphics", ["none", "qemu", "vmware", "virtualbox", "hyper-v"], default="1"
    )

    return cfg




def check_root():
    if os.geteuid() != 0:
        console.print("[red]Error: you must run this script as root.[/red]")
        sys.exit(1)


def ensure_tools(*names):
    """Exit early if one of the required binaries is not in $PATH."""
    missing = [n for n in names if shutil.which(n) is None]
    if missing:
        console.print(f"[red]Missing required commands: {', '.join(missing)}[/red]")
        console.print("Please install them or run this script from an Arch live environment.")
        sys.exit(1)

console = Console()
DRY_RUN = False

def banner(text="EMInstaller v0.1.3"):
    ascii_art = rf"""
[cyan]
    _______  _______    ________   _______ 
  //       \/       \\ /        \//   /   \
 //        /        //_/       ///        /
/        _/         //         /         / 
\________/\__/__/__/ \\_______/\__/_____/  
EMIN — EMInstaller
[/cyan]
[magenta]{text}[/magenta]
"""
    console.print(ascii_art)

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

def run_stage(stage_name, cmd, duration=3, verbose=False):
    
    console.print(f"\n[bold yellow]==> {stage_name}[/bold yellow]")
    if DRY_RUN:
        console.print(f"[blue][dry-run][/blue] {cmd}")
        console.print(f"[green]✓ {stage_name} completed (dry-run)[/green]")
        return True

    max_runtime_seconds = 300
    stdout = ""
    stderr = ""
    timed_out = False

    try:
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception as e:
        console.print(f"[yellow]⚠ {stage_name} warning: {e}[/yellow]")
        return False

    with Progress(
        SpinnerColumn(style="bright_cyan"),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(
            bar_width=42,
            complete_style="bold green",
            finished_style="bright_green",
            pulse_style="bright_blue",
        ),
        TimeElapsedColumn(),
        transient=True,
        expand=True,
        console=console,
    ) as progress:
        task = progress.add_task(f"{stage_name}...", total=None)
        start = time.monotonic()

        while process.poll() is None:
            if time.monotonic() - start > max_runtime_seconds:
                timed_out = True
                process.kill()
                break
            progress.update(task)
            time.sleep(0.1)

    if timed_out:
        stderr = "Timeout"
        success = False
    else:
        stdout, stderr = process.communicate()
        success = process.returncode == 0

    if verbose and stdout:
        console.print(stdout)

    if success or "error" not in stderr.lower():
        console.print(f"[green]✓ {stage_name} completed[/green]")
        return True
    else:
        console.print(f"[yellow]⚠ {stage_name} warning: {stderr[:100]}[/yellow]")
        return False


def arch_chroot(cmd, description=None, duration=1, verbose=False):
    """Helper to run a command inside the /mnt chroot using run_stage."""
    if description is None:
        description = cmd.split()[0]
    full_cmd = f"arch-chroot /mnt {cmd}"
    return run_stage(description, full_cmd, duration, verbose)


def ensure_chroot_alpm_user():
    """Ensure pacman's DownloadUser exists inside chroot before pacman -S runs."""
    arch_chroot(
        "bash -lc \"id -u alpm >/dev/null 2>&1 || useradd -r -M -s /usr/bin/nologin -d /var/lib/pacman alpm\"",
        "Ensuring pacman DownloadUser",
    )

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


def validate_configuration(cfg):
    """Validate user-provided configuration values before destructive steps."""
    errors = []

    disk = cfg.get("disk", "")
    if not re.fullmatch(r"/dev/[A-Za-z0-9._-]+", disk):
        errors.append(f"Invalid disk path: {disk}")

    hostname = cfg.get("hostname", "")
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", hostname):
        errors.append("Hostname must be 1-63 chars and contain only letters, numbers, and hyphens (no leading/trailing hyphen).")

    username = cfg.get("username", "")
    if not re.fullmatch(r"[a-z_][a-z0-9_-]{0,31}", username):
        errors.append("Username must start with a lowercase letter/underscore and contain only lowercase letters, numbers, '_' or '-'.")

    timezone = cfg.get("timezone", "")
    if not re.fullmatch(r"[A-Za-z0-9._+-]+(?:/[A-Za-z0-9._+-]+)*", timezone):
        errors.append("Timezone contains invalid characters.")

    language = cfg.get("language", "")
    if not re.fullmatch(r"[A-Za-z]{2,3}_[A-Za-z]{2,3}", language):
        errors.append("Language must be in format like en_US.")

    locale_encoding = cfg.get("locale_encoding", "")
    if locale_encoding not in {"UTF-8", "ISO-8859-1"}:
        errors.append(f"Unsupported locale encoding: {locale_encoding}")

    if not cfg.get("userpass"):
        errors.append("User password cannot be empty.")
    if not cfg.get("rootpass"):
        errors.append("Root password cannot be empty.")

    if errors:
        console.print("[red]Configuration validation failed:[/red]")
        for error in errors:
            console.print(f"  - {error}")
        sys.exit(1)

# summary & confirmation (called from main)

def print_summary(cfg, assume_yes=False):
    console.print("\n[bold yellow]=== Installation Configuration ===[/bold yellow]\n")
    items = [
        ("Disk", cfg['disk']),
        ("Hostname", cfg['hostname']),
        ("Username", cfg['username']),
        ("Filesystem", cfg['fs']),
        ("LUKS Encryption", cfg['use_luks']),
        ("Swapfile", cfg['create_swap']),
        ("Kernel", cfg['kernel']),
        ("Desktop", cfg['desktop']),
        ("Timezone", cfg['timezone']),
        ("Language", cfg['language']),
        ("Locale Encoding", cfg['locale_encoding']),
        ("GPU Driver", cfg['gpu']),
        ("VM Graphics", cfg['vm_graphics']),
        ("Gaming Stack", cfg['gaming']),
        ("Dev Tools", cfg['dev_tools']),
        ("Dotfiles", cfg['dotfiles']),
    ]
    for name, val in items:
        console.print(f"  [cyan]{name}:[/cyan] {val}")
    console.print()
    
    if not assume_yes:
        # Show a final warning/confirmation before proceeding
        console.print(f"[bold red]⚠ WARNING: This will erase ALL data on {cfg['disk']}.[/bold red]")
        response = prompt_input("Type 'YES' to proceed or press Enter to cancel: ")
        if response.upper() != "YES":
            console.print("[yellow]Installation cancelled.[/yellow]")
            sys.exit(0)


# main entrypoint


def main():
    global DRY_RUN
    check_platform()
    check_root()
    # verify we have the external commands we rely on
    ensure_tools(
        "lsblk",
        "parted",
        "mkfs.fat",
        "pacstrap",
        "genfstab",
        "grub-install",
        "arch-chroot",
        "wipefs",
        "mount",
        "umount",
        "dd",
        "mkswap",
    )

    parser = argparse.ArgumentParser(description="EMInstaller - interactive Arch installer")
    parser.add_argument("-y", "--yes", action="store_true", help="Assume yes for all confirmations")
    parser.add_argument("--no-gui", action="store_true", help="Use text prompts instead of curses GUI")
    parser.add_argument("--dry-run", action="store_true", help="Print planned commands without executing them")
    args = parser.parse_args()
    DRY_RUN = args.dry_run

    # Prefer GUI by default; fall back to text mode only when GUI is unavailable.
    try:
        if args.no_gui:
            cfg = collect_configuration_text()
        else:
            try:
                cfg = collect_configuration_curses()
            except RuntimeError as gui_error:
                console.print(f"[yellow]GUI unavailable, falling back to text mode: {gui_error}[/yellow]")
                cfg = collect_configuration_text()
        validate_configuration(cfg)
        print_summary(cfg, assume_yes=args.yes)
    except EOFError as e:
        console.print(f"[red]Input error: {e}[/red]")
        console.print("[yellow]Tip: run from a local terminal with a TTY, or avoid piping stdin into the installer process.[/yellow]")
        sys.exit(1)

    
    # begin installation using values from cfg
    
    disk = cfg['disk']
    hostname = cfg['hostname']
    username = cfg['username']
    userpass = cfg['userpass']
    rootpass = cfg['rootpass']
    fs = cfg['fs']
    create_swap = cfg['create_swap']
    kernel = cfg['kernel']
    desktop = cfg['desktop']
    custom_packages_input = cfg['custom_packages_input']
    gaming = cfg['gaming']
    dev_tools = cfg['dev_tools']
    custom_packages = []
    timezone = cfg['timezone']
    language = cfg['language']
    locale_encoding = cfg['locale_encoding']
    gpu = cfg['gpu']
    vm_graphics = cfg['vm_graphics']

    fs_tool_map = {
        "ext4": "mkfs.ext4",
        "btrfs": "mkfs.btrfs",
        "xfs": "mkfs.xfs",
    }
    fs_tool = fs_tool_map.get(fs)
    if fs_tool is None:
        console.print(f"[red]Unsupported filesystem: {fs}[/red]")
        sys.exit(1)
    ensure_tools(fs_tool)

    q_disk = shlex.quote(disk)
    q_hostname = shlex.quote(hostname)
    q_username = shlex.quote(username)
    q_rootpass_entry = shlex.quote(f"root:{rootpass}")
    q_userpass_entry = shlex.quote(f"{username}:{userpass}")
    q_timezone_path = shlex.quote(f"/usr/share/zoneinfo/{timezone}")

    console.print("\n[bold green]Starting installation to disk...[/bold green]\n")

    # partition naming
    if "nvme" in disk:
        efi_part = f"{disk}p1"
        root_part = f"{disk}p2"
    else:
        efi_part = f"{disk}1"
        root_part = f"{disk}2"

    q_efi_part = shlex.quote(efi_part)
    q_root_part = shlex.quote(root_part)
    q_fs = shlex.quote(fs)

    run_stage("Wiping disk", f"wipefs -af {q_disk}", duration=2)
    run_stage("Creating GPT partition table", f"parted -s {q_disk} mklabel gpt", duration=1)
    run_stage("Creating EFI partition (512MB)", f"parted -s {q_disk} mkpart primary fat32 1MiB 513MiB", duration=1)
    run_stage("Setting EFI boot flag", f"parted -s {q_disk} set 1 esp on", duration=1)
    run_stage("Creating root partition", f"parted -s {q_disk} mkpart primary {q_fs} 513MiB 100%", duration=1)
    run_stage("Formatting EFI partition", f"mkfs.fat -F32 -n EFI {q_efi_part}", duration=1)
    run_stage(f"Formatting root partition ({fs})", f"{fs_tool} -L arch {q_root_part}", duration=3)
    run_stage("Creating mount directories", f"mkdir -p /mnt/boot /mnt", duration=1)
    run_stage("Mounting root partition", f"mount {q_root_part} /mnt", duration=1)
    run_stage("Mounting EFI partition", f"mkdir -p /mnt/boot/efi && mount {q_efi_part} /mnt/boot/efi", duration=1)

    if create_swap:
        run_stage("Creating swapfile (2GB)", f"dd if=/dev/zero of=/mnt/swapfile bs=1M count=2048 && chmod 600 /mnt/swapfile && mkswap /mnt/swapfile", duration=3)

    # build package set (use set to dedupe)
    packages = {"base", "linux-firmware", "grub", "efibootmgr", kernel, "networkmanager", "vim", "sudo"}

    if custom_packages_input.strip():
        for pkg in custom_packages_input.split():
            if re.match(r'^[a-zA-Z0-9@._+-]+$', pkg):
                custom_packages.append(pkg)
            else:
                console.print(f"[red]Invalid package name ignored: {pkg}[/red]")

    if desktop != "cli-only":
        packages.add("xorg")
        if desktop == "gnome":
            packages.update({"gnome", "gdm", "networkmanager", "network-manager-applet", "konsole"})
        elif desktop == "kde":
            packages.update({"plasma", "sddm", "networkmanager", "konsole"})
        elif desktop == "hyprland":
            # lightweight Wayland compositor
            packages.update({"hyprland", "kitty", "dolphin", "wayland", "xorg-xwayland", "lightdm", "lightdm-gtk-greeter"})
        elif desktop == "xfce":
            packages.update({"xfce4", "xfce4-goodies", "lightdm", "lightdm-gtk-greeter", "konsole"})
        elif desktop == "i3":
            packages.update({"i3", "i3status", "lightdm", "lightdm-gtk-greeter", "konsole"})

    if gaming:
        packages.update({"steam", "wine", "lutris"})
    if dev_tools:
        packages.update({"git", "base-devel", "npm", "python"})
    if custom_packages:
        packages.update(custom_packages)

    package_args = " ".join(shlex.quote(pkg) for pkg in sorted(packages))
    run_stage("Installing base packages", f"pacstrap /mnt {package_args}", duration=10)
    run_stage("Generating fstab", "genfstab -U /mnt >> /mnt/etc/fstab", duration=1)

    console.print("\n[bold green]Configuring system in chroot...[/bold green]\n")
    # timezone/locale/hostname/hosts/passwords/users
    arch_chroot(f"ln -sf {q_timezone_path} /etc/localtime", "Setting timezone")
    locale_string = f"{language}.{locale_encoding}"
    q_locale_line = shlex.quote(f"{locale_string} {locale_encoding}")
    q_lang_line = shlex.quote(f"LANG={locale_string}")
    q_host_line = shlex.quote(f"127.0.1.1 {hostname}.localdomain {hostname}")
    q_sudoers_line = shlex.quote(f"{username} ALL=(ALL) ALL")
    q_sudoers_file = shlex.quote(f"/etc/sudoers.d/{username}")

    arch_chroot(f"bash -lc \"printf '%s\\n' {q_locale_line} >> /etc/locale.gen && locale-gen\"", "Generating locale", duration=2)
    arch_chroot(f"bash -lc \"printf '%s\\n' {q_lang_line} > /etc/locale.conf\"", "Setting LANG")
    arch_chroot(f"bash -lc \"printf '%s\\n' {q_hostname} > /etc/hostname\"", "Setting hostname")
    arch_chroot(
        f"bash -lc \"printf '%s\\n' '127.0.0.1 localhost' '::1 localhost' {q_host_line} >> /etc/hosts\"",
        "Configuring hosts",
    )
    arch_chroot(f"bash -lc \"printf '%s\\n' {q_rootpass_entry} | chpasswd\"", "Setting root password")
    arch_chroot(f"useradd -m -s /bin/bash {q_username}", "Creating user")
    arch_chroot(f"bash -lc \"printf '%s\\n' {q_userpass_entry} | chpasswd\"", "Setting user password")

    arch_chroot("systemctl enable NetworkManager", "Enabling NetworkManager")
    arch_chroot("mkdir -p /etc/sudoers.d", "Creating sudoers directory")
    arch_chroot(
        f"bash -lc \"printf '%s\\n' {q_sudoers_line} > {q_sudoers_file} && chmod 0440 {q_sudoers_file}\"",
        "Configuring sudoers",
    )
    arch_chroot(f"test -f {q_sudoers_file} && echo 'sudoers configured'", "Verifying sudoers configuration")

    if desktop == "gnome":
        arch_chroot("systemctl enable gdm", "Enabling GNOME Display Manager (GDM)")
    elif desktop == "kde":
        arch_chroot("systemctl enable sddm", "Enabling Simple Desktop Display Manager (SDDM)")
    elif desktop in ["hyprland", "xfce", "i3"]:
        arch_chroot("systemctl enable lightdm", "Enabling LightDM")

    arch_chroot("grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=GRUB", "Installing GRUB", duration=2)
    arch_chroot("grub-mkconfig -o /boot/grub/grub.cfg", "Generating GRUB config")

    ensure_chroot_alpm_user()

    # GPU & VM drivers
    if gpu == "nvidia":
        arch_chroot("pacman -S --noconfirm nvidia nvidia-utils", "Installing NVIDIA drivers", duration=5)
    elif gpu == "nvidia-legacy":
        arch_chroot("pacman -S --noconfirm xf86-video-nouveau", "Installing Nouveau (Legacy NVIDIA fallback)", duration=3)
    elif gpu == "amd":
        arch_chroot("pacman -S --noconfirm xf86-video-amdgpu", "Installing AMD drivers", duration=5)
    elif gpu == "intel":
        arch_chroot("pacman -S --noconfirm xf86-video-intel", "Installing Intel drivers", duration=3)

    if vm_graphics == "qemu":
        arch_chroot("pacman -S --noconfirm xf86-video-qxl spice-vdagent", "Installing QEMU graphics drivers", duration=3)
    elif vm_graphics == "vmware":
        arch_chroot("pacman -S --noconfirm xf86-video-vmware open-vm-tools", "Installing VMware graphics drivers", duration=3)
    elif vm_graphics == "virtualbox":
        arch_chroot("pacman -S --noconfirm virtualbox-guest-utils", "Installing VirtualBox graphics drivers", duration=3)
    elif vm_graphics == "hyper-v":
        arch_chroot("pacman -S --noconfirm xf86-video-fbdev", "Installing Hyper-V graphics drivers", duration=3)

    arch_chroot("umount -R /mnt", "Unmounting partitions")

    console.print()
    banner("INSTALLATION COMPLETE!")
    console.print(f"[bold green]Arch Linux has been successfully installed on {disk}![/bold green]\n")

    console.print("[cyan]Final Configuration Summary:[/cyan]")
    console.print(f"  Disk: [green]{disk}[/green]")
    console.print(f"  Hostname: [green]{hostname}[/green]")
    console.print(f"  User: [green]{username}[/green]")
    console.print(f"  Desktop: [green]{desktop}[/green]")
    console.print(f"  Filesystem: [green]{fs}[/green]")
    console.print(f"  Kernel: [green]{kernel}[/green]")
    console.print(f"  Timezone: [green]{timezone}[/green]")
    console.print(f"  Language: [green]{language}[/green]")
    console.print(f"  Locale Encoding: [green]{locale_encoding}[/green]")
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

    if custom_packages:
        console.print(f"  [cyan]Custom Packages:[/cyan] {' '.join(custom_packages)}")

    console.print("\n[bold green]Installation successful! You can now remove the ISO and boot from disk.[/bold green]")


if __name__ == "__main__":
    main()
