# 拾评 (ReviewGather)

> 基于 Steam 官方公开接口的评测批量抓取工具，图形化界面，开箱即用。

「拾评」让你无需编写任何代码，即可快速抓取任意 Steam 游戏的用户评测数据，
按语言、好评 / 差评、购买来源、游戏时长等多维度筛选，实时统计并与官方总数对比，
一键导出 CSV / TXT 报告用于二次分析。

- 平台：Windows 10 / 11（无边框窗口依赖平台特性，其他平台未测试）
- 界面：PySide6 (Qt) 自绘无边框窗口，支持深浅主题与自定义背景
- 分发：PyInstaller 打包为独立 EXE，目标机器无需安装 Python

## 功能特性

### 抓取核心

- **多语言支持**：11 种常用语言 + 全部语言
- **多维度筛选**：全部 / 仅好评 / 仅差评、Steam 直购 / 非 Steam 购买、最少游戏时长过滤
- **时长基准可选**：按游戏总时长或评测时游戏时长过滤
- **数量控制**：可设置抓取上限（0 = 无上限）
- **实时进度**：原始抓取数 → 有效数 → 好评数实时反馈，含耗时计时
- **官方对比**：自动拉取官方评测总数，计算本次抓取完整率
- **统计汇总**：购买来源分布、语言分布，爬取结束自动展示

### 报告导出

- **导出格式可选**：全部 / 仅 CSV / 仅 TXT
- **CSV**：UTF-8-SIG 编码，Excel 直接打开不乱码，含 15 个结构化字段
- **TXT**：人性化分隔的完整评测报告，含游戏信息、详细评分与内容正文
- **导出目录可配**：留空默认保存到程序目录

### 用户体验

- **昵称富化**：可选 Steam Web API Key，将 SteamID 自动替换为用户昵称，带实时进度条
- **API Key 便捷管理**：显示 / 隐藏密钥、一键验证、链接直达 Steam 官方申请页
- **游戏信息预览**：输入 AppID 一键查询游戏名称与官方评测统计
- **运行日记**：日志实时滚动，可配置最大行数、时间戳、自动跳转

### 界面个性化

- **深浅主题**：深海蓝 / 石墨灰 两套预设一键切换
- **强调色**：预设色（青绿 / 蓝色）或手动输入 `#RRGGBB` 实时调色
- **自定义背景图片**：选择本地图片铺满窗口，配合卡片透明度与背景模糊调节

### 网络控制

- 请求超时、失败重试、翻页间隔、随机抖动等全部可调
- 侧边栏一键测试连接，快速确认网络 / 代理状态

## 环境要求

- Windows 10 / 11
- Python 3.8+（源码运行方式）
- 依赖见 [requirements.txt](requirements.txt)

## 快速开始

### 源码运行

```bash
git clone https://github.com/wandergrain/review-gather.git
cd review-gather
pip install -r requirements.txt
python main.py
```

### 直接使用 EXE

