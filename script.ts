// main.ts

const CANONICAL_HOST = "informatique-plouguerneau-antoine-conter.fr";

function setupCanonicalRedirect() {
  const host = location.hostname.toLowerCase();
  const isGithub = host.endsWith(".github.io");
  const isWww = host === "www." + CANONICAL_HOST;

  if (isGithub || isWww) {
    const target = `https://${CANONICAL_HOST}${location.pathname}${location.search}${location.hash}`;
    if (location.href !== target) {
      location.replace(target);
    }
  }
}

function setupTOC(reduceMotion: boolean) {
  const container = document.getElementById("toc-list");
  const tocBanner = document.querySelector<HTMLElement>(".toc-banner");
  if (!container || !tocBanner) return;

  const headings = Array.from(
    document.querySelectorAll<HTMLHeadingElement>(
      "section:not(.hidden-list) h2.titre-section, section:not(.hidden-list) > h2"
    )
  );

  if (!headings.length) {
    tocBanner.style.display = "none";
    return;
  }

  headings.forEach((h2, idx) => {
    const parentSection = h2.closest("section");
    if (parentSection && !parentSection.id) {
      const base = (h2.textContent || `section-${idx + 1}`)
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/(^-|-$)/g, "")
        .slice(0, 40);

      let unique = base || `section-${idx + 1}`;
      let i = 2;
      while (document.getElementById(unique)) {
        unique = `${base}-${i++}`;
      }
      parentSection.id = unique;
    }
  });

  const listItems: HTMLLIElement[] = [];
  headings.forEach((h2) => {
    const sec = h2.closest("section");
    if (!sec || !sec.id) return;
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = `#${sec.id}`;
    a.textContent = (h2.textContent || "").trim();
    li.appendChild(a);
    listItems.push(li);
  });

  if (!listItems.length) {
    tocBanner.style.display = "none";
    return;
  }

  listItems.forEach((li) => container.appendChild(li));

  const toggle = document.querySelector<HTMLButtonElement>(".toc-toggle");
  if (toggle) {
    let open = false;
    const setState = (state: boolean) => {
      open = state;
      toggle.setAttribute("aria-expanded", String(open));
      container.classList.toggle("is-open", open);
      tocBanner.setAttribute("aria-expanded", String(open));
    };

    toggle.addEventListener("click", () => setState(!open));

    const mq = window.matchMedia("(max-width: 992px)");
    const applyMQ = () => setState(!mq.matches);
    applyMQ();
    if (mq.addEventListener) {
      mq.addEventListener("change", applyMQ);
    } else {
      // @ts-ignore (compat ancien)
      mq.addListener(applyMQ);
    }
  }
}

function setupContactBubble() {
  const bubble = document.getElementById("contact-bubble");
  const form = document.getElementById("contact-form");
  const closeBtn = document.getElementById("close-form");

  if (!bubble || !form || !closeBtn) return;

  const setOpen = (open: boolean) => {
    form.style.display = open ? "block" : "none";
    bubble.setAttribute("aria-expanded", String(open));
  };

  bubble.addEventListener("click", () => setOpen(true));
  closeBtn.addEventListener("click", () => setOpen(false));

  document.addEventListener("click", (e) => {
    const target = e.target as Node;
    if (!form.contains(target) && target !== bubble) {
      setOpen(false);
    }
  });
}

function setupReveal(reduceMotion: boolean) {
  const targets = Array.from(document.querySelectorAll<HTMLElement>(".reveal"));

  if (!("IntersectionObserver" in window) || reduceMotion) {
    targets.forEach((t) => t.classList.add("is-visible", "visible"));
    return;
  }

  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const el = entry.target as HTMLElement;
          el.classList.add("is-visible", "visible");
          el.classList.add("animate__animated", "animate__fadeInUp");
          io.unobserve(el);
        }
      });
    },
    { rootMargin: "0px 0px -10% 0px", threshold: 0.1 }
  );

  targets.forEach((t) => io.observe(t));
}

function setupCopyToast() {
  const toast = document.getElementById("live-region") || document.getElementById("toast");
  if (!toast) return;

  const showToast = (msg: string) => {
    toast.textContent = msg;
    toast.classList.add("show");
    window.setTimeout(() => toast.classList.remove("show"), 1600);
  };

  document.addEventListener("click", (e) => {
    const target = e.target as HTMLElement | null;
    if (!target) return;
    const btn = target.closest<HTMLButtonElement>(".copy-btn");
    if (!btn) return;

    e.preventDefault();
    const value = btn.getAttribute("data-copy") || "";
    if (!value) return;

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard
        .writeText(value)
        .then(() => showToast(`Copié : ${value}`))
        .catch(() => showToast("Impossible de copier."));
    } else {
      try {
        const input = document.createElement("input");
        input.value = value;
        document.body.appendChild(input);
        input.select();
        document.execCommand("copy");
        document.body.removeChild(input);
        showToast(`Copié : ${value}`);
      } catch {
        showToast("Impossible de copier.");
      }
    }
  });
}

function setupPrefetchProjets() {
  const link = document.querySelector<HTMLAnchorElement>('#projets-lien a[href$="projets.html"]');
  if (!link) return;

  const prefetch = () => {
    if ((link as any).dataset.prefetched) return;
    const l = document.createElement("link");
    l.rel = "prefetch";
    l.href = link.href;
    document.head.appendChild(l);
    (link as any).dataset.prefetched = "1";
  };

  link.addEventListener("mouseenter", prefetch, { passive: true });
  link.addEventListener("focus", prefetch, { passive: true });

  if ("requestIdleCallback" in window) {
    (window as any).requestIdleCallback(prefetch, { timeout: 2000 });
  }
}

function setupServiceWorker() {
  if (!("serviceWorker" in navigator)) return;
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  });
}

function applyReducedMotion(reduceMotion: boolean) {
  if (!reduceMotion) return;
  const animated = document.querySelectorAll<HTMLElement>('[class*="animate__"]');
  animated.forEach((el) => {
    el.className = el.className.replace(/\banimate__\S+\b/g, "").trim();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  setupCanonicalRedirect();
  setupTOC(reduceMotion);
  setupContactBubble();
  setupReveal(reduceMotion);
  setupCopyToast();
  setupPrefetchProjets();
  setupServiceWorker();
  applyReducedMotion(reduceMotion);
});
