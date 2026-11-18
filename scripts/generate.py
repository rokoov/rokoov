#!/usr/bin/env python3
# Generates assets/hero.svg (christmas tree in Dec, planet otherwise) from GitHub contribution data
import json, math, os, random, sys, urllib.request
from datetime import date

USER = os.environ.get("GH_USER", "rokoov")
OUT = os.path.join(os.path.dirname(__file__), "..", "assets")
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"
BG = "#0d1117"
GREENS = ["#2d333b", "#0e4429", "#006d32", "#26a641", "#39d353"]
RAMP = " .:;+x*o%#@"
LANGS = [("Luau", "#00a2ff"), ("TypeScript", "#3178c6"), ("Swift", "#f05138"), ("Python", "#ffd43b")]

QUERY = """query($u:String!){user(login:$u){
contributionsCollection{totalCommitContributions totalPullRequestContributions totalIssueContributions
contributionCalendar{totalContributions weeks{contributionDays{contributionCount contributionLevel}}}}
repositories(first:100,ownerAffiliations:OWNER,isFork:false){totalCount nodes{stargazerCount
languages(first:5,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}}}}"""

LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


def fetch():
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"u": USER}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GH_TOKEN']}", "Content-Type": "application/json"})
    u = json.load(urllib.request.urlopen(req))["data"]["user"]
    cc = u["contributionsCollection"]
    weeks = [[LEVELS[d["contributionLevel"]] for d in w["contributionDays"]] for w in cc["contributionCalendar"]["weeks"]]
    langs = {}
    for r in u["repositories"]["nodes"]:
        for e in r["languages"]["edges"]:
            n = e["node"]["name"]
            langs.setdefault(n, [0, e["node"]["color"] or "#8b949e"])[0] += e["size"]
    return {
        "weeks": weeks,
        "total": cc["contributionCalendar"]["totalContributions"],
        "commits": cc["totalCommitContributions"],
        "prs": cc["totalPullRequestContributions"],
        "issues": cc["totalIssueContributions"],
        "repos": u["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
        "langs": sorted(([k, v[0], v[1]] for k, v in langs.items()), key=lambda x: -x[1])[:6],
    }


def sample():
    rnd = random.Random(7)
    weeks = [[min(4, int(rnd.random() ** 1.6 * 5 * (0.4 + w / 60))) if rnd.random() > 0.3 else 0 for _ in range(7)] for w in range(53)]
    return {"weeks": weeks, "total": 1284, "commits": 1103, "prs": 41, "issues": 12, "repos": 24, "stars": 18,
            "langs": [["Luau", 61, "#00a2ff"], ["TypeScript", 19, "#3178c6"], ["Swift", 9, "#f05138"],
                      ["JavaScript", 6, "#f1e05a"], ["Python", 3, "#3572a5"], ["CSS", 2, "#663399"]]}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def planet(d):
    cols, rows, cw, ch = 100, 44, 7.0, 12.0
    W, H = cols * cw, rows * ch + 56
    grid = [[None] * cols for _ in range(rows)]
    rnd = random.Random(42)
    cx, cy, R = cols / 2, rows / 2, 13.5
    rx = R * ch / cw
    weeks = d["weeks"]
    light = (-0.55, -0.6, 0.58)

    stars = []
    for _ in range(140):
        x, y = rnd.randrange(cols), rnd.randrange(rows)
        stars.append((x, y, rnd.choice("..··*+✦"), rnd.choice(["s1", "s2", "s3", "s4"])))
    for x, y, c, cls in stars:
        grid[y][x] = (c, "#c9d1d9", cls)

    tilt, ring_in, ring_out = -0.32, 1.45, 2.05

    def ring(front):
        for y in range(rows):
            for x in range(cols):
                px, py = (x - cx) / rx, (y - cy) / R
                ux = px * math.cos(tilt) + py * math.sin(tilt)
                uy = -px * math.sin(tilt) + py * math.cos(tilt)
                r = math.hypot(ux, uy / 0.17)
                if ring_in < r < ring_out and (uy > 0) == front:
                    band = (r - ring_in) / (ring_out - ring_in)
                    c = "=" if 0.25 < band < 0.7 else "-"
                    if band > 0.85: c = "·"
                    grid[y][x] = (c, "#6e7681" if 0.25 < band < 0.7 else "#3d444d", None)

    ring(False)
    for y in range(rows):
        for x in range(cols):
            nx, ny = (x - cx) / rx, (y - cy) / R
            r2 = nx * nx + ny * ny
            if r2 > 1:
                if r2 < 1.12 and grid[y][x] is None:
                    grid[y][x] = ("·", "#388bfd", "glow")
                continue
            nz = math.sqrt(1 - r2)
            lit = max(0.0, nx * light[0] + ny * light[1] + nz * light[2])
            lon = math.atan2(nx, nz)
            lat = math.asin(max(-1, min(1, -ny)))
            wk = int((lon / math.pi + 0.5) * len(weeks)) % len(weeks)
            day = int((0.5 - lat / math.pi * 1.35) * 7)
            lvl = weeks[wk][day] if 0 <= day < 7 and day < len(weeks[wk]) else 0
            shade = min(len(RAMP) - 1, 2 + int((0.15 + lit * 0.85) * (len(RAMP) - 3)))
            if lvl:
                col = GREENS[min(4, max(1, lvl + (1 if lit > 0.65 else 0) - (1 if lit < 0.2 else 0)))]
                cls = "hot" if lvl == 4 and rnd.random() < 0.35 else None
            else:
                col = "#2d333b" if lit < 0.3 else ("#3d444d" if lit < 0.6 else "#545d68")
                cls = None
            grid[y][x] = (RAMP[shade], col, cls)
    ring(True)

    for i, (name, color) in enumerate(LANGS):
        a = [2.55, 0.35, 3.75, 5.45][i]
        rr = (ring_in + ring_out) / 2
        ux, uy = rr * math.cos(a), rr * math.sin(a) * 0.17
        px = ux * math.cos(tilt) - uy * math.sin(tilt)
        py = ux * math.sin(tilt) + uy * math.cos(tilt)
        x, y = int(cx + px * rx) - len(name) // 2, int(cy + py * R) + (2 if uy > 0 else -2)
        for j, c in enumerate(name):
            if 0 <= x + j < cols and 0 <= y < rows:
                grid[y][x + j] = (c, color, "lang")

    css = ["@keyframes tw{0%,100%{opacity:1}50%{opacity:.15}}",
           "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.45}}",
           ".s1{animation:tw 3s infinite}.s2{animation:tw 4.5s 1s infinite}.s3{animation:tw 5.5s 2s infinite}.s4{opacity:.5}",
           ".hot{animation:pulse 2.4s infinite}.glow{opacity:.6}.lang{font-weight:700}"]
    return render(grid, cols, rows, cw, ch, W, H, d, css, [], f"@{USER} · {date.today().year}")


def render(grid, cols, rows, cw, ch, W, H, d, css, extra, title):
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W * 2:.0f}" height="{H * 2:.0f}" viewBox="0 0 {W:.0f} {H:.0f}">',
           "<style>",
           f"text{{font-family:{FONT};font-size:11.5px}}",
           *css,
           ".t{fill:#e3b341;font-size:13px}.m{fill:#c9d1d9;font-size:12px}",
           "</style>",
           f'<rect width="100%" height="100%" fill="{BG}"/>']
    for y in range(rows):
        runs, cur = [], None
        for x in range(cols):
            g = grid[y][x]
            key = (g[1], g[2]) if g and g[0] != " " else None
            if key and cur and cur[0] == key and cur[2] == x:
                cur[1] += g[0]; cur[2] = x + 1
            else:
                if cur: runs.append(cur)
                cur = [key, g[0], x + 1, x] if key else None
        if cur: runs.append(cur)
        for (col, cls), txt, _, x0 in runs:
            c = f' class="{cls}"' if cls else ""
            out.append(f'<text x="{x0 * cw:.1f}" y="{(y + 1) * ch:.1f}" fill="{col}"{c} xml:space="preserve">{esc(txt)}</text>')
    out += extra
    active = sum(1 for w in d["weeks"] if any(w))
    out.append(f'<text x="{W / 2}" y="{rows * ch + 22}" text-anchor="middle" class="t">{title}</text>')
    out.append(f'<text x="{W / 2}" y="{rows * ch + 44}" text-anchor="middle" class="m">{d["total"]:,} contributions · {active} active weeks</text>')
    out.append("</svg>")
    return "\n".join(out)


