// Renders a guide's markdown (the single source of truth agents also read) into the page,
// with Mermaid diagrams, highlighted code, a contents list, and copy buttons.
(function () {
  const src = document.body.dataset.src;
  const article = document.getElementById("doc");
  const toc = document.getElementById("toc-links");
  const mdUrl = new URL(src, location.href).href;
  const toast = document.getElementById("toast");

  function say(text) {
    toast.textContent = text;
    toast.classList.add("on");
    setTimeout(() => toast.classList.remove("on"), 1600);
  }

  function copy(text, done) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => say(done), () => say("Copy failed. Select and copy by hand."));
    } else {
      say("Copy failed. Select and copy by hand.");
    }
  }

  document.querySelectorAll("[data-md-url]").forEach((el) => { el.textContent = mdUrl; });
  document.querySelectorAll("[data-copy-md]").forEach((b) => {
    b.addEventListener("click", () => copy(mdUrl, "Link copied. Paste it into your agent."));
  });

  function escapeHtml(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function slug(text) {
    return text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  }

  marked.use({
    gfm: true,
    renderer: {
      code(code, lang) {
        if ((lang || "").trim() === "mermaid") {
          return '<div class="diagram"><pre class="mermaid">' + escapeHtml(code) + "</pre></div>";
        }
        const language = (lang || "").trim().split(/\s+/)[0];
        let body = escapeHtml(code);
        if (window.hljs) {
          try {
            body = language && hljs.getLanguage(language)
              ? hljs.highlight(code, { language }).value
              : hljs.highlightAuto(code).value;
          } catch (e) {}
        }
        return '<pre><code class="hljs">' + body + "</code></pre>";
      },
      table(header, body) {
        return '<div class="table-wrap"><table><thead>' + header + "</thead><tbody>" + body + "</tbody></table></div>";
      }
    }
  });

  fetch(src)
    .then((r) => { if (!r.ok) throw new Error(r.status); return r.text(); })
    .then((md) => {
      article.innerHTML = marked.parse(md);

      // Guides link to each other as .md for agents; people get the web page.
      article.querySelectorAll('a[href$=".md"]').forEach((a) => {
        const href = a.getAttribute("href");
        if (!/^https?:/.test(href)) a.setAttribute("href", href.replace(/\.md$/, ".html"));
      });
      article.querySelectorAll("a[href^='http']").forEach((a) => { a.target = "_blank"; a.rel = "noopener"; });

      const used = {};
      article.querySelectorAll("h2, h3").forEach((h) => {
        let id = slug(h.textContent) || "section";
        if (used[id]) id += "-" + (++used[id]); else used[id] = 1;
        h.id = id;
        if (h.tagName === "H2") {
          const a = document.createElement("a");
          a.href = "#" + id;
          a.textContent = h.textContent;
          toc.appendChild(a);
        }
      });

      article.querySelectorAll("pre:not(.mermaid)").forEach((pre) => {
        const b = document.createElement("button");
        b.className = "copy";
        b.type = "button";
        b.textContent = "Copy";
        b.addEventListener("click", () => copy(pre.innerText.replace(/\nCopy$/, ""), "Copied"));
        pre.appendChild(b);
      });

      if (window.mermaid) {
        mermaid.initialize({
          startOnLoad: false,
          securityLevel: "strict",
          theme: "base",
          flowchart: { htmlLabels: true, curve: "basis" },
          themeVariables: {
            fontFamily: '"IBM Plex Sans", "Segoe UI", sans-serif',
            fontSize: "15px",
            primaryColor: "#e8f0fe",
            primaryBorderColor: "#1a73e8",
            primaryTextColor: "#0f1115",
            lineColor: "#5f6368",
            secondaryColor: "#e6f4ea",
            tertiaryColor: "#fef7e0",
            actorBkg: "#f3e8fd",
            actorBorder: "#9334e6",
            noteBkgColor: "#fef7e0",
            noteBorderColor: "#f9ab00"
          }
        });
        // Measure labels with the real font, or the boxes come out too narrow.
        const fontsReady = document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve();
        fontsReady.then(() => mermaid.run({ querySelector: "pre.mermaid" })).catch(() => {});
      }

      const heads = [...article.querySelectorAll("h2")];
      const links = [...toc.querySelectorAll("a")];
      const spy = () => {
        let cur = 0;
        heads.forEach((h, i) => { if (h.getBoundingClientRect().top < 120) cur = i; });
        links.forEach((a, i) => a.classList.toggle("on", i === cur));
      };
      addEventListener("scroll", spy, { passive: true });
      spy();
      if (location.hash) {
        const t = document.getElementById(location.hash.slice(1));
        if (t) t.scrollIntoView();
      }
    })
    .catch(() => {
      article.innerHTML = '<p class="status">Could not load the guide. Open <a href="' + src + '">' + src + "</a> directly.</p>";
    });
})();
