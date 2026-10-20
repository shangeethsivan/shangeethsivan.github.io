/**
 * Edge adapter for the two checks GitHub Pages cannot answer:
 * Link response headers, and Accept: text/markdown on the homepage.
 *
 * Attach this worker to the shravz.dev route in front of the Pages origin.
 * The homepage markdown body is /llms.txt.
 */
export default {
  async fetch(request) {
    const url = new URL(request.url);
    const accept = request.headers.get("accept") || "";
    const wantsMarkdown = accept.includes("text/markdown");
    const isHome = url.pathname === "/" || url.pathname === "/index.html";

    if (wantsMarkdown && isHome) {
      const markdownUrl = new URL("/llms.txt", url);
      const markdown = await fetch(markdownUrl, request);
      const body = await markdown.arrayBuffer();
      const tokens = Math.ceil(new TextDecoder().decode(body).length / 4);
      return new Response(body, {
        status: markdown.status,
        headers: {
          "content-type": "text/markdown; charset=utf-8",
          "x-markdown-tokens": String(tokens),
          "vary": "Accept",
          "access-control-allow-origin": "*",
          "link": linkHeader(),
        },
      });
    }

    const response = await fetch(request);
    const headers = new Headers(response.headers);
    const existing = headers.get("link");
    headers.set("link", existing ? `${existing}, ${linkHeader()}` : linkHeader());
    headers.set("access-control-allow-origin", "*");
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers,
    });
  },
};

function linkHeader() {
  return [
    '</.well-known/ai-catalog.json>; rel="describedby"',
    '</llms.txt>; rel="describedby"',
    '</sitemap.xml>; rel="sitemap"',
    '</.well-known/agent-skills/index.json>; rel="describedby"',
  ].join(", ");
}