def tree(d):
    cols, rows, cw, ch = 100, 40, 7.0, 12.0
    W, H = cols * cw, rows * ch + 56
    grid = [[None] * cols for _ in range(rows)]
    rnd = random.Random(12)
    weeks = d["weeks"]
    days = [l for w in weeks for l in w]
    cx, top = cols // 2, 5
    tiers = [(top + 1, 9, 13), (top + 8, 10, 20), (top + 16, 11, 27)]
    ground = top + 30

    for y in range(rows):
        for x in range(cols):
            dx, dy = (x - cx) / 14, (y - (top - 1)) / 2.2
            if dx * dx + dy * dy < 1 and rnd.random() < 0.55:
                grid[y][x] = (rnd.choice("·.:"), "#e3b341", "halo")

    i = 0
    for y0, h, base in tiers:
        for k in range(h):
            y = y0 + k
            hw = int(2 + (base - 2) * k / (h - 1))
            for x in range(cx - hw, cx + hw + 1):
                rel = (x - (cx - hw)) / (2 * hw + 1)
                lvl = days[(i * 7 + k) % len(days)] if days else 0
                i += 1
                lit = max(0, min(1, 1 - rel * 0.75 - k / h * 0.15 + rnd.uniform(-0.3, 0.3)))
                ch_ = RAMP[min(len(RAMP) - 1, 3 + int(lit * 6))]
                col = GREENS[max(1, min(4, lvl + (1 if lit > 0.7 else 0)))] if lvl else ("#1a7f37" if lit > 0.5 else "#0e4429")
                g = (ch_, col, None)
                if lvl >= 2 and rnd.random() < 0.13:
                    g = ("O", rnd.choice(["#f85149", "#e3b341", "#58a6ff", "#db61a2"]), rnd.choice(["b1", "b2", "b3"]))
                if abs((y - y0) - (x - cx + hw * 0.2) * 0.35 - h * 0.45) < 0.5 and rnd.random() < 0.9:
                    g = ("~", "#d29922", None)
                grid[y][x] = g

    for c, (dx, dy) in zip("\\|/-*-/|\\", [(-1, -1), (0, -1), (1, -1), (-1, 0), (0, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]):
        grid[top + dy][cx + dx * 2] = (c, "#f2cc60", "star")
    grid[top][cx] = ("★", "#ffe58f", "star")

    for y in range(ground - 3, ground):
        for x in range(cx - 3, cx + 4):
            grid[y][x] = ("#", "#8b5a2b" if x < cx + 1 else "#5c3a1a", None)

    gx = cx - 30
    for name, color in LANGS:
        w = len(name) + 4
        box = ["+" + "-" * (w - 2) + "+", "| " + name + " |", "+" + "-" * (w - 2) + "+"]
        if gx + w > cx - 4 and gx < cx + 4:
            gx = cx + 5
        for r, line in enumerate(box):
            for j, c in enumerate(line):
                grid[ground - 3 + r][gx + j] = (c, color, "lang" if r == 1 and 1 < j < w - 2 else None)
        gx += w + 2

    for y in range(ground, ground + 3):
        for x in range(cols):
            if rnd.random() < 0.75 - (y - ground) * 0.2:
                grid[y][x] = (rnd.choice(".:-~'"), "#c9d1d9" if y == ground else "#6e7681", None)

    flakes = []
    for _ in range(110):
        x, y = rnd.uniform(0, W), rnd.uniform(-24, 0)
        flakes.append(f'<text x="{x:.0f}" y="{y:.0f}" class="f" style="animation-duration:{rnd.uniform(9, 18):.1f}s;'
                      f'animation-delay:-{rnd.uniform(0, 18):.1f}s;fill-opacity:{rnd.uniform(.35, 1):.2f}">{rnd.choice("*·.+")}</text>')

    css = ["@keyframes fall{from{transform:translate(0,0)}to{transform:translate(-30px,%dpx)}}" % (H + 30),
           "@keyframes bl{0%%,100%%{opacity:1}50%%{opacity:.25}}",
           ".f{fill:#fff;animation:fall linear infinite}",
           ".b1,.b2,.b3{font-weight:700}.b1{animation:bl 1.6s infinite}.b2{animation:bl 2.3s .5s infinite}.b3{animation:bl 3.1s 1s infinite}",
           ".star{animation:bl 2s infinite;font-weight:700}.halo{opacity:.55;animation:bl 4s infinite}.lang{font-weight:700}"]
    return render(grid, cols, rows, cw, ch, W, H, d, css, flakes, f"merry christmas from @{USER}")


if __name__ == "__main__":
    data = sample() if "--sample" in sys.argv else fetch()
    os.makedirs(OUT, exist_ok=True)
    t = date.today()
    xmas = "--xmas" in sys.argv or t.month == 12 or (t.month == 11 and t.day >= 15) or (t.month == 1 and t.day <= 6)
    if "--planet" in sys.argv: xmas = False
    open(os.path.join(OUT, "hero.svg"), "w").write(tree(data) if xmas else planet(data))
