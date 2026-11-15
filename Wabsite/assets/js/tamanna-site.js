// Smooth scroll
        function scrollToSection(id) {
            const el = document.getElementById(id);
            if (!el) return;
            window.scrollTo({
                top: el.offsetTop - 80,
                behavior: "smooth"
            });
        }

        // Simple intersection fade‑in
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("visible");
                    }
                });
            },
            { threshold: 0.15 }
        );

        document.querySelectorAll(".fade-in").forEach((el) => observer.observe(el));
