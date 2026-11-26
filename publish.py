# -*- coding: utf-8 -*-
"""
海参.cn 每日内容发布脚本（配合 build.py 使用）

用途：把 content/ 下新增的 Markdown 文章发布成带 GEO/FQA Schema 的文章页，
      并增量同步：全站导航、首页栏目卡片、栏目页、sitemap、llms.txt、ai.txt。

用法：
    python publish.py content/yangzhi-zhouqi.md

特点：
- 只增量处理传入的 md 文件，不覆盖已有文章的 GEO 增强内容；
- 全站导航插入"海参养殖"入口，天然幂等（已存在则跳过）；
- 自动从 md 的「常见问题」小节生成 FAQPage JSON-LD + 可见 FAQ 区块。
"""
import os
import re
import sys
import json
import html as htmllib
from datetime import datetime

import build as B

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content")
SITE_URL = B.SITE["url"].rstrip("/")


def detect_crlf(path):
    """检测文件原始换行风格（须在写回前调用）。"""
    if not os.path.exists(path):
        return False
    with open(path, "rb") as f:
        return b"\r\n" in f.read()


def read(path):
    # 内部统一按 LF 处理，写回时再还原原始风格
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")


def write(path, text, crlf=False):
    if crlf:
        text = text.replace("\n", "\r\n")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def sync_nav():
    """给所有已发布 HTML 的全站导航加上「海参养殖」入口（幂等）。"""
    nav_new_root = '      <a href="yangzhi.html">海参养殖</a>\n'
    nav_new_sub = '      <a href="../yangzhi.html">海参养殖</a>\n'
    changed = 0
    for dirpath, _, files in os.walk(ROOT):
        if ".git" in dirpath.split(os.sep):
            continue
        for fn in files:
            if not fn.endswith(".html"):
                continue
            p = os.path.join(dirpath, fn)
            crlf = detect_crlf(p)
            text = read(p)
            if '>海参养殖</a>' in text:
                continue
            anchor = '<a href="%sbaike.html">海参百科</a>\n' % (
                "../" if os.path.basename(dirpath) == "articles" else "")
            news = nav_new_sub if os.path.basename(dirpath) == "articles" else nav_new_root
            if anchor not in text:
                continue
            text = text.replace(anchor, anchor + news, 1)
            write(p, text, crlf)
            changed += 1
    return changed


def parse_faq(body):
    """从 md 正文的「常见问题」小节提取问答，返回 [(q, a), ...]。"""
    m = re.search(r"^##\s+常见问题\s*$(.*?)(?=^##\s|\Z)", body, re.M | re.S)
    if not m:
        return []
    chunk = m.group(1).strip()
    qa = []
    blocks = re.split(r"\*\*(.+?)\*\*", chunk)
    for i in range(1, len(blocks), 2):
        q = blocks[i].strip()
        a = re.sub(r"\s+", " ", blocks[i + 1]).strip() if i + 1 < len(blocks) else ""
        if q and a:
            qa.append((q, a))
    return qa


def faq_block(qa):
    if not qa:
        return ""
    items = "".join(
        '<div class="faq-item"><h3>%s</h3><p>%s</p></div>' % (
            htmllib.escape(q), htmllib.escape(a)) for q, a in qa)
    return '<h2>常见问题</h2>\n<div class="faq">\n%s\n</div>' % items


def faq_schema(qa):
    if not qa:
        return ""
    main = [{
        "@type": "Question",
        "name": q,
        "acceptedAnswer": {"@type": "Answer", "text": a}
    } for q, a in qa]
    data = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": main}
    return '<script type="application/ld+json">%s</script>\n' % json.dumps(
        data, ensure_ascii=False)


def strip_faq_section(body):
    """从正文移除常见问题小节，避免与 FAQ 区块重复。"""
    return re.sub(r"^##\s+常见问题\s*$.*?(?=^##\s|\Z)", "", body, flags=re.M | re.S).rstrip()


