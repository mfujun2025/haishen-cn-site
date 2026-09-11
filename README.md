# 海参.cn 静态站 · 部署与维护指南

> 站点：海参知识科普网（海参百科 / 选购指南 / 泡发与食用）
> 结构：纯静态 HTML，无数据库、无后端依赖，任何虚拟主机/云服务器/OSS 均可部署

---

## 一、目录结构

```
site/
├── content/          # 文章源文件（Markdown，含 front-matter）
│   ├── *.md          # 44 篇文章 + about/disclaimer 两个单页
├── build.py          # 静态站生成器（Python，无第三方依赖，相对路径适配子路径部署）
├── .github/
│   └── workflows/
│       └── deploy.yml # GitHub Actions：push 到 main 自动构建并部署 GitHub Pages
├── output/           # 生成结果（本地部署时直接用；GitHub Pages 由 CI 自动生成）
│   ├── index.html    # 首页
│   ├── baike.html    # 栏目页：海参百科
│   ├── xuangou.html  # 栏目页：选购指南
│   ├── paofa.html    # 栏目页：泡发与食用
│   ├── about.html / disclaimer.html
│   ├── articles/     # 44 篇文章页
│   ├── css/style.css # 全站样式（响应式，移动端适配）
│   ├── sitemap.xml   # 站点地图（SEO 用）
│   └── robots.txt
└── README.md
```

## 二、本地预览

```bash
cd site/output
python -m http.server 8080
# 浏览器打开 http://localhost:8080
```

## 三、新增/修改文章（两步）

1. 在 `content/` 下新建 `.md` 文件（文件名用拼音 slug），格式：

```markdown
---
title: 文章标题
category: baike        # baike=百科 / xuangou=选购 / paofa=泡发与食用
date: 2026-09-09
description: 一句话摘要（用于列表与 SEO description）
---

## 二级标题

正文支持：**粗体**、列表、> 引用、表格（| 语法）、### 三级标题。
```

2. 重新生成整站：

```bash
python build.py
```

输出会打印文章清单。把新的 `output/` 上传到服务器即可（增量上传改动文件也行，因为文件名稳定）。

## 四、部署方式（任选其一）

| 方式 | 步骤概要 |
| --- | --- |
| **GitHub Pages（当前采用）** | 见下方「GitHub Pages 部署」，push 即自动发布 |
| 云服务器 + 宝塔 | 新建站点 → 把 output/ 内容上传到网站根目录 → 开启 HTTPS |
| 虚拟主机 | FTP 上传 output/ 全部内容到 webroot |
| OSS/COS 静态托管 | 上传 output/ → 开静态网站功能 → 绑定域名 |
| Cloudflare Pages/Vercel | 推送 site/ 到 Git 仓库，构建命令留空，output 目录设为发布目录 |

## 四A、GitHub Pages 部署（推荐，已配好 CI）

仓库已包含 `.github/workflows/deploy.yml`：每次 push 到 `main`，CI 自动执行
`python site/build.py` 并把 `site/output/` 发布到 GitHub Pages。**本地无需安装
Python，也不用上传 output/ 目录（CI 会生成）。**

首次启用只需三步：

1. 仓库页 → **Settings → Pages**；
2. **Build and deployment → Source** 选择 **GitHub Actions**（不是 Deploy from a branch）；
3. 完成。之后每次 push 到 main，Actions 会自动构建并发布，地址为：
   `https://<用户名>.github.io/<仓库名>/`

日常更新流程（加文章只需两步）：

```bash
# 1. 在 content/ 新增或修改 .md 文件
# 2. 提交推送（CI 自动构建发布）
git add content/ && git commit -m "新增文章" && git push
```

注意事项：

- `build.py` 已改为**相对路径**输出，子路径部署（`/仓库名/`）下样式和链接均正常；
- `sitemap.xml` 使用 `SITE["url"]` 绝对地址，绑自定义域名时记得同步修改；
- 绑定自定义域名（如 haishen.cn）：在 Settings → Pages → Custom domain 填入，
  并在 DNS 添加 CNAME 记录指向 `<用户名>.github.io`（域名托管在国内服务商时
  解析生效快，但 GitHub Pages 服务器在境外，国内访问速度一般）。

## 五、上线前必做清单

- [ ] **替换域名**：`build.py` 顶部的 `SITE["url"]` 改为实际域名（影响 canonical 与 sitemap），改后重新 build
- [ ] **ICP 备案**：国内服务器/解析到国内必须备案（内容站不影响备案，无经营行为无需食品许可）
- [ ] **提交搜索引擎**：到百度搜索资源平台添加站点 + 提交 `sitemap.xml`
- [ ] **HTTPS**：申请免费证书开启，全站 https
- [ ] **统计**：页面底部 footer 前可自行插入统计代码（如百度统计）

## 六、SEO 快速启动建议（配合养站策略）

1. 保持每周 2-3 篇更新频率（新增 md → build → 上传）；
2. 新文章围绕长尾词写（可参考现有选题模式：「XX怎么选」「XX怎么做」「XX原因」）；
3. 同步做百度系内容：百度百科词条、百度知道回答，留自然品牌曝光；
4. 3 个月内不要频繁改站点标题与结构（新站考核期）；
5. 每月记录：收录量、关键词排名、UV——这些是未来出售/出租时的议价数据。

## 七、后续变现衔接

- 交易平台挂牌（阿里云域名/易名/有名网/聚名网）时，直接引用本站流量与收录数据作为增值证明；
- 站点 footer 已预留"关于/免责声明"页，符合内容站规范形象；
- 未来若加广告或电商导购，注意广告法对滋补品宣传的限制（本站内容已按"不宣传功效"口径写作，可放心作为基础）。
