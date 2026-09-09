# -*- coding: utf-8 -*-
"""
海参.cn 静态站生成器（GitHub Pages 兼容版）
用法：python build.py
特性：全部站内链接为相对路径，无论部署在域名根路径还是 github.io 仓库子路径均可正常工作
"""
import os
import re
import html as htmllib
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content")
OUTPUT = os.path.join(ROOT, "output")

SITE = {
    "name": "海参.cn",
    "full_name": "海参.cn · 海参知识科普网",
    "slogan": "懂海参，不踩坑",
    "desc": "海参知识科普网：海参百科、选购避坑、泡发教程与家常做法，用内容帮你明明白白吃海参。",
    # 部署后替换为实际对外域名（如 GitHub Pages 自定义域名或 github.io 地址）
    "url": "https://海参.cn",
}

CATS = {
    "baike": {"title": "海参百科", "file": "baike.html", "desc": "认识海参：种类、产地、营养与产品形态。"},
    "xuangou": {"title": "选购指南", "file": "xuangou.html", "desc": "怎么挑、怎么避坑：干参、即食、礼盒选购实操。"},
    "paofa": {"title": "泡发与食用", "file": "paofa.html", "desc": "泡发全流程、保存方法与经典家常做法。"},
}

def parse_md(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    meta, body = {}, m.group(2) if m else text
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    meta["slug"] = os.path.splitext(os.path.basename(path))[0]
    meta["body"] = body
    return meta

def inline(s):
    s = htmllib.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s

def md_to_html(md):
    lines = md.splitlines()
    out, i = [], 0
    def flush_par(buf):
        if buf:
            out.append("<p>%s</p>" % inline(" ".join(buf)))
    par = []
    while i < len(lines):
        line = lines[i]
        st = line.strip()
        if not st:
            flush_par(par); par = []; i += 1; continue
        if st.startswith("### "):
            flush_par(par); par = []; out.append("<h3>%s</h3>" % inline(st[4:])); i += 1; continue
        if st.startswith("## "):
            flush_par(par); par = []; out.append("<h2>%s</h2>" % inline(st[3:])); i += 1; continue
        if st == "---":
            flush_par(par); par = []; out.append("<hr/>"); i += 1; continue
        if st.startswith("> "):
            flush_par(par); par = []
            quote = []
            while i < len(lines) and lines[i].strip().startswith("> "):
                quote.append(lines[i].strip()[2:]); i += 1
            out.append("<blockquote><p>%s</p></blockquote>" % inline(" ".join(quote))); continue
        if st.startswith("|"):
            flush_par(par); par = []
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(cells); i += 1
            if len(rows) >= 2 and all(re.fullmatch(r"[-: ]+", c or "-") for c in rows[1]):
                head, body = rows[0], rows[2:]
            else:
                head, body = None, rows
            t = ["<table>"]
            if head:
                t.append("<thead><tr>" + "".join("<th>%s</th>" % inline(c) for c in head) + "</tr></thead>")
            t.append("<tbody>")
            for r in body:
                t.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>")
            t.append("</tbody></table>")
            out.append("".join(t)); continue
        if re.match(r"^[-*] ", st) or re.match(r"^\d+\. ", st):
            flush_par(par); par = []
            ol = bool(re.match(r"^\d+\. ", st))
            items = []
            while i < len(lines) and (re.match(r"^[-*] ", lines[i].strip()) or re.match(r"^\d+\. ", lines[i].strip())):
                item = re.sub(r"^([-*]|\d+\.) ", "", lines[i].strip())
                items.append("<li>%s</li>" % inline(item)); i += 1
            tag = "ol" if ol else "ul"
            out.append("<%s>%s</%s>" % (tag, "".join(items), tag)); continue
        par.append(st); i += 1
    flush_par(par)
    return "\n".join(out)

def esc(s):
    return htmllib.escape(s or "")

def page_shell(title, desc, body, canonical="", depth=0):
    p = "" if depth == 0 else "../"   # 相对路径前缀
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}"/>
<link rel="canonical" href="{SITE['url']}/{canonical}"/>
<link rel="stylesheet" href="{p}css/style.css"/>
</head>
<body>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="logo" href="{p}index.html">海参<span class="logo-dot">.cn</span></a>
    <nav class="nav">
      <a href="{p}index.html">首页</a>
      <a href="{p}baike.html">海参百科</a>
      <a href="{p}xuangou.html">选购指南</a>
      <a href="{p}paofa.html">泡发与食用</a>
      <a href="{p}about.html">关于本站</a>
    </nav>
  </div>
</header>
<main class="wrap">
{body}
</main>
<footer class="site-footer">
  <div class="wrap">
    <p>海参.cn —— 海参知识科普网站。本站内容为食品科普与经验分享，不构成医疗建议；特殊人群请遵医嘱。</p>
    <p><a href="{p}disclaimer.html">免责声明</a> · <a href="{p}about.html">关于本站</a></p>
    <p class="copy">© {datetime.now().year} 海参.cn</p>
  </div>
