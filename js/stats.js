document.addEventListener("DOMContentLoaded", () => {

    const repoOwner = "imemix";
    const repoName = "imemix.github.io";

    const githubHeaders = {
        Accept: "application/vnd.github+json",
        "User-Agent": "EMInstaller-site"
    };

    let rateLimitNoticeShown = false;

    const statEls = {
        stars: document.querySelector('[data-stat="stars"]'),
        forks: document.querySelector('[data-stat="forks"]'),
        issues: document.querySelector('[data-stat="issues"]'),
        watchers: document.querySelector('[data-stat="watchers"]'),
        updated: document.querySelector('[data-stat="updated"]'),
        license: document.querySelector('[data-stat="license"]'),
        installerStatus: document.getElementById("installer-status"),
        linesAdded: document.querySelector('[data-stat="lines-added"]'),
        linesDeleted: document.querySelector('[data-stat="lines-deleted"]'),
        lastCommit: document.querySelector('[data-stat="last-commit"]'),
        lastCommitMessage: document.querySelector('[data-stat="last-commit-message"]')
    };

    const setAllStats = (value) => {
        Object.values(statEls).forEach((el) => {
            if (el) {
                el.textContent = value;
                if (el === statEls.lastCommit) {
                    el.removeAttribute("href");
                    el.removeAttribute("aria-label");
                }
                if (el === statEls.lastCommitMessage) {
                    el.removeAttribute("title");
                }
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

    const updateLineStats = (addedText, deletedText) => {
        if (statEls.linesAdded) {
            statEls.linesAdded.textContent = addedText;
        }
        if (statEls.linesDeleted) {
            statEls.linesDeleted.textContent = deletedText;
        }
    };

    const updateLastCommit = (isoDate, sha, url, message) => {
        const lastCommitEl = statEls.lastCommit;
        const messageEl = statEls.lastCommitMessage;

        const resetLastCommit = (text = "--") => {
            if (lastCommitEl) {
                lastCommitEl.textContent = text;
                lastCommitEl.removeAttribute("href");
                lastCommitEl.removeAttribute("aria-label");
            }
            if (messageEl) {
                messageEl.textContent = text;
                messageEl.removeAttribute("title");
            }
        };

        if (!lastCommitEl && !messageEl) {
            return;
        }

        if (!isoDate) {
            resetLastCommit();
            return;
        }

        const formatted = formatUpdatedDate(isoDate);
        if (formatted === "--") {
            resetLastCommit();
            return;
        }

        if (lastCommitEl) {
            lastCommitEl.textContent = sha
                ? `${formatted} (${sha.slice(0, 7)})`
                : formatted;

            if (url) {
                lastCommitEl.setAttribute("href", url);
                if (sha) {
                    lastCommitEl.setAttribute("aria-label", `View commit ${sha}`);
                } else {
                    lastCommitEl.removeAttribute("aria-label");
                }
            } else {
                lastCommitEl.removeAttribute("href");
                lastCommitEl.removeAttribute("aria-label");
            }
        }

        if (messageEl) {
            const trimmedMessage = typeof message === "string" ? message.trim() : "";
            const summary = trimmedMessage ? trimmedMessage.split("\n")[0].trim() : "";
            messageEl.textContent = summary || "--";

            if (trimmedMessage) {
                messageEl.setAttribute("title", trimmedMessage);
            } else {
                messageEl.removeAttribute("title");
            }
        }
    };

    const showRateLimitNotice = (resetEpochSeconds) => {
        if (rateLimitNoticeShown) {
            return;
        }
        rateLimitNoticeShown = true;

        const parsedReset = Number(resetEpochSeconds);
        const resetDate = Number.isFinite(parsedReset)
            ? new Date(parsedReset * 1000)
            : null;

        const resetTime = resetDate
            ? resetDate.toLocaleTimeString(undefined, {
                hour: "2-digit",
                minute: "2-digit"
            })
            : null;

        const message = resetTime
            ? `GitHub API limit hit. Resets at ${resetTime}.`
            : "GitHub API limit hit. Try again later.";

        setAllStats("Rate limited");
        updateLineStats("Rate limited", "Rate limited");

        if (statEls.installerStatus) {
            statEls.installerStatus.textContent = message;
        }
    };

    const detectRateLimit = (response) => {
        if (response.status !== 403) {
            return;
        }

        const remaining = response.headers.get("X-RateLimit-Remaining");
        if (remaining !== "0") {
            return;
        }

        const resetEpochSeconds = response.headers.get("X-RateLimit-Reset");
        showRateLimitNotice(resetEpochSeconds);
    };

    const githubFetch = async (url, options = {}) => {
        const mergedHeaders = options.headers
            ? { ...githubHeaders, ...options.headers }
            : githubHeaders;

        const response = await fetch(url, { ...options, headers: mergedHeaders });
        detectRateLimit(response);
        return response;
    };

    const loadLatestCommitStats = async () => {
        try {
            updateLineStats("Loading latest...", "Loading latest...");
            if (statEls.lastCommit) {
                statEls.lastCommit.textContent = "Loading latest...";
                statEls.lastCommit.removeAttribute("href");
                statEls.lastCommit.removeAttribute("aria-label");
            }
            if (statEls.lastCommitMessage) {
                statEls.lastCommitMessage.textContent = "Loading latest...";
                statEls.lastCommitMessage.removeAttribute("title");
            }

            const commitsResponse = await githubFetch(`https://api.github.com/repos/${repoOwner}/${repoName}/commits?per_page=1`);
            if (!commitsResponse.ok) {
                throw new Error("Failed to fetch latest commit list" + ` (status: ${commitsResponse.status})`);
            }

            const commits = await commitsResponse.json();
            if (!Array.isArray(commits) || commits.length === 0 || !commits[0]?.url) {
                updateLineStats("Checking...", "--");
                updateLastCommit(null);
                return;
            }

            const commitResponse = await githubFetch(commits[0].url);
            if (!commitResponse.ok) {
                throw new Error("Failed to fetch commit stats" + ` (status: ${commitResponse.status})`);
            }

            const commitData = await commitResponse.json();
            const stats = commitData?.stats;

            const commitDate = commitData?.commit?.committer?.date || commitData?.commit?.author?.date;
            const commitSha = commitData?.sha;
            const commitUrl = commitData?.html_url;
            const commitMessage = commitData?.commit?.message;
            updateLastCommit(commitDate, commitSha, commitUrl, commitMessage);

            if (stats) {
                updateLineStats(`+${formatNumber(stats.additions || 0)}`, `-${formatNumber(stats.deletions || 0)}`);
            } else {
                updateLineStats("--", "--");
            }
        } catch (error) {
            if (rateLimitNoticeShown) {
                updateLineStats("Rate limited", "Rate limited");
            } else {
                updateLineStats("--", "--");
                updateLastCommit(null);
            }
        }
    };

    const loadCodeFrequency = async (attempt = 0) => {
        const maxAttempts = 5;
        const retryDelay = 2000;

        if (!statEls.linesAdded && !statEls.linesDeleted) {
            return;
        }

        try {
            const response = await githubFetch(`https://api.github.com/repos/${repoOwner}/${repoName}/stats/code_frequency`);

            if (response.status === 202) {
                updateLineStats("Loading...", "Loading...");
                if (attempt < maxAttempts) {
                    setTimeout(() => {
                        loadCodeFrequency(attempt + 1);
                    }, retryDelay * (attempt + 1));
                } else {
                    loadLatestCommitStats();
                }
                return;
            }

            if (!response.ok) {
                throw new Error("Failed to fetch code frequency stats" + ` (status: ${response.status})`);
            }

            const codeFrequencyData = await response.json();

            if (Array.isArray(codeFrequencyData) && codeFrequencyData.length > 0) {
                const totals = codeFrequencyData.reduce((acc, week) => {
                    if (!Array.isArray(week) || week.length < 3) {
                        return acc;
                    }
                    acc.added += Math.max(0, week[1] || 0);
                    acc.deleted += Math.abs(week[2] || 0);
                    return acc;
                }, { added: 0, deleted: 0 });

                updateLineStats(`+${formatNumber(totals.added)}`, `-${formatNumber(totals.deleted)}`);
            } else {
                loadLatestCommitStats();
            }
        } catch (error) {
            if (rateLimitNoticeShown) {
                updateLineStats("Rate limited", "Rate limited");
            } else {
                loadLatestCommitStats();
            }
        }
    };

    const loadRepoStats = async () => {
        try {
            setAllStats("Loading...");

            const response = await githubFetch(`https://api.github.com/repos/${repoOwner}/${repoName}`);
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
            if (statEls.installerStatus && !rateLimitNoticeShown) {
                statEls.installerStatus.textContent = "Working ✓";
            }
            
            loadCodeFrequency();
        } catch (error) {
            if (!rateLimitNoticeShown) {
                setAllStats("Unavailable");
            }
        }
    };

    loadRepoStats();
    loadLatestCommitStats();
});