def build_article(md_path):
    a = B.parse_md(md_path)
    slug = a["slug"]
    cat = B.CATS[a["category"]]
    qa = parse_faq(a["body"])
    body_md = strip_faq_section(a["body"])
    body_html = B.md_to_html(body_md)
    if qa:
        body_html += "\n\n" + faq_block(qa)

    related = [x for x in all_articles() if x["category"] == a["category"] and x["slug"] != slug][:3]
    rel_html = ""
    if related:
        rel_html = ('<section class="related"><h2>相关文章</h2><ul class="rel-list">' + "".join(
            '<li><a href="../articles/%s.html">%s</a></li>' % (r["slug"], htmllib.escape(r["title"]))
            for r in related) + "</ul></section>")

    article_body = f"""<nav class="crumb"><a href="../index.html">首页</a> / <a href="../{cat['file']}">{cat['title']}</a> / <span>{htmllib.escape(a['title'])}</span></nav>
<article class="post">
  <h1>{htmllib.escape(a['title'])}</h1>
  <p class="post-meta">{htmllib.escape(a.get('date',''))} · {cat['title']} · 阅读约 4 分钟</p>
  <div class="post-body">
{body_html}
  </div>
</article>
{rel_html}"""

    shell = B.page_shell(
        f"{a['title']} - {cat['title']} | {B.SITE['name']}",
        a.get("description", ""), article_body,
        "articles/" + slug + ".html", depth=1)
    shell = shell.replace("</head>", faq_schema(qa) + "</head>")
    out = os.path.join(ROOT, "articles", slug + ".html")
    write(out, shell, detect_crlf(out))
    return slug, cat


def all_articles():
    arts = []
    for f in sorted(os.listdir(CONTENT)):
        if not f.endswith(".md"):
            continue
        a = B.parse_md(os.path.join(CONTENT, f))
        if a.get("category") != "page":
            arts.append(a)
    arts.sort(key=lambda x: (x.get("date", ""), x["slug"]), reverse=True)
    return arts


def refresh_index():
    """用生成器重建首页（含新栏目卡片），再补回 Organization Schema。"""
    index_path = os.path.join(ROOT, "index.html")
    crlf = detect_crlf(index_path)
    old = read(index_path)
    org = ""
    m = re.search(r'<script type="application/ld\+json">(\{"@context".*?"@type":\s*"Organization".*?\})</script>', old)
    if m:
        org = '<script type="application/ld+json">%s</script>\n' % m.group(1)
    sections = []
    for ck, cat in B.CATS.items():
        items = [a for a in all_articles() if a["category"] == ck]
        cards = "".join(B.article_card(a) for a in items)
        sections.append(f"""<section class="cat-sec" id="{ck}">
  <div class="sec-head"><h2>{cat['title']}</h2><p>{cat['desc']}</p><a class="more" href="{cat['file']}">查看全部 →</a></div>
  <div class="grid">{cards}</div>
</section>""")
    home = f"""<section class="hero">
  <h1>{htmllib.escape(B.SITE['slogan'])}</h1>
  <p>{htmllib.escape(B.SITE['desc'])}</p>
  <p class="hero-tags"><span>海参百科</span><span>海参养殖</span><span>选购避坑</span><span>泡发教程</span><span>家常做法</span></p>
</section>
{"".join(sections)}"""
    shell = B.page_shell(B.SITE["full_name"] + " —— " + B.SITE["slogan"],
                         B.SITE["desc"], home, "index.html")
    shell = shell.replace("</head>", org + "</head>")
    write(index_path, shell, crlf)


def refresh_category(cat_key):
    cat = B.CATS[cat_key]
    items = [a for a in all_articles() if a["category"] == cat_key]
    cards = "".join(B.article_card(a) for a in items)
    body = f"""<nav class="crumb"><a href="index.html">首页</a> / <span>{cat['title']}</span></nav>
<section class="cat-head"><h1>{cat['title']}</h1><p>{cat['desc']}</p></section>
<div class="grid">{cards}</div>"""
    shell = B.page_shell(f"{cat['title']} | {B.SITE['name']}", cat["desc"], body, cat["file"])
    out = os.path.join(ROOT, cat["file"])
    write(out, shell, detect_crlf(out))


