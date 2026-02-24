document.addEventListener("DOMContentLoaded", () => {
    const progress = document.getElementById("progress-bar");
    const log = document.getElementById("boot-log");

    let percent = 0;

    const steps = [
        "[ OK ] Partitioning disks",
        "[ OK ] Formatting filesystem",
        "[ OK ] Installing base system",
        "[ OK ] Installing kernel",
        "[ OK ] Installing GPU drivers",
        "[ OK ] Installing desktop environment",
        "[ OK ] Applying dotfiles",
        "[ OK ] Finalizing installation"
    ];

    let stepIndex = 0;

    const interval = setInterval(() => {
        percent += 5;
        progress.style.width = percent + "%";

        if (stepIndex < steps.length && percent % 15 === 0) {
            log.textContent += "\n" + steps[stepIndex++];
            log.scrollTop = log.scrollHeight;
        }

        if (percent >= 100) {
            clearInterval(interval);
            log.textContent += "\n[SUCCESS] Installation ready. Reboot to continue.";
        }
    }, 400);
});