从 [GitHub Releases](https://github.com/wandergrain/review-gather/releases) 下载最新版
`ReviewGather.exe`，双击运行即可，无需安装 Python 环境。

> 建议下载后先进行 SHA256 校验（见 [发布版本校验](#发布版本校验)），确认文件完整性。

## 使用说明

### 爬取数据

1. 在「爬取数据」页填入**游戏 ID (AppID)**，点击「查看游戏信息」确认游戏存在；
   - 不知道 ID 可前往 Steam 商店页面查看，例如 CS2 的地址为
     `https://store.steampowered.com/app/730/CounterStrike_2`，其中 `730` 即 AppID；
2. 选择语言、评测类型、购买来源、时长基准与最少游戏时长等参数；
3. 选择**导出格式**：全部（默认）/ 仅 CSV / 仅 TXT；
4. 点击「开始爬取」，底部进度条与摘要实时刷新；
5. 完成后按所选格式自动导出到「导出目录」（默认程序目录），并自动跳转运行日记。

### 获取用户昵称（可选）

1. 前往 [Steam Web API Key 页面](https://steamcommunity.com/dev/apikey)，域名填写 `localhost` 即可获取 Key；
2. 回到「爬取数据」页，点击「获取 API Key」可直达申请页面；
3. 将 Key 粘贴到输入框，可点击「显示」查看明文、点击「验证 Key」检查有效性；
4. 填写 Key 后抓取会自动获取每个用户昵称（进度条实时显示，数量大时约需 1-3 分钟）；
   Key 已保存到本机 `config.json`，重启程序无需重复填写；
5. 留空则导出文件中使用 SteamID 代替昵称。

### 界面与日志

- **背景颜色**：切换整体预设，立即生效；
- **强调色**：选择预设色，或选择「自定义（手动调色）」输入 `#RRGGBB` 实时预览；
- **自定义背景图片**：选择本地图片作为窗口背景，配合「卡片透明度」与「背景模糊」调节；
  设置背景后程序自动为文字加投影，保证图片背景上文字仍清晰可读；
- **日志行为**：最大行数、自动滚动、时间戳、爬取完成自动跳转日志均可配置。

## 配置文件

源码运行首次启动后会在程序目录生成 `config.json`（已加入 `.gitignore`，不会提交到仓库）。
默认值参见 [config.example.json](config.example.json)。主要字段：

| 字段 | 说明 |
| --- | --- |
| `theme` | 背景预设名（深海蓝 / 石墨灰） |
| `engine.accent_color` | 强调色预设名或 `#RRGGBB` |
| `engine.steam_api_key` | Steam Web API Key（用户主动填写，仅存本机） |
| `engine.bg_image` | 自定义背景图片路径，空为不使用 |
| `engine.card_transparency` | 卡片透明度 0-100 |
| `engine.bg_blur` | 背景模糊像素 0-60 |
| `engine.export_dir` | 报告导出目录，空为程序目录 |
| `engine.timeout` | 单次请求超时（秒） |
| `engine.retries` | 请求失败最大重试次数 |
| `engine.page_size` | 每页评测数量 |
| `engine.base_sleep` | 翻页基础等待（秒） |
| `engine.jitter` | 随机抖动（秒） |
| `engine.log_line_limit` | 日志最大行数 |
| `engine.auto_scroll_log` | 日志自动滚动 |
| `engine.log_timestamp` | 日志显示时间戳 |
| `engine.auto_switch_to_log` | 爬取完成自动跳转日志 |

## 编译打包

使用 PyInstaller，目标机器无需安装 Python。推荐 **onedir 模式**（启动快，无需解压）：

```bash
pip install pyinstaller
pyinstaller --noconfirm ReviewGather.spec
```

产物在 `dist/ReviewGather/`，分发时复制整个文件夹，双击 `ReviewGather.exe` 运行。

如需打成**单个 EXE**（分发方便，但启动时先解压、稍慢）：

```bash
pyinstaller --noconfirm --onefile --windowed --name ReviewGather --icon assets/icon.ico main.py
```

> 打包后 `config.json` 会在 EXE 同目录自动生成；`export_dir`、背景图片等路径均相对 EXE 所在目录生效。

### 发布版本校验

GitHub Release 的版本描述中会附带每种产物的 SHA256 校验值。下载后可使用以下命令校验：

```powershell
Get-FileHash .\ReviewGather.exe -Algorithm SHA256
```

将输出结果与 Release 描述中的值比对，一致即表示文件未被篡改且下载完整。

## 项目结构

```
review-gather/
├── main.py                # 程序入口，设置应用图标并启动主窗口
├── core/
│   └── scraper.py         # 爬虫核心：配置、请求、抓取、昵称富化、统计、导出
├── gui/
│   ├── app.py             # 主窗口：无边框标题栏、侧边栏、页面堆叠、背景层
│   ├── theme.py           # 主题系统：预设、强调色、玻璃态、全局样式
│   ├── widgets.py         # 通用组件：卡片、按钮、下拉框、统计卡、滑杆
│   └── pages/
│       ├── scrape_page.py     # 爬取数据页：参数配置、进度、摘要
│       ├── log_page.py        # 运行日记页
│       ├── settings_page.py   # 网络与请求 / 界面与日志 设置页
│       └── about_page.py      # 关于此程序页与用户协议弹窗
├── assets/
│   ├── icon.ico           # 程序图标（打包与窗口图标）
│   └── icon.png           # 图标位图源
├── config.example.json    # 配置示例（默认值）
├── ReviewGather.spec      # PyInstaller 打包配置
└── requirements.txt       # Python 依赖
```

## 技术栈

- Python 3
- PySide6 (Qt) — 图形界面
- requests — 访问 Steam 官方接口
- pandas — 数据整理与 CSV 导出
- concurrent.futures — 并行获取游戏信息
- PyInstaller — 打包分发

## 常见问题

**Q：抓取速度慢 / 超时报错？**
A：可在「网络与请求」设置页适当增大超时与重试次数；也可降低翻页频率（增大 `base_sleep`）
避免触发 Steam 限流。

**Q：为什么没有导出文件？**
A：检查「导出设置」中的格式是否为「仅 TXT」却期望 CSV；确认「导出目录」有写入权限；
若本次没有符合条件的评测，程序不会生成文件。

**Q：填了 API Key 还是显示 SteamID？**
A：先用「验证 Key」检查有效性；若 Key 有效，请确认没有在申请时填写过期域名，
新申请的 Key 可能需要几分钟生效。

**Q：背景图片铺不满 / 重启后不适配？**
A：较新版本已修复此问题，请升级到最新 Release；若仍异常，请附带截图反馈。

## 免责声明

- 本工具仅用于个人学习与研究，请遵守 [Steam 用户协议](https://store.steampowered.com/subscriber_agreement/)
  与当地法律法规，勿用于商业用途或大规模滥用；
- 请合理控制请求频率，过快请求可能导致 Steam 返回 429 或限制 IP；
- API Key 仅在本机使用，程序不会将数据上传到任何第三方服务器；
- 使用本工具产生的任何后果由使用者自行承担。

## 开源协议

[MIT License](LICENSE)

Copyright (c) 2026 wandergrain