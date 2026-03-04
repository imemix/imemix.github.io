(() => {
    const applyLazyLoading = () => {
        const viewportHeight = window.innerHeight || document.documentElement.clientHeight;

        document.querySelectorAll("img").forEach((img) => {
            if (!img.hasAttribute("decoding")) {
                img.setAttribute("decoding", "async");
            }

            if (!img.hasAttribute("loading")) {
                const rect = img.getBoundingClientRect();
                const isAboveFold = rect.top >= 0 && rect.top < viewportHeight;
                img.setAttribute("loading", isAboveFold ? "eager" : "lazy");
            }
        });

        document.querySelectorAll("iframe").forEach((iframe) => {
            if (!iframe.hasAttribute("loading")) {
                iframe.setAttribute("loading", "lazy");
            }
        });
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", applyLazyLoading, { once: true });
    } else {
        applyLazyLoading();
    }
})();