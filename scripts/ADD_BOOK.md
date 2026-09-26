# 新增 Library 书籍

给首页 LIBRARY 区块加一本书的完整步骤。

## 1. 生成统一背景的封面

```bash
python scripts/make_book_cover.py "书封源图路径" "书名slug"
```

- 源图可以是截图（会自动裁掉灰色边框），也可以是干净的竖版书封
- 输出到 `public/library-<slug>.jpg`，背景自动与其他封面一致（860×500，圆环底 + 投影）
- 书封默认高度 405px，如某本书特别矮/高可用 `--height` 调整

## 2. 加首页卡片

编辑 `src/pages/index.astro`，在 `card-grid` 里按序号追加一个 `article`：

```html
<article class="work-card" data-tag="games-production">
  <a href="购买链接" target="_blank" rel="noopener">
    <div class="thumb lib-cover" data-title="书名" data-i18n-attr-title="book.<slug>.title" style="background-image:url('/library-<slug>.jpg')"></div>
    <div class="card-line"><span>07</span><h3 data-i18n="book.<slug>.title">书名</h3><span>→</span></div>
    <p><span class="tag" data-i18n="tag.gamesProduction">Games / Production</span> 作者 <span class="status is-read" data-i18n="status.read">Read</span></p>
    <p class="bio" data-i18n="book.<slug>.bio">一句话简介</p>
  </a>
</article>
```

要点：
- `data-tag` 用现有分类之一：`psychology` / `games-production` / `design-systems`
- 状态徽章：`is-reading`（正在读，蓝底）或 `is-read`（已读，灰描边）
- 序号递增（当前到 06）

## 3. 加中英文字典

编辑 `src/layouts/BaseLayout.astro`，在 EN 和 ZH 字典里各加两条：

```js
"book.<slug>.title": "英文书名",
"book.<slug>.bio":  "英文简介",
// 中文区：
"book.<slug>.title": "中文书名",
"book.<slug>.bio":  "中文简介",
```

## 4. 构建 + 推送 + 验证

```bash
node node_modules/astro/astro.js build
# 推送 3 个文件：封面 jpg + index.astro + BaseLayout.astro
# 等 Cloudflare Pages 部署后，确认卡片、双语、封面图都上线
```

> 封面背景参数固化在 `scripts/make_book_cover.py` 顶部常量区，如需调整务必同步核对现有封面是否一致。
