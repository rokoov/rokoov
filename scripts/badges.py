#!/usr/bin/env python3
# Builds full-colour stack badges into assets/badges (needs: npm i devicon simple-icons)
import base64, os, re, sys
from PIL import ImageFont

NM = sys.argv[1] if len(sys.argv) > 1 else "node_modules"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "badges")
FONT = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 13)

BADGES = {
    "luau": ("Luau", "dev:luau/luau-original"),
    "typescript": ("TypeScript", "dev:typescript/typescript-original"),
    "javascript": ("JavaScript", "dev:javascript/javascript-original"),
    "swift": ("Swift", "dev:swift/swift-original"),
    "python": ("Python", "dev:python/python-original"),
    "cpp": ("C/C++", "dev:cplusplus/cplusplus-original"),
    "react": ("React", "dev:react/react-original"),
    "nextjs": ("Next.js", "si:nextdotjs:ffffff"),
    "tailwind": ("Tailwind", "dev:tailwindcss/tailwindcss-original"),
    "medusa": ("Medusa", "si:medusa:ffffff"),
    "playwright": ("Playwright", "dev:playwright/playwright-original"),
    "figma": ("Figma", "dev:figma/figma-original"),
    "claude-code": ("Claude Code", "si:claude:D97757"),
    "mcp": ("MCP", "si:modelcontextprotocol:ffffff"),
    "cloudflare": ("Cloudflare", "dev:cloudflare/cloudflare-original"),
    "git": ("Git", "dev:git/git-original"),
    "github-actions": ("GitHub Actions", "dev:githubactions/githubactions-original"),
    "rojo": ("Rojo", None),
}


def icon(src):
    if src.startswith("dev:"):
        return open(f"{NM}/devicon/icons/{src[4:]}.svg").read()
    _, name, color = src.split(":")
    svg = open(f"{NM}/simple-icons/icons/{name}.svg").read()
    return re.sub(r"<title>.*?</title>", "", svg).replace("<svg ", f'<svg fill="#{color}" ', 1)


def badge(label, src):
    tw = FONT.getlength(label)
    ix = 7
    tx = ix + (19 if src else 0)
    w = round(tx + tw + 9)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="24" viewBox="0 0 {w} 24">',
             f'<rect width="{w}" height="24" rx="3" fill="#161b22"/>']
    if src:
        data = base64.b64encode(icon(src).encode()).decode()
        parts.append(f'<image x="{ix}" y="5" width="14" height="14" href="data:image/svg+xml;base64,{data}"/>')
    parts.append(f'<text x="{tx}" y="16.5" fill="#e6edf3" font-size="13" '
                 f'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">{label}</text></svg>')
    return "".join(parts)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for key, (label, src) in BADGES.items():
        open(os.path.join(OUT, f"{key}.svg"), "w").write(badge(label, src))
