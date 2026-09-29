# AGENTS.md — Story Twirl 网站建设规则

面向所有在这个仓库干活的人与 AI（Hermes、ChatGPT、Meta AI …）。动手前先读这份。

## 这个站是什么
儿童睡前故事站：**每晚一个免费故事**，想多读就买会员。朗读用设备自带的离线语音，不打印、
无服务器、无账号。线上：https://yanbing2026.github.io/story-twirl/

## 数据源与生成物（最重要的一节）
- **内容源 = `stories.json`**：每个故事含 `id, slug, title, blurb, minutes, cover, lesson, body`。改故事只改这个文件。
- **生成器 = `python3 scripts/build-site.py`**：重写 `index.html` 的数据块与 BUILD 戳，并生成
  `/stories/<slug>/`、`stories/index.html`、`sitemap.xml`、`robots.txt`。它同时是数据契约的持有者
  （缺字段会直接报错退出）。
- 只校验不写盘：`python3 scripts/build-site.py --check`。
- **绝不手改生成物**：`index.html`、`stories/**`、`sitemap.xml`、`robots.txt` 都归生成器管，
  手改会在下一次构建被静默覆盖。要改样式或结构，改 `scripts/build-site.py` 里的模板。

## 动手前后必须跑
```bash
python3 scripts/build-site.py --check    # 数据契约校验
python3 scripts/build-site.py            # 重新生成
python3 test-gate.py --check             # 断言自检（不开浏览器）
python3 test-gate.py                     # 端到端自检：34 项必须全过
```
`test-gate.py` 驱动真实页面点击真实按钮（免费读完 → 书架锁住 → 会员码解锁），需要
`chromium --headless=new --remote-debugging-port=9222`；没有会自动拉起。它带反回归项：
卡片必须是圆角矩形而不是药丸、标题必须单行、播放键必须真的派发出第一段朗读——
最后这条注意：CI 的 headless 没有音频引擎，断言队列状态（`qi`/`curU`），不要断言声音；这些都是真实踩过的坑。

## 发布与验证
- 发布 = GitHub Pages（`master` 分支根目录），合并后自动构建。
- Pages 对 HTML 发 `cache-control: max-age=600`，所以「推完就 curl」**不算验证**：先
  `gh api repos/yanbing2026/story-twirl/pages/builds/latest` 等到 `built`，再用本次改动独有的
  标记串 curl 确认。给用户看的链接带 `?v=N`。

## 流程（master 已保护）
1. 开分支 → 提交 → 开 PR。**不要直接推 `master`**（已禁止直接推、强推、删分支，对管理员同样生效）。
2. PR 描述写清：改了什么 + `build-site.py --check` 与 `test-gate.py` 的实际结果。
3. 合并前 `git status` 必须干净（生成物与源文件一致）。

## 其他约定
- 仓库里不放任何密钥：`.env`、token、口令一律不进 git。
- `story-twirl-1.0.apk` 是冻结的旧站快照（App 暂时不动）；
  `~/projects/StoryTwirl/scripts/sync-web-asset.sh` 是站点与 App 之间唯一的同步通道。
