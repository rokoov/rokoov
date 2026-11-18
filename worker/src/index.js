// Live README art: renders the contribution tree (or planet off-season) on each request
const USER = "rokoov";
const FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace";
const BG = "#0d1117";
const GREENS = ["#2d333b", "#0e4429", "#006d32", "#26a641", "#39d353"];
const RAMP = " .:;+x*o%#@";
const LANGS = [["Luau", "#00a2ff"], ["TypeScript", "#3178c6"], ["Swift", "#f05138"], ["Python", "#ffd43b"]];
const LEVELS = { NONE: 0, FIRST_QUARTILE: 1, SECOND_QUARTILE: 2, THIRD_QUARTILE: 3, FOURTH_QUARTILE: 4 };
const TTL = 60_000;

const QUERY = `query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{
totalContributions weeks{contributionDays{contributionLevel}}}}}}`;

let memo = null;

async function fetchData(token) {
  if (memo && Date.now() - memo.at < TTL) return memo.data;
  const res = await fetch("https://api.github.com/graphql", {
    method: "POST",
    headers: { Authorization: `bearer ${token}`, "Content-Type": "application/json", "User-Agent": "rokoov-readme" },
    body: JSON.stringify({ query: QUERY, variables: { u: USER } }),
  });
  const cal = (await res.json()).data.user.contributionsCollection.contributionCalendar;
  const data = {
    total: cal.totalContributions,
    weeks: cal.weeks.map((w) => w.contributionDays.map((d) => LEVELS[d.contributionLevel] ?? 0)),
  };
  memo = { at: Date.now(), data };
  return data;
}