def refresh_sitemap(changed_urls=None):
    """增量更新 sitemap：保留已有 URL 的 lastmod，仅为新增/指定 URL 更新为今天。"""
    changed_urls = set(changed_urls or [])
    out = os.path.join(ROOT, "sitemap.xml")
    crlf = detect_crlf(out)
    old = read(out) if os.path.exists(out) else ""
    old_lm = dict(re.findall(r"<loc>%s/(.+?)</loc><lastmod>(.+?)</lastmod>" % re.escape(SITE_URL), old))

    urls = ["index.html", "baike.html", "yangzhi.html", "xuangou.html",
            "paofa.html", "about.html", "disclaimer.html"]
    urls += ["articles/%s.html" % a["slug"] for a in all_articles()]
    today = datetime.now().strftime("%Y-%m-%d")
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        lastmod = today if (u in changed_urls or u not in old_lm) else old_lm[u]
        lines.append("<url><loc>%s/%s</loc><lastmod>%s</lastmod></url>" % (SITE_URL, u, lastmod))
    lines.append("</urlset>")
    write(out, "\n".join(lines), crlf)


def refresh_geo_text():
    """更新 llms.txt / ai.txt 的养殖栏目与文章计数。"""
    n = len(all_articles())
    for fn in ("llms.txt", "ai.txt"):
        p = os.path.join(ROOT, fn)
        crlf = detect_crlf(p)
        t = read(p)
        if "海参养殖：https://海参.cn/yangzhi.html" not in t:
            t = t.replace("- 海参百科：https://海参.cn/baike.html",
                          "- 海参百科：https://海参.cn/baike.html\n- 海参养殖：https://海参.cn/yangzhi.html")
        t = re.sub(r"共\s*\d+\s*篇文章", "共 %d 篇文章" % n, t)
        if "海参养殖：参苗育苗、底播圈养" not in t:
            t = t.replace("- 海参百科：种类、产地、营养、产品形态",
                          "- 海参百科：种类、产地、营养、产品形态\n- 海参养殖：参苗育苗、底播圈养、北参南养与养殖周期")
        if "海参养殖（yangzhi.html）" not in t:
            t = t.replace("1. 海参百科（baike.html）",
                          "1. 海参百科（baike.html）\n2. 海参养殖（yangzhi.html）")
            t = re.sub(r"(\n2\. 海参养殖（yangzhi\.html）)\n2\. 选购指南", r"\1\n3. 选购指南", t)
            t = t.replace("3. 价格行情（jiage.html）", "4. 价格行情（jiage.html）")
            t = t.replace("4. 泡发与食用（paofa.html）", "5. 泡发与食用（paofa.html）")
            t = t.replace("5. 批发信息（pifa.html）", "6. 批发信息（pifa.html）")
        t = re.sub(r"(更新时间|Generated):\s*\d{4}-\d{2}-\d{2}",
                   lambda m: "%s: %s" % (m.group(1), datetime.now().strftime("%Y-%m-%d")), t)
        write(p, t, crlf)


def main():
    if len(sys.argv) < 2:
        print("用法: python publish.py <content/xxx.md> [更多md...]")
        sys.exit(1)
    changed_urls = set()
    for arg in sys.argv[1:]:
        if not arg.endswith(".md"):
            continue
        slug, _ = build_article(os.path.join(ROOT, arg))
        changed_urls.add("articles/%s.html" % slug)
    changed = sync_nav()
    refresh_index()
    refresh_category("yangzhi")
    changed_urls.update(["index.html", "yangzhi.html"])
    refresh_sitemap(changed_urls)
    refresh_geo_text()
    print("发布完成：文章 %d 篇，导航补充 %d 页" % (len(all_articles()), changed))


if __name__ == "__main__":
    main()