</footer>
</body>
</html>"""

def article_card(a, depth=0):
    p = "" if depth == 0 else "../"
    return f"""<article class="card">
  <h3><a href="{p}articles/{a['slug']}.html">{esc(a['title'])}</a></h3>
  <p class="meta">{esc(a.get('date',''))} · {esc(CATS[a['category']]['title'] if a['category'] in CATS else '')}</p>
  <p class="desc">{esc(a.get('description',''))}</p>
</article>"""

def build():
    files = sorted(f for f in os.listdir(CONTENT) if f.endswith(".md"))
    arts, pages = [], {}
    for f in files:
        a = parse_md(os.path.join(CONTENT, f))
        if a.get("category") == "page":
            pages[a["slug"]] = a
        else:
            arts.append(a)
    arts.sort(key=lambda x: (x.get("date", ""), x["slug"]), reverse=True)

    os.makedirs(os.path.join(OUTPUT, "articles"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT, "css"), exist_ok=True)

    # 文章页（depth=1）
    for a in arts:
        cat = CATS[a["category"]]
        related = [x for x in arts if x["category"] == a["category"] and x["slug"] != a["slug"]][:3]
        rel_html = ""
        if related:
            rel_html = '<section class="related"><h2>相关文章</h2><ul class="rel-list">' + "".join(
                f'<li><a href="../articles/{r["slug"]}.html">{esc(r["title"])}</a></li>' for r in related) + "</ul></section>"
        body = f"""<nav class="crumb"><a href="../index.html">首页</a> / <a href="../{cat['file']}">{cat['title']}</a> / <span>{esc(a['title'])}</span></nav>
<article class="post">
  <h1>{esc(a['title'])}</h1>
  <p class="post-meta">{esc(a.get('date',''))} · {cat['title']} · 阅读约 4 分钟</p>
  <div class="post-body">
{md_to_html(a["body"])}
  </div>
</article>
{rel_html}"""
        with open(os.path.join(OUTPUT, "articles", a["slug"] + ".html"), "w", encoding="utf-8") as f:
            f.write(page_shell(f"{a['title']} - {cat['title']} | {SITE['name']}", a.get("description", ""), body,
                               "articles/" + a["slug"] + ".html", depth=1))

    # 首页（depth=0）
    sections = []
    for ck, cat in CATS.items():
        items = [a for a in arts if a["category"] == ck]
        cards = "".join(article_card(a) for a in items)
        sections.append(f"""<section class="cat-sec" id="{ck}">
  <div class="sec-head"><h2>{cat['title']}</h2><p>{cat['desc']}</p><a class="more" href="{cat['file']}">查看全部 →</a></div>
  <div class="grid">{cards}</div>
</section>""")
    home_body = f"""<section class="hero">
  <h1>{esc(SITE['slogan'])}</h1>
  <p>{esc(SITE['desc'])}</p>
  <p class="hero-tags"><span>海参百科</span><span>选购避坑</span><span>泡发教程</span><span>家常做法</span></p>
</section>
{"".join(sections)}"""
    with open(os.path.join(OUTPUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(page_shell(SITE["full_name"] + " —— " + SITE["slogan"], SITE["desc"], home_body, "index.html"))

    # 栏目页（depth=0）
    for ck, cat in CATS.items():
        items = [a for a in arts if a["category"] == ck]
        cards = "".join(article_card(a) for a in items)
        body = f"""<nav class="crumb"><a href="index.html">首页</a> / <span>{cat['title']}</span></nav>
<section class="cat-head"><h1>{cat['title']}</h1><p>{cat['desc']}</p></section>
<div class="grid">{cards}</div>"""
        with open(os.path.join(OUTPUT, cat["file"]), "w", encoding="utf-8") as f:
            f.write(page_shell(f"{cat['title']} | {SITE['name']}", cat["desc"], body, cat["file"]))

    # 单页（about / disclaimer，depth=0）
    for slug, pg in pages.items():
        body = f"""<nav class="crumb"><a href="index.html">首页</a> / <span>{esc(pg['title'])}</span></nav>