function rng(seed) {
  return () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const pick = (r, arr) => arr[Math.floor(r() * arr.length)];
const uni = (r, a, b) => a + (b - a) * r();
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const grid = (rows, cols) => Array.from({ length: rows }, () => Array(cols).fill(null));

function render(g, cols, rows, cw, ch, W, H, d, css, extra, title) {
  const out = [
    `<svg xmlns="http://www.w3.org/2000/svg" width="${W * 4}" height="${H * 4}" viewBox="0 0 ${W} ${H}">`,
    "<style>", `text{font-family:${FONT};font-size:11.5px}`, ...css,
    ".t{fill:#e3b341;font-size:13px}.m{fill:#c9d1d9;font-size:12px}", "</style>",
    `<rect width="100%" height="100%" fill="${BG}"/>`,
  ];
  for (let y = 0; y < rows; y++) {
    const runs = [];
    let cur = null;
    for (let x = 0; x < cols; x++) {
      const c = g[y][x];
      const key = c && c[0] !== " " ? `${c[1]}|${c[2] ?? ""}` : null;
      if (key && cur && cur.key === key && cur.end === x) { cur.txt += c[0]; cur.end = x + 1; }
      else {
        if (cur) runs.push(cur);
        cur = key ? { key, col: c[1], cls: c[2], txt: c[0], end: x + 1, x0: x } : null;
      }
    }
    if (cur) runs.push(cur);
    for (const r of runs) {
      const cls = r.cls ? ` class="${r.cls}"` : "";
      out.push(`<text x="${(r.x0 * cw).toFixed(1)}" y="${((y + 1) * ch).toFixed(1)}" fill="${r.col}"${cls} xml:space="preserve">${esc(r.txt)}</text>`);
    }
  }
  out.push(...extra);
  const active = d.weeks.filter((w) => w.some(Boolean)).length;
  out.push(`<text x="${W / 2}" y="${rows * ch + 22}" text-anchor="middle" class="t">${title}</text>`);
  out.push(`<text x="${W / 2}" y="${rows * ch + 44}" text-anchor="middle" class="m">${d.total.toLocaleString("en-US")} contributions · ${active} active weeks</text>`);
  out.push("</svg>");
  return out.join("\n");
}

function tree(d) {
  const cols = 100, rows = 40, cw = 7, ch = 12, W = cols * cw, H = rows * ch + 56;
  const g = grid(rows, cols), r = rng(12);
  const days = d.weeks.flat();
  const cx = 50, top = 5, ground = top + 30;
  const tiers = [[top + 1, 9, 13], [top + 8, 10, 20], [top + 16, 11, 27]];

  for (let y = 0; y < rows; y++)
    for (let x = 0; x < cols; x++) {
      const dx = (x - cx) / 14, dy = (y - (top - 1)) / 2.2;
      if (dx * dx + dy * dy < 1 && r() < 0.55) g[y][x] = [pick(r, "·.:"), "#e3b341", "halo"];
    }

  let i = 0;
  for (const [y0, h, base] of tiers)
    for (let k = 0; k < h; k++) {
      const y = y0 + k, hw = Math.floor(2 + ((base - 2) * k) / (h - 1));
      for (let x = cx - hw; x <= cx + hw; x++) {
        const rel = (x - (cx - hw)) / (2 * hw + 1);
        const lvl = days.length ? days[(i * 7 + k) % days.length] : 0;
        i++;
        const lit = Math.max(0, Math.min(1, 1 - rel * 0.75 - (k / h) * 0.15 + uni(r, -0.3, 0.3)));
        const chr = RAMP[Math.min(RAMP.length - 1, 3 + Math.floor(lit * 6))];
        const col = lvl ? GREENS[Math.max(1, Math.min(4, lvl + (lit > 0.7 ? 1 : 0)))] : lit > 0.5 ? "#1a7f37" : "#0e4429";
        let cell = [chr, col, null];
        if (lvl >= 2 && r() < 0.13) cell = ["O", pick(r, ["#f85149", "#e3b341", "#58a6ff", "#db61a2"]), pick(r, ["b1", "b2", "b3"])];
        if (Math.abs(y - y0 - (x - cx + hw * 0.2) * 0.35 - h * 0.45) < 0.5 && r() < 0.9) cell = ["~", "#d29922", null];
        g[y][x] = cell;
      }
    }

  const star = [[-1, -1, "\\"], [0, -1, "|"], [1, -1, "/"], [-1, 0, "-"], [0, 0, "*"], [1, 0, "-"], [-1, 1, "/"], [0, 1, "|"], [1, 1, "\\"]];
  for (const [dx, dy, c] of star) g[top + dy][cx + dx * 2] = [c, "#f2cc60", "star"];
  g[top][cx] = ["★", "#ffe58f", "star"];

  for (let y = ground - 3; y < ground; y++)
    for (let x = cx - 3; x < cx + 4; x++) g[y][x] = ["#", x < cx + 1 ? "#8b5a2b" : "#5c3a1a", null];

  let gx = cx - 30;
  for (const [name, color] of LANGS) {
    const w = name.length + 4;
    const box = ["+" + "-".repeat(w - 2) + "+", "| " + name + " |", "+" + "-".repeat(w - 2) + "+"];
    if (gx + w > cx - 4 && gx < cx + 4) gx = cx + 5;
    box.forEach((line, ri) =>
      [...line].forEach((c, j) => { g[ground - 3 + ri][gx + j] = [c, color, ri === 1 && j > 1 && j < w - 2 ? "lang" : null]; }));
    gx += w + 2;
  }

  for (let y = ground; y < ground + 3; y++)
    for (let x = 0; x < cols; x++)
      if (r() < 0.75 - (y - ground) * 0.2) g[y][x] = [pick(r, ".:-~'"), y === ground ? "#c9d1d9" : "#6e7681", null];

  const flakes = [];
  for (let n = 0; n < 110; n++) {
    const x = uni(r, 0, W), y = uni(r, -24, 0);
    flakes.push(`<text x="${x.toFixed(0)}" y="${y.toFixed(0)}" class="f" style="animation-duration:${uni(r, 9, 18).toFixed(1)}s;` +
      `animation-delay:-${uni(r, 0, 18).toFixed(1)}s;fill-opacity:${uni(r, 0.35, 1).toFixed(2)}">${pick(r, "*·.+")}</text>`);
  }
  const css = [
    `@keyframes fall{from{transform:translate(0,0)}to{transform:translate(-30px,${H + 30}px)}}`,
    "@keyframes bl{0%,100%{opacity:1}50%{opacity:.25}}",
    ".f{fill:#fff;animation:fall linear infinite}",
    ".b1,.b2,.b3{font-weight:700}.b1{animation:bl 1.6s infinite}.b2{animation:bl 2.3s .5s infinite}.b3{animation:bl 3.1s 1s infinite}",
    ".star{animation:bl 2s infinite;font-weight:700}.halo{opacity:.55;animation:bl 4s infinite}.lang{font-weight:700}",
  ];
  return render(g, cols, rows, cw, ch, W, H, d, css, flakes, `merry christmas from @${USER}`);
}

function planet(d) {
  const cols = 100, rows = 44, cw = 7, ch = 12, W = cols * cw, H = rows * ch + 56;
  const g = grid(rows, cols), r = rng(42);
  const cx = cols / 2, cy = rows / 2, R = 13.5, rx = (R * ch) / cw;
  const weeks = d.weeks, light = [-0.55, -0.6, 0.58];
  const tilt = -0.32, rin = 1.45, rout = 2.05;

  for (let n = 0; n < 140; n++) {
    const x = Math.floor(r() * cols), y = Math.floor(r() * rows);
    g[y][x] = [pick(r, [..."..··*+✦"]), "#c9d1d9", pick(r, ["s1", "s2", "s3", "s4"])];
  }

  const ring = (front) => {
    for (let y = 0; y < rows; y++)
      for (let x = 0; x < cols; x++) {
        const px = (x - cx) / rx, py = (y - cy) / R;
        const ux = px * Math.cos(tilt) + py * Math.sin(tilt);
        const uy = -px * Math.sin(tilt) + py * Math.cos(tilt);
        const rr = Math.hypot(ux, uy / 0.17);
        if (rr > rin && rr < rout && uy > 0 === front) {
          const band = (rr - rin) / (rout - rin);
          const mid = band > 0.25 && band < 0.7;
          g[y][x] = [band > 0.85 ? "·" : mid ? "=" : "-", mid ? "#6e7681" : "#3d444d", null];
        }
      }
  };

  ring(false);
  for (let y = 0; y < rows; y++)
    for (let x = 0; x < cols; x++) {
      const nx = (x - cx) / rx, ny = (y - cy) / R, r2 = nx * nx + ny * ny;
      if (r2 > 1) { if (r2 < 1.12 && !g[y][x]) g[y][x] = ["·", "#388bfd", "glow"]; continue; }
      const nz = Math.sqrt(1 - r2);
      const lit = Math.max(0, nx * light[0] + ny * light[1] + nz * light[2]);
      const lon = Math.atan2(nx, nz), lat = Math.asin(Math.max(-1, Math.min(1, -ny)));
      const wk = ((Math.floor((lon / Math.PI + 0.5) * weeks.length) % weeks.length) + weeks.length) % weeks.length;
      const day = Math.floor((0.5 - (lat / Math.PI) * 1.35) * 7);
      const lvl = day >= 0 && day < 7 && day < weeks[wk].length ? weeks[wk][day] : 0;
      const shade = Math.min(RAMP.length - 1, 2 + Math.floor((0.15 + lit * 0.85) * (RAMP.length - 3)));
      if (lvl) {
        const col = GREENS[Math.min(4, Math.max(1, lvl + (lit > 0.65 ? 1 : 0) - (lit < 0.2 ? 1 : 0)))];
        g[y][x] = [RAMP[shade], col, lvl === 4 && r() < 0.35 ? "hot" : null];
      } else g[y][x] = [RAMP[shade], lit < 0.3 ? "#2d333b" : lit < 0.6 ? "#3d444d" : "#545d68", null];
    }
  ring(true);

  LANGS.forEach(([name, color], i) => {
    const a = [2.55, 0.35, 3.75, 5.45][i], rr = (rin + rout) / 2;
    const ux = rr * Math.cos(a), uy = rr * Math.sin(a) * 0.17;
    const px = ux * Math.cos(tilt) - uy * Math.sin(tilt), py = ux * Math.sin(tilt) + uy * Math.cos(tilt);
    const x = Math.floor(cx + px * rx) - Math.floor(name.length / 2), y = Math.floor(cy + py * R) + (uy > 0 ? 2 : -2);
    [...name].forEach((c, j) => { if (x + j >= 0 && x + j < cols && y >= 0 && y < rows) g[y][x + j] = [c, color, "lang"]; });
  });

  const css = [
    "@keyframes tw{0%,100%{opacity:1}50%{opacity:.15}}", "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.45}}",
    ".s1{animation:tw 3s infinite}.s2{animation:tw 4.5s 1s infinite}.s3{animation:tw 5.5s 2s infinite}.s4{opacity:.5}",
    ".hot{animation:pulse 2.4s infinite}.glow{opacity:.6}.lang{font-weight:700}",
  ];
  return render(g, cols, rows, cw, ch, W, H, d, css, [], `@${USER} · ${new Date().getUTCFullYear()}`);
}

export function isXmas(now = new Date()) {
  const m = now.getUTCMonth() + 1, day = now.getUTCDate();
  return m === 12 || (m === 11 && day >= 15) || (m === 1 && day <= 6);
}

export function art(data, theme) {
  return (theme ? theme === "xmas" : isXmas()) ? tree(data) : planet(data);
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (!["/", "/hero.svg"].includes(url.pathname)) return new Response("Not found", { status: 404 });
    try {
      const svg = art(await fetchData(env.GH_TOKEN), url.searchParams.get("theme"));
      return new Response(svg, {
        headers: { "content-type": "image/svg+xml; charset=utf-8", "cache-control": "no-cache, no-store, max-age=0, must-revalidate" },
      });
    } catch (e) {
      return new Response(`Error: ${e.message}`, { status: 502 });
    }
  },
};
