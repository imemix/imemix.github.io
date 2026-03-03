document.addEventListener("DOMContentLoaded", () => {
    const progress_bar = document.getElementById("progress-bar");
    const log = document.getElementById("boot-log");
    const progress_text = document.getElementById("progress-text");

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
        
        percent = Math.min(percent + 5, 100);

        
        progress_bar.style.width = percent + "%";
        progress_text.textContent = percent + "%";

        
        if (stepIndex < steps.length && percent % 15 === 0) {
            log.textContent += "\n" + steps[stepIndex++];
            log.scrollTop = log.scrollHeight;
        }

        if (percent >= 100) {
            clearInterval(interval);
            log.textContent += "\n[SUCCESS] Installation ready. Reboot to continue.";
        }
    }, 400);

    const repoOwner = "imemix";
    const repoName = "imemix.github.io";

    const statEls = {
        stars: document.querySelector('[data-stat="stars"]'),
        forks: document.querySelector('[data-stat="forks"]'),
        issues: document.querySelector('[data-stat="issues"]'),
        watchers: document.querySelector('[data-stat="watchers"]'),
        updated: document.querySelector('[data-stat="updated"]'),
        license: document.querySelector('[data-stat="license"]'),
        installerStatus: document.getElementById("installer-status"),
        pythonCode: document.querySelector('[data-stat="python-code"]')
    };

    const setAllStats = (value) => {
        Object.values(statEls).forEach((el) => {
            if (el) {
                el.textContent = value;
            }
        });
    };

    const formatNumber = (value) => new Intl.NumberFormat().format(value);

    const formatUpdatedDate = (isoDate) => {
        const parsed = new Date(isoDate);
        if (Number.isNaN(parsed.getTime())) {
            return "--";
        }
        return parsed.toLocaleDateString(undefined, {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        });
    };

    const loadRepoStats = async () => {
        try {
            setAllStats("Loading...");

            const response = await fetch(`https://api.github.com/repos/${repoOwner}/${repoName}`);
            if (!response.ok) {
                throw new Error("Failed to fetch repository stats"+` (status: ${response.status})`);
            }

            const data = await response.json();

            if (statEls.stars) {
                statEls.stars.textContent = formatNumber(data.stargazers_count || 0);
            }
            if (statEls.forks) {
                statEls.forks.textContent = formatNumber(data.forks_count || 0);
            }
            if (statEls.issues) {
                statEls.issues.textContent = formatNumber(data.open_issues_count || 0);
            }
            if (statEls.watchers) {
                statEls.watchers.textContent = formatNumber(data.subscribers_count || 0);
            }
            if (statEls.updated) {
                statEls.updated.textContent = formatUpdatedDate(data.updated_at);
            }
            if (statEls.license) {
                statEls.license.textContent = data.license ? data.license.spdx_id : "--";
            }
            if (statEls.installerStatus) {
                statEls.installerStatus.textContent = "Working ✓";
            }
            if (statEls.pythonCode) {
                statEls.pythonCode.textContent = formatNumber(data.size || 0) + " - Slitherly lines of code";
            }
        } catch (error) {
            setAllStats("Unavailable");
        }
    };

    loadRepoStats();
});