<article class="post"><h1>{esc(pg['title'])}</h1>
<div class="post-body">
{md_to_html(pg["body"])}
</div></article>"""
        with open(os.path.join(OUTPUT, slug + ".html"), "w", encoding="utf-8") as f:
            f.write(page_shell(f"{pg['title']} | {SITE['name']}", pg.get("description", ""), body, slug + ".html"))

    # CSS
    css = """:root{--ink:#1c2b28;--muted:#5f6f6b;--line:#dfe8e5;--brand:#0f6e56;--brand-soft:#e1f5ee;--bg:#ffffff;--soft:#f4f8f6}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:"Microsoft YaHei","PingFang SC",system-ui,sans-serif;color:var(--ink);background:var(--bg);line-height:1.75}
.wrap{max-width:960px;margin:0 auto;padding:0 20px}
.site-header{border-bottom:1px solid var(--line);background:#fff;position:sticky;top:0;z-index:10}
.header-inner{display:flex;align-items:center;justify-content:space-between;height:60px}
.logo{font-size:22px;font-weight:700;color:var(--ink);text-decoration:none}
.logo-dot{color:var(--brand)}
.nav a{margin-left:18px;color:var(--muted);text-decoration:none;font-size:15px}
.nav a:hover{color:var(--brand)}
.hero{padding:56px 0 40px;text-align:center}
.hero h1{font-size:34px;color:var(--brand)}
.hero p{color:var(--muted);margin-top:12px;max-width:640px;margin-left:auto;margin-right:auto}
.hero-tags{margin-top:18px}
.hero-tags span{display:inline-block;background:var(--brand-soft);color:var(--brand);border-radius:999px;padding:4px 14px;margin:0 6px;font-size:14px}
.cat-sec{margin:36px 0}
.sec-head h2{font-size:24px}
.sec-head p{color:var(--muted);margin-top:4px}
.more{display:inline-block;margin-top:8px;color:var(--brand);text-decoration:none;font-size:14px}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:18px}
.card{background:var(--soft);border:1px solid var(--line);border-radius:12px;padding:18px}
.card h3{font-size:16px;line-height:1.5}
.card h3 a{color:var(--ink);text-decoration:none}
.card h3 a:hover{color:var(--brand)}
.card .meta{font-size:12px;color:var(--muted);margin:8px 0 6px}
.card .desc{font-size:13px;color:var(--muted);line-height:1.6}
.crumb{font-size:13px;color:var(--muted);padding:20px 0 0}
.crumb a{color:var(--muted);text-decoration:none}
.crumb a:hover{color:var(--brand)}
.post{padding:24px 0 8px}
.post h1{font-size:28px;line-height:1.4}
.post-meta{color:var(--muted);font-size:13px;margin-top:10px;padding-bottom:16px;border-bottom:1px solid var(--line)}
.post-body{padding-top:8px;font-size:15.5px}
.post-body h2{font-size:21px;margin:28px 0 10px;color:var(--ink);border-left:4px solid var(--brand);padding-left:10px}
.post-body h3{font-size:17px;margin:22px 0 8px}
.post-body p{margin:10px 0}
.post-body ul,.post-body ol{margin:10px 0 10px 24px}
.post-body li{margin:5px 0}
.post-body blockquote{background:var(--brand-soft);border-left:4px solid var(--brand);padding:10px 14px;margin:12px 0;border-radius:0 8px 8px 0;color:#0b5344}
.post-body table{width:100%;border-collapse:collapse;margin:14px 0;font-size:14px}
.post-body th{background:var(--brand-soft);color:#0b5344;text-align:left}
.post-body th,.post-body td{border:1px solid var(--line);padding:8px 10px}
.post-body hr{border:none;border-top:1px solid var(--line);margin:24px 0}
.related{padding:16px 0 40px}
.rel-list{list-style:none;padding:0;margin-top:10px}
.rel-list li{padding:8px 0;border-bottom:1px dashed var(--line)}
.rel-list a{color:var(--ink);text-decoration:none}
.rel-list a:hover{color:var(--brand)}
.cat-head{padding:36px 0 8px}
.cat-head h1{font-size:28px}
.cat-head p{color:var(--muted);margin-top:8px}
.site-footer{border-top:1px solid var(--line);background:var(--soft);margin-top:48px;padding:28px 0;font-size:13px;color:var(--muted)}
.site-footer a{color:var(--brand);text-decoration:none}
.copy{margin-top:8px}
@media(max-width:720px){.grid{grid-template-columns:1fr}.nav{display:none}.hero h1{font-size:26px}}
"""
    with open(os.path.join(OUTPUT, "css", "style.css"), "w", encoding="utf-8") as f:
        f.write(css)

    # .nojekyll（GitHub Pages 防止 Jekyll 处理）
    with open(os.path.join(OUTPUT, ".nojekyll"), "w", encoding="utf-8") as f:
        f.write("")

    # sitemap + robots
    urls = ["/index.html", "/baike.html", "/xuangou.html", "/paofa.html", "/about.html", "/disclaimer.html"]
    urls += ["articles/%s.html" % a["slug"] for a in arts]
    today = datetime.now().strftime("%Y-%m-%d")
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm.append("<url><loc>%s/%s</loc><lastmod>%s</lastmod></url>" % (SITE["url"], u, today))
    sm.append("</urlset>")
    with open(os.path.join(OUTPUT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(sm))
    with open(os.path.join(OUTPUT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % SITE["url"])

    print("OK  文章 %d 篇  页面 %d 个" % (len(arts), len(arts) + 6))

if __name__ == "__main__":
    build()
