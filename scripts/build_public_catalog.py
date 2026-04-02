from __future__ import annotations

import json
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HUB_CONFIG = ROOT / "hub.json"
SKILLS_DIR = ROOT / "skills"
PACKS_DIR = ROOT / "packs"
PUBLIC_DIR = ROOT / "public"


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def build_items() -> tuple[dict, list[dict], list[dict]]:
    hub = load_json(HUB_CONFIG)
    packs = [load_json(path) for path in sorted(PACKS_DIR.glob("*.json"))]
    items: list[dict] = []
    plugin = hub["defaults"]["plugin"]
    plugin_description = f"{hub['owner']['name']}'s generated skill catalog."

    for manifest_path in sorted(SKILLS_DIR.glob("*/skill.json")):
        item = load_json(manifest_path)
        item["plugin"] = plugin
        item["pluginDescription"] = plugin_description
        item["path"] = f"skills/{item['name']}"
        items.append(item)

    return hub, items, packs


def render_html(hub: dict, items: list[dict], packs: list[dict]) -> str:
    items_json = json.dumps(items, ensure_ascii=False)
    packs_json = json.dumps(packs, ensure_ascii=False)
    title = escape(f"{hub['owner']['name']} Skills Hub")
    clone_url = escape(hub["repository"]["cloneUrl"])
    web_url = escape(hub["repository"]["webUrl"])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      --bg: #f5f2ea;
      --panel: #fffdf8;
      --ink: #1b2230;
      --muted: #596577;
      --line: #d7d1c4;
      --accent: #0e6b5c;
      --accent-soft: #dff4ee;
      --tag: #ece8de;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", "PingFang SC", "Noto Sans SC", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(14,107,92,0.14), transparent 28%),
        linear-gradient(180deg, #faf8f2, var(--bg));
    }}
    main {{ max-width: 1080px; margin: 0 auto; padding: 32px 20px 60px; }}
    .hero, .toolbar, .grid {{ display: grid; gap: 16px; }}
    .hero {{ grid-template-columns: 1.35fr 1fr; margin-bottom: 24px; }}
    .toolbar {{ grid-template-columns: 1.4fr 1fr 1fr; margin-bottom: 18px; }}
    .panel, .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 22px;
      padding: 20px;
      box-shadow: 0 14px 32px rgba(0,0,0,0.04);
    }}
    h1 {{ margin: 0 0 10px; font-size: 40px; line-height: 1.05; }}
    .lead {{ color: var(--muted); margin: 0 0 20px; line-height: 1.6; }}
    .stat {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--line); }}
    .stat:last-child {{ border-bottom: 0; }}
    .stat-label {{ color: var(--muted); font-size: 13px; }}
    .stat-value {{ color: var(--accent); font-weight: 700; }}
    input, select {{
      width: 100%;
      padding: 12px 14px;
      border: 1px solid var(--line);
      border-radius: 12px;
      background: var(--panel);
      color: var(--ink);
      font-size: 14px;
    }}
    .grid {{ grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }}
    .eyebrow {{ color: var(--accent); font-size: 12px; font-weight: 700; text-transform: uppercase; }}
    .title {{ margin: 8px 0; font-size: 20px; font-weight: 700; }}
    .desc {{ color: var(--muted); line-height: 1.6; min-height: 52px; }}
    .meta {{ margin-top: 12px; display: flex; flex-wrap: wrap; gap: 8px; }}
    .chip {{ padding: 6px 10px; background: var(--tag); border-radius: 999px; font-size: 12px; }}
    pre {{
      margin: 0;
      overflow: auto;
      padding: 14px;
      border-radius: 16px;
      background: #1f2430;
      color: #f5f7fb;
      font-size: 12px;
      line-height: 1.5;
    }}
    .callout {{ margin-top: 14px; padding: 12px; border-radius: 14px; background: var(--accent-soft); font-size: 13px; }}
    .empty {{
      display: none;
      margin-top: 20px;
      padding: 18px;
      border-radius: 16px;
      border: 1px dashed var(--line);
      background: var(--panel);
      color: var(--muted);
    }}
    a {{ color: var(--accent); }}
    @media (max-width: 800px) {{
      .hero, .toolbar {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 30px; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div class="panel">
        <h1>{title}</h1>
        <p class="lead">A small public skills source maintained by {escape(hub['owner']['name'])}. The catalog is generated from the canonical files under <code>skills/</code> and <code>packs/</code>.</p>
        <div class="grid">
          <div>
            <div class="eyebrow">GitHub</div>
            <pre>{clone_url}</pre>
          </div>
          <div>
            <div class="eyebrow">Install For Codex</div>
            <pre>npx skills add {clone_url} --agent codex -g --yes</pre>
          </div>
        </div>
      </div>
      <div class="panel">
        <div class="stat"><div class="stat-label">Owner</div><div class="stat-value">{escape(hub['owner']['name'])}</div></div>
        <div class="stat"><div class="stat-label">Repository</div><div class="stat-value">{escape(hub['repository']['name'])}</div></div>
        <div class="stat"><div class="stat-label">Pack Count</div><div class="stat-value">{len(packs)}</div></div>
        <div class="stat"><div class="stat-label">Skill Count</div><div class="stat-value" id="skill-count"></div></div>
        <div class="stat"><div class="stat-label">Web</div><div class="stat-value"><a href="{web_url}">Open</a></div></div>
      </div>
    </section>
    <section class="toolbar">
      <input id="query" type="search" placeholder="Search by name, title, description, tag or owner">
      <select id="agent"><option value="">All agents</option></select>
      <select id="pack"><option value="">All packs</option></select>
    </section>
    <section id="cards" class="grid"></section>
    <section id="empty" class="empty">No matching skills.</section>
  </main>
  <script>
    const items = {items_json};
    const packs = {packs_json};
    const cards = document.getElementById("cards");
    const empty = document.getElementById("empty");
    const query = document.getElementById("query");
    const agent = document.getElementById("agent");
    const pack = document.getElementById("pack");
    const skillCount = document.getElementById("skill-count");

    function escapeHtml(text) {{
      return String(text)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }}

    function populateFilters() {{
      const agents = [...new Set(items.flatMap(item => item.agents))].sort();
      for (const value of agents) {{
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        agent.appendChild(option);
      }}
      for (const item of packs) {{
        const option = document.createElement("option");
        option.value = item.name;
        option.textContent = `${{item.name}} (${{item.skills.length}} skills)`;
        pack.appendChild(option);
      }}
    }}

    function render(list) {{
      skillCount.textContent = String(list.length);
      cards.innerHTML = list.map(item => `
        <article class="card">
          <div class="eyebrow">${{escapeHtml(item.plugin)}}</div>
          <div class="title">${{escapeHtml(item.title)}}</div>
          <div class="desc">${{escapeHtml(item.description)}}</div>
          <div class="meta">
            <span class="chip">skill: ${{escapeHtml(item.name)}}</span>
            <span class="chip">pack: ${{escapeHtml(item.pack)}}</span>
            <span class="chip">status: ${{escapeHtml(item.status)}}</span>
            ${{item.agents.map(value => `<span class="chip">${{escapeHtml(value)}}</span>`).join("")}}
            ${{item.tags.map(value => `<span class="chip">${{escapeHtml(value)}}</span>`).join("")}}
          </div>
          <div class="callout">owner: ${{escapeHtml(item.owners.join(", "))}}<br>path: ${{escapeHtml(item.path)}}</div>
        </article>
      `).join("");
      empty.style.display = list.length === 0 ? "block" : "none";
    }}

    function filter() {{
      const q = query.value.trim().toLowerCase();
      const agentValue = agent.value;
      const packValue = pack.value;
      const list = items.filter(item => {{
        const haystack = [item.name, item.title, item.description, item.pack, ...item.tags, ...item.owners, ...item.agents].join(" ").toLowerCase();
        return (!q || haystack.includes(q)) && (!agentValue || item.agents.includes(agentValue)) && (!packValue || item.pack === packValue);
      }});
      render(list);
    }}

    query.addEventListener("input", filter);
    agent.addEventListener("change", filter);
    pack.addEventListener("change", filter);
    populateFilters();
    render(items);
  </script>
</body>
</html>
"""


def main() -> int:
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    hub, items, packs = build_items()
    (PUBLIC_DIR / "index.json").write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (PUBLIC_DIR / "packs.json").write_text(json.dumps(packs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (PUBLIC_DIR / "index.html").write_text(render_html(hub, items, packs), encoding="utf-8")
    print(f"Built catalog with {len(items)} skill(s) and {len(packs)} pack(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
