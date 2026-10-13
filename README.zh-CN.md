> 🌐 [English](README.md) | **简体中文**

<div align="center">

# MCP for Blender

**将 Blender 连接到任何 LLM**

*原名 `blender-mcp` —— PyPI 包现已更名为 [`mcp-for-blender`](https://pypi.org/project/mcp-for-blender/)。*
*现有配置继续有效，无需任何修改。[了解详情](https://github.com/ahujasid/mcp-for-blender/issues/366)*

**免责声明：** 本项目为第三方集成，并非由 Blender 官方出品

由 AI 驱动的提示词辅助 3D 建模、场景创建与操作。

[![PyPI Downloads](https://static.pepy.tech/personalized-badge/blender-mcp?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/blender-mcp)
[![Discord](https://img.shields.io/badge/Discord-join-5865F2?logo=discord&logoColor=white)](https://discord.gg/SNqPn4TcKQ)
[![Website](https://img.shields.io/badge/Website-mcp--for--blender.com-black)](https://mcp-for-blender.com/)
[![Sponsor](https://img.shields.io/badge/Sponsor-%E2%9D%A4-EA4AAA?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/ahujasid)
[![PyPI Version](https://img.shields.io/pypi/v/mcp-for-blender?color=blue)](https://pypi.org/project/mcp-for-blender/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

<a href="https://trendshift.io/repositories/14834?utm_source=repository-badge&amp;utm_medium=badge&amp;utm_campaign=badge-repository-14834" target="_blank" rel="noopener noreferrer"><img src="https://trendshift.io/api/badge/repositories/14834" alt="ahujasid%2Fblender-mcp | Trendshift" width="250" height="55"/></a>

<br />

**支持者**

[CodeRabbit](https://www.coderabbit.ai/)
[Guillermo Rauch](https://github.com/rauchg)

**全部支持者：** [支持这个项目](https://github.com/sponsors/ahujasid)

</div>

---

## 快速开始

> **注意：** PyPI 包 `blender-mcp` 已更名为 **`mcp-for-blender`**。现有配置
> 继续有效 —— `uvx blender-mcp` 仍可正常运行服务器，**无需修改任何配置**。
> 新安装请使用 `mcp-for-blender`。
> [变更说明](https://github.com/ahujasid/mcp-for-blender/issues/366)

**一条命令**即可完成 AI 应用与 Blender 插件的配置：

**macOS / Linux**

```bash
curl -LsSf https://www.mcp-for-blender.com/install.sh | sh
```

**Windows**（PowerShell）

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://www.mcp-for-blender.com/install.ps1 | iex"
```

已安装 uv？可直接运行 `uvx mcp-for-blender setup`。

安装脚本会在需要时安装 [uv](https://docs.astral.sh/uv/)，找到你机器上的 MCP 客户端（Claude Desktop、Claude Code、Codex、Cursor、VS Code、Devin Desktop/Windsurf、OpenCode、Antigravity），让你选择要配置哪些；随后安装 Blender 插件并启用它。现有配置会被保留：只会新增一个 `blender` 条目，并为每个改动的文件保存 `.bak` 备份。

然后**完全退出并重新打开你的 AI 应用**（Windows 下请从系统托盘退出），打开 Blender，让它搭建点什么。插件会随 Blender 启动而自动开启服务。


<details>
<summary><b>手动安装（自动安装不可用时）</b></summary>

三个步骤：安装 `uv`、让 MCP 客户端指向服务器、安装 Blender 插件。

**1. 安装 uv**

```bash
# macOS
brew install uv

# Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> **警告：** 在安装 uv 之前请勿继续。请使用官方安装器 —— *不要* `pip install uv`。

**2. 在客户端中添加 MCP 服务器**

<details open>
<summary><b>Claude Desktop</b> — Settings → Developer → Edit Config</summary>

```json
{
    "mcpServers": {
        "blender": {
            "command": "uvx",
            "args": ["mcp-for-blender"]
        }
    }
}
```
</details>

<details>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add blender uvx mcp-for-blender
```
</details>

<details>
<summary><b>Codex</b></summary>

```bash
codex mcp add blender -- uvx mcp-for-blender
```
</details>

<details>
<summary><b>Cursor / VS Code / OpenCode / Antigravity</b></summary>

各客户端的详细说明和一键安装按钮见下文 [MCP 客户端配置](#mcp-客户端配置)。
</details>

**3. 安装 Blender 插件**

```bash
uvx mcp-for-blender install-addon
```

然后在 Blender 中：**Edit → Preferences → Add-ons** → 启用 **Interface: MCP for Blender**。

**4. 连接**

插件会随 Blender 启动而自动开启服务。检查方法：在 3D 视口中按 `N` → 打开 **MCP for Blender** 标签页（若服务未运行，点击 **Start MCP Server**）。完成 —— 让 Claude 搭建点什么吧。

</details>

> **注意：** 只运行**一个** MCP 服务器实例（Cursor 或 Claude Desktop 二选一），不要同时运行。

---

## 目录

- [快速开始](#快速开始)
- [功能特性](#功能特性)
- [Premium](#premium)
- [组成部分](#组成部分)
- [安装](#安装)
  - [自动安装](#自动安装)
  - [前置要求](#前置要求)
  - [让客户端找到 uvx](#让客户端找到-uvx)
  - [固定 Python 版本](#固定-python-版本)
  - [不用 uv 安装](#不用-uv-安装)
  - [使用 Docker 运行](#使用-docker-运行)
  - [环境变量](#环境变量)
- [MCP 客户端配置](#mcp-客户端配置)
  - [Claude for Desktop](#claude-for-desktop)
  - [Codex](#codex)
  - [Cursor](#cursor)
  - [Visual Studio Code](#visual-studio-code)
  - [OpenCode](#opencode)
  - [Antigravity](#antigravity)
- [HTTP / SSE 传输](#http--sse-传输)
- [安装 Blender 插件](#安装-blender-插件)
- [升级（现有用户）](#升级现有用户)
- [使用方法](#使用方法)
  - [启动连接](#启动连接)
  - [与 Claude 配合使用](#与-claude-配合使用)
  - [功能一览](#功能一览)
  - [示例指令](#示例指令)
- [持久化 API 凭据](#持久化-api-凭据)
- [故障排查](#故障排查)
- [技术细节](#技术细节)
- [限制与安全注意事项](#限制与安全注意事项)
- [遥测控制](#遥测控制)
- [反馈](#反馈)
- [参与贡献](#参与贡献)
- [免责声明](#免责声明)
- [Star History](#star-history)

---

## 功能特性

| | |
|---|---|
| **双向通信** | 通过基于 socket 的服务器将 Claude AI 连接到 Blender |
| **对象操作** | 在 Blender 中创建、修改和删除 3D 对象 |
| **材质控制** | 应用和修改材质与颜色 |
| **视觉验证** | 多角度、相机、线框、X 射线和动画条带视图，外加渲染图，让 AI 能检查自己的工作成果 |
| **代码执行** | AI 直接编写 Blender Python |
| **资产与模型生成** | Poly Haven 资产、Sketchfab 模型、Poly Pizza 低多边形模型，以及通过 Tripo、Hyper3D Rodin 和 Hunyuan3D 生成的 AI 3D 模型 |

## Premium

通过 [Premium（高级版）](https://www.mcp-for-blender.com/premium)，无需自备 API 密钥即可直接在 Blender 中生成 AI 3D 模型（Hunyuan3D、Tripo、Hyper3D Rodin）。

## 组成部分

系统由两个主要部分组成：

1. **Blender 插件**（`addon.py`）—— 一个在 Blender 内创建 socket 服务器的插件，负责接收并执行命令
2. **MCP 服务器**（`src/blender_mcp/server.py`）—— 一个实现模型上下文协议（Model Context Protocol）并连接到 Blender 插件的 Python 服务器

---

## 安装

### 自动安装

最快捷的方式是一行式安装器。它会安装 uv、配置你的 MCP 客户端，并安装并启用 Blender 插件：

```bash
# macOS / Linux
curl -LsSf https://www.mcp-for-blender.com/install.sh | sh
```

```powershell
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://www.mcp-for-blender.com/install.ps1 | iex"
```

已安装 uv？可直接运行 `uvx mcp-for-blender setup`。它做了什么见[快速开始](#快速开始)。本节其余部分介绍手动安装。

### 前置要求

- **Blender** 3.0 或更高版本
- **Python** 3.10 或更高版本
- **uv** 包管理器

<details>
<summary><b>各平台安装 uv</b></summary>

**macOS**
```bash
brew install uv
```

**Windows**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

然后在 Windows 中将 uv 加入用户 PATH（之后可能需要重启 Claude Desktop）：

```powershell
$localBin = "$env:USERPROFILE\.local\bin"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
[Environment]::SetEnvironmentVariable("Path", "$userPath;$localBin", "User")
```

**Linux**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

uv 会被安装到 `~/.local/bin` —— 请打开一个新的终端会话，让它进入 PATH。

其他安装方式见官网：[Install uv](https://docs.astral.sh/uv/getting-started/installation/)

无论哪个操作系统，请务必使用上面的 uv **官方安装器 —— 不要 `pip install uv`**，后者可能不会创建 `uvx` 命令，还会把 uv 藏在客户端看不到的环境里。
</details>

> **警告：** 在安装 uv 之前请勿继续。

### 让客户端找到 uvx

从 GUI 启动的 MCP 客户端（Claude Desktop、从 Dock/开始菜单打开的 Cursor、VS Code）**不会**继承你终端的 PATH，因此即使 `uvx` 在终端里可用，配置中的 `"command": "uvx"` 也可能报 **`spawn uvx ENOENT`**。如果遇到这种情况：

- 找到 uvx 的完整路径 —— `which uvx`（macOS/Linux）或 `where uvx`（Windows），把它作为 `"command"` 使用，例如 `/opt/homebrew/bin/uvx` 或 `C:\Users\<你>\.local\bin\uvx.exe`。
- Windows 下也可以包一层：`"command": "cmd", "args": ["/c", "uvx", "mcp-for-blender"]`。
- 任何 PATH 或配置改动之后，都要**完全退出并重启**客户端（Windows：从系统托盘退出，而不是只关窗口；macOS：<kbd>Cmd</kbd>+<kbd>Q</kbd>）。

### 固定 Python 版本

*避免 conda / pyenv / 版本冲突。*

由 uv 决定用哪个 Python 运行服务器。在装有 conda（自动激活 base 环境）、pyenv 或 asdf 的机器上——或者当 CPython 新版本尚未提供某些依赖的 wheel 时——uv 可能选到一个导致安装失败的解释器。固定使用 Python 3.11 并优先使用 uv 托管的解释器，避免碰运气用 PATH 上的任意 Python：

```json
{
    "mcpServers": {
        "blender": {
            "command": "uvx",
            "args": ["--python", "3.11", "mcp-for-blender"],
            "env": { "UV_PYTHON_PREFERENCE": "only-managed" }
        }
    }
}
```

`--python 3.11` 仍满足本包的 `requires-python >=3.10`，而 `UV_PYTHON_PREFERENCE=only-managed` 让 uv 不会优先选择 conda、pyenv、asdf 或系统 Python。（仓库的 `.python-version` 只是给贡献者的提示，**不会**影响 `uvx`。）

如果之前一次失败的尝试在修复后仍然反复出现，清理缓存：

```bash
uv cache clean mcp-for-blender blender-mcp && uvx --refresh mcp-for-blender
```

### 不用 uv 安装

在受限机器上可以用 [`pipx`](https://pipx.pypa.io) 完全绕开 uvx，然后让客户端指向安装好的命令：

```bash
pipx install mcp-for-blender
pipx ensurepath          # 然后重启终端 / 客户端
```

把得到的绝对路径作为 `"command"`（用 `which mcp-for-blender` / `where mcp-for-blender` 查找），并去掉 `args`。

### 使用 Docker 运行

可以用容器来运行 MCP 服务器，而不必安装它。Blender 本体仍运行在你的机器上 —— 容器只承载 MCP 服务器，由它向外连接 Blender 插件。

在仓库根目录构建镜像：

```bash
docker build -t mcp-for-blender .
```

然后让 MCP 客户端指向它（`-i` 参数必不可少 —— 服务器通过 stdin/stdout 与客户端通信）：

```json
{
    "mcpServers": {
        "blender": {
            "command": "docker",
            "args": ["run", "-i", "--rm", "mcp-for-blender"]
        }
    }
}
```

镜像默认设置 `BLENDER_HOST=host.docker.internal`，在 **macOS 和 Windows** 上配合 Docker Desktop 开箱即可连到宿主机上的 Blender。

在 **Linux** 上，`host.docker.internal` 不存在，且插件只监听 `localhost`，因此请改用 host 网络：

```json
{
    "mcpServers": {
        "blender": {
            "command": "docker",
            "args": ["run", "-i", "--rm", "--network=host", "-e", "BLENDER_HOST=localhost", "mcp-for-blender"]
        }
    }
}
```

要在容器中启用[安全模式](#安全模式)，在 `args` 中加入 `"-e", "BLENDER_MCP_SAFE_MODE=1"`。

### 环境变量

以下环境变量可用于配置 Blender 连接：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `BLENDER_HOST` | `localhost` | Blender socket 服务器的主机地址 |
| `BLENDER_PORT` | `9876` | Blender socket 服务器的端口 |
| `BLENDER_MCP_TRANSPORT` | `stdio` | MCP 传输方式：`stdio`、`http`（Streamable HTTP）或 `sse`（旧版）—— 见 [HTTP / SSE 传输](#http--sse-传输) |
| `BLENDER_MCP_HTTP_HOST` | `127.0.0.1` | HTTP/SSE 传输监听的地址 |
| `BLENDER_MCP_HTTP_PORT` | `8000` | HTTP/SSE 传输监听的端口 |
| `BLENDER_MCP_HTTP_STATELESS` | off | 设为 `1` 以无会话方式运行 Streamable HTTP（面向无状态客户端/部署） |
| `BLENDER_MCP_HTTP_TOKEN` | 未设置 | 设置后，HTTP/SSE 请求必须携带 `Authorization: Bearer <token>` |
| `BLENDER_MCP_HTTP_SERVICES` | on | 设为 `0` 可在保留 MCP-over-HTTP 的同时禁用预览/上传/下载路由 |
| `BLENDER_MCP_FILES_DIR` | `~/.blender-mcp/files` | 托管目录，存放 `uploads/`、`exports/` 和 `renders/` |
| `BLENDER_MCP_PUBLIC_URL` | 未设置 | HTTP 附加服务对外通告的基础 URL（容器端口映射改变主机/端口时使用） |
| `BLENDER_MCP_MAX_UPLOAD_MB` | `512` | `POST /upload/{filename}` 的大小上限 |
| `BLENDER_MCP_SAFE_MODE` | off | 设为 `1` 可在脚本于 Blender 中运行前进行校验（见下文） |
| `BLENDER_MCP_APPS` | auto | 设为 `1` 可对支持 MCP Apps 但未声明支持的客户端强制开启内嵌视口应用（Codex 插件会设置此项） |
| `BLENDER_MCP_OPENAI_FORMS` | auto | 设为 `1` 可强制开启缩略图资产选择器（Codex 插件会设置此项） |

示例：

```bash
export BLENDER_HOST='host.docker.internal'
export BLENDER_PORT=9876
```

也可以通过 CLI 参数传递连接信息，其优先级高于环境变量。并行运行多个 Blender 实例时这一点很方便：每个 MCP 客户端条目可以用普通参数指向不同的端口，而不必依赖环境变量：

```bash
uvx mcp-for-blender --port 9877
```

在 MCP 客户端配置里，就是仅 `args` 不同的第二个条目：

```json
{
  "mcpServers": {
    "blender": { "command": "uvx", "args": ["mcp-for-blender"] },
    "blender-b": { "command": "uvx", "args": ["mcp-for-blender", "--port", "9877"] }
  }
}
```

每个实例都需要在 Blender 插件面板中设置与之匹配的独立端口。

> **注意：** 插件的 socket 服务器没有鉴权或加密，任何能访问该端口的人都可以在
> Blender 中执行 Python。除非处于可信网络，否则请保持在 `localhost` 上；需要
> 跨机访问时，优先使用 SSH 隧道，而不是把 `--host`/`BLENDER_HOST` 直接指向远程
> 机器。

#### 安全模式

默认情况下，AI 可以在 Blender 中运行任意 Python 代码。设置 `BLENDER_MCP_SAFE_MODE=1` 后，每个脚本在运行前都会被检查，有风险的代码会被拦截 —— 例如直接读写文件、运行其他程序、访问网络，或安装脚本结束后仍持续运行的代码。正常的 Blender 操作（建模、材质、渲染、保存、导入/导出）不受影响。被拦截的脚本会连同原因一起返回给 AI，让它修正后重试。

---

## MCP 客户端配置

### Claude for Desktop

[观看配置教学视频](https://www.youtube.com/watch?v=neoK_WMq92g)（假设你已安装 uv）

打开 **Claude → Settings → Developer → Edit Config → `claude_desktop_config.json`**，加入以下内容：

```json
{
    "mcpServers": {
        "blender": {
            "command": "uvx",
            "args": [
                "mcp-for-blender"
            ]
        }
    }
}
```

<details>
<summary><b>Claude Code</b></summary>

使用 Claude Code CLI 添加 MCP for Blender 服务器：

```bash
claude mcp add blender uvx mcp-for-blender
```
</details>

### Codex

Codex CLI、桌面应用和 IDE 扩展共用同一个配置文件（`~/.codex/config.toml`），因此配置一次，三端通用。

#### Codex 插件（推荐）

插件可以在聊天中内嵌实时视口（点击对象即可附加到下一条消息）、为 Poly Haven、Sketchfab 和 Poly Pizza 提供缩略图选择器，并支持 `@` 提及场景中的对象、材质与集合。它尚未上架 Codex 插件目录，请从本仓库添加：

```bash
git clone https://github.com/ahujasid/blender-mcp.git
codex plugin marketplace add ./blender-mcp/integrations/codex
```

然后重启 Codex，在插件目录中安装 **MCP for Blender**，并在聊天中让它使用 MCP for Blender。运行后，视口会在对话旁的侧边面板中打开：

![Codex 应用中的 MCP for Blender 插件，聊天旁显示实时视口](assets/codex-screenshot.png)

#### 普通 MCP 服务器

用 [Codex CLI](https://github.com/openai/codex) 注册服务器：

```bash
codex mcp add blender -- uvx mcp-for-blender
```

或手动添加到 `~/.codex/config.toml`（或 `$CODEX_HOME/config.toml`）：

```toml
[mcp_servers.blender]
command = "uvx"
args = ["mcp-for-blender"]
```

或在 **Codex 桌面应用**中：**Settings → MCP servers → Add server** → 命名为 `blender`，类型选 **STDIO**，命令填 `uvx mcp-for-blender`，然后 **Save** 并重启。如果应用找不到 `uvx`，改用完整路径 —— 见[让客户端找到 uvx](#让客户端找到-uvx)。

用 `codex mcp list` 检查注册结果 —— `blender` 服务器应显示为 **enabled**。工具会在下次启动 Codex 时可用。

要设置[环境变量](#环境变量)（例如非默认的 Blender 主机/端口），给 `codex mcp add` 传 `--env KEY=VALUE` 参数，或在配置文件中添加：

```toml
[mcp_servers.blender]
command = "uvx"
args = ["mcp-for-blender"]
env = { BLENDER_HOST = "localhost", BLENDER_PORT = "9876" }
```

### Cursor

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/link/mcp%2Finstall?name=blender&config=eyJjb21tYW5kIjoidXZ4IG1jcC1mb3ItYmxlbmRlciJ9)

**macOS** —— 打开 **Settings → MCP**，粘贴以下内容：

- 作为全局服务器：点击 *"add new global MCP server"* 按钮并粘贴
- 作为项目级服务器：在项目根目录创建 `.cursor/mcp.json` 并粘贴

```json
{
    "mcpServers": {
        "blender": {
            "command": "uvx",
            "args": [
                "mcp-for-blender"
            ]
        }
    }
}
```

**Windows** —— 打开 **Settings → MCP → Add Server**，按以下配置添加新服务器：

```json
{
    "mcpServers": {
        "blender": {
            "command": "cmd",
            "args": [
                "/c",
                "uvx",
                "mcp-for-blender"
            ]
        }
    }
}
```

[Cursor 配置视频](https://www.youtube.com/watch?v=wgWsJshecac)

### Visual Studio Code

*前置要求：先安装 [Visual Studio Code](https://code.visualstudio.com/)。*

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_mcp--for--blender_server-0098FF?style=flat-square&logo=visualstudiocode&logoColor=ffffff)](https://vscode.dev/redirect/mcp/install?name=blender&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22mcp-for-blender%22%5D%7D)

### OpenCode

```json
{
  "mcp": {
    "blender-mcp": {
      "type": "local",
      "command": ["uvx", "mcp-for-blender"],
      "enabled": true,
      "environment": {
        "BLENDER_HOST": "localhost",
        "BLENDER_PORT": "9876"
      }
    }
  }
}
```

### Antigravity

```json
{
  "mcpServers": {
    "blender-mcp": {
      "command": "uvx",
      "args": ["mcp-for-blender"],
      "env": {
        "BLENDER_HOST": "localhost",
        "BLENDER_PORT": "9876"
      }
    }
  }
}
```

---

## HTTP / SSE 传输

默认情况下，MCP 服务器使用 stdio 通信：由你的 MCP 客户端启动它并通过 stdin/stdout 交互。如果客户端通过 URL 连接（Web 连接器、多个客户端共享一个服务器进程、或服务器运行在另一台机器上），可以将它作为 HTTP 端点启动：

```bash
uvx mcp-for-blender --transport http
# MCP 端点：http://127.0.0.1:8000/mcp
```

`http` 是 [Streamable HTTP](https://modelcontextprotocol.io/docs/concepts/transports#streamable-http)，即当前的 MCP HTTP 传输方式。只会说旧版 SSE 协议的客户端可以用 `--transport sse` 启动（端点为 `http://127.0.0.1:8000/sse`）。stdio 仍是默认值，所有现有客户端配置无需任何改动即可继续工作。

常用参数（每个都有对应的 `BLENDER_MCP_*` 环境变量，见[环境变量](#环境变量)；CLI 优先）：

| 参数 | 默认值 | 说明 |
|---|---|---|
| `--transport` | `stdio` | `stdio`、`http` 或 `sse` |
| `--http-host` | `127.0.0.1` | 监听地址 |
| `--http-port` | `8000` | 监听端口 |
| `--stateless-http` | off | 以无 MCP 会话的方式运行 Streamable HTTP（面向无状态客户端/部署） |

注意 `--http-host`/`--http-port` 是 MCP 服务器*监听*的地址 —— 它们与指向 *Blender* socket 服务器的 `--host`/`--port` 是相互独立的。

### 连接基于 URL 的客户端

把客户端的 `url` 指向启动时打印的端点：

**Cursor**（`~/.cursor/mcp.json`）：

```json
{
  "mcpServers": {
    "blender": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

**Visual Studio Code**（`.vscode/mcp.json`）：

```json
{
  "servers": {
    "blender": {
      "type": "http",
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

**Claude for Desktop**（通过 [mcp-remote](https://www.npmjs.com/package/mcp-remote)）：

```json
{
  "mcpServers": {
    "blender": {
      "command": "npx",
      "args": ["mcp-remote", "http://127.0.0.1:8000/mcp"]
    }
  }
}
```

**Codex**（`~/.codex/config.toml`，较新版本）：

```toml
[mcp_servers.blender]
url = "http://127.0.0.1:8000/mcp"
```

如果启用了 `BLENDER_MCP_HTTP_TOKEN`（见[安全须知](#安全须知)，请将其作为 `Authorization` 请求头发送。大多数基于 URL 的客户端都原生支持：

**Cursor：**

```json
{
  "mcpServers": {
    "blender": {
      "url": "http://127.0.0.1:8000/mcp",
      "headers": { "Authorization": "Bearer <你的token>" }
    }
  }
}
```

**Visual Studio Code：**

```json
{
  "servers": {
    "blender": {
      "type": "http",
      "url": "http://127.0.0.1:8000/mcp",
      "headers": { "Authorization": "Bearer <你的token>" }
    }
  }
}
```

**Claude for Desktop 的 mcp-remote：** 在上面的 `args` 中加入
`"--header", "Authorization: Bearer <你的token>"`。

### 在 Docker 中运行 HTTP 传输

容器内的服务器仍然绑定 `127.0.0.1`，而 `-p` 端口发布无法到达回环地址 —— 因此要让它绑定容器的网络接口，并把端口发布到*你的*回环地址上，使其仅对本机可见：

```bash
docker run --rm -p 127.0.0.1:8000:8000 -e BLENDER_MCP_HTTP_HOST=0.0.0.0 \
    mcp-for-blender --transport http
```

在 Linux 上，host 网络是更简单的做法（容器随后共享宿主机的回环地址，默认绑定即可工作，Blender 插件也无需额外参数即可访问 —— 见[使用 Docker 运行](#使用-docker-运行)）：

```bash
docker run --rm --network=host mcp-for-blender --transport http
```

如果将端口发布到宿主机回环之外（`-p 8000:8000`）且未设置 `BLENDER_MCP_HTTP_TOKEN`，就等于把 `execute_blender_code` 暴露给了你的网络；见下文[安全须知](#安全须知)。

### 预览、上传与下载（HTTP 附加服务）

通过 HTTP 传输启动时，服务器会在 MCP 端点旁边挂载一组普通 HTTP 路由，让浏览器——或任何脚本——无需 MCP 客户端也能参与设计流程：

| 端点 | 作用 |
|---|---|
| `GET /preview` | 面向人的实时页面：自动刷新的视口截图、**立即截图**按钮、拖拽上传素材、下载列表 |
| `GET /preview/latest.png` | 最近一次视口截图（PNG） |
| `POST /preview/capture` | 让 Blender 立即截取一张新截图 |
| `POST /upload/{filename}` | 把素材存到 Blender 所在机器 —— 请求体为**原始文件字节**（例如 `curl --data-binary @model.glb http://127.0.0.1:8000/upload/model.glb`） |
| `GET /files` | 以 JSON 列出 `uploads/`、`exports/` 和 `renders/` |
| `GET /files/{category}/{name}` | 下载某个文件 |
| `POST /files/uploads/{name}/import` | 把上传的文件导入场景 |

智能体同样能拿到这些 URL：`get_addon_status` 会在 `http_services` 字段中报告它们，`export_scene` / `render_scene` 的结果会带上 `/files` 下载链接——设计完成后智能体可以直接把预览或下载地址交给你。支撑这一切的是三个新工具：

- **`export_scene`** —— 把整个场景、当前选择或指定对象导出为 GLB/FBX，写入托管目录（即插件的 `export_scene` 命令，现在作为工具直接可用）。
- **`render_scene`** —— 真正的多角度渲染：为目标自动装配临时相机（front/right/top/three_quarter 或自定义方向），用场景自身的渲染引擎出图（包括 Cycles），每个角度一张全尺寸 PNG 存入托管目录，并在结果中附上缩放副本。
- **`import_file`** —— 从 Blender 所在机器导入文件：模型（`.glb/.gltf/.fbx/.obj/.ply/.stl/.dae/.abc/.usd*/.svg`）、其他 `.blend` 文件（追加其中对象）、图片和 HDRI 贴图。

所有文件放在一个托管目录中——默认 `~/.blender-mcp/files`，含 `uploads/`、`exports/`、`renders/` 三个子目录——因为插件与服务器需要共享同一个文件系统（截图本来就是通过临时路径传递的）。当容器端口映射导致对外地址不同时，用 `BLENDER_MCP_PUBLIC_URL` 指定对外 URL。

这些服务与 MCP 端点共用鉴权：设置 `BLENDER_MCP_HTTP_TOKEN` 后，这些路由既接受 `Authorization: Bearer` 请求头，也接受浏览器链接使用的 `?token=...`（服务器报告的 URL 已自动带上）。设置 `BLENDER_MCP_HTTP_SERVICES=0` 可以在保留 MCP-over-HTTP 的同时关闭这些服务。

### 安全须知

HTTP 端点会暴露所有工具，包括能在 Blender 内执行任意 Python 的
`execute_blender_code`。默认情况下没有鉴权：

- 服务器绑定到 `127.0.0.1` —— 除非你清楚风险，否则请保持如此。回环绑定同时保留了
  MCP SDK 的 DNS 重绑定（Host/Origin）校验；绑定更宽的地址会放宽这些校验、改由
  Bearer 令牌把关，若绑定超出回环且未设置令牌，服务器会在启动时打印警告。
- 要将其暴露到回环之外，请设置 `BLENDER_MCP_HTTP_TOKEN`（一串较长的随机字符）并把
  令牌交给客户端：此后服务器会拒绝任何未携带 `Authorization: Bearer <token>` 的
  请求，且失败尝试会被记录。没有 TLS —— 令牌在每个请求中都是明文传输 —— 因此请只在
  你信任的网络（回环、局域网、VPN）上使用；远程访问优先使用 SSH 隧道。
- 任何能访问该端点的人都可以在 Blender 中执行 Python，因此把端口开放在不受信任的
  网络上，等同于把你的机器交出去。

---

## 安装 Blender 插件

> `uvx mcp-for-blender setup`（见[快速开始](#快速开始)）会完成以下全部步骤，包括启用插件。以下步骤供手动操作。

**1. 推荐** —— 在终端运行：

```bash
uvx mcp-for-blender install-addon
```

该命令会把插件复制到你的 Blender 插件目录，命名为 `blender_mcp.py`。它会打印写入位置，并对被替换的文件保留 `.bak` 备份。

> 可选：`uvx mcp-for-blender addon-paths` 列出检测到的 Blender 插件目录。可用 `BLENDERMCP_ADDONS_DIR=/path/to/scripts/addons` 覆盖目标路径。

**2.** 打开 Blender

**3.** 进入 **Edit → Preferences → Add-ons**

**4.** 启用 **Interface: MCP for Blender**（搜索 "MCP for Blender"）。如果列表中还没有，点击 **Install…** 并选择已复制的 `blender_mcp.py` / `addon.py`，或重启 Blender。

**5. 手动替代方案** —— 如果上面的命令找不到你的 Blender 安装，或者你偏好手动操作：从本仓库下载 `addon.py` → 在 Blender 中，**Edit → Preferences → Add-ons → Install…** → 选择下载的 `addon.py` → 启用它。

然后在 Blender 侧边栏打开 **MCP for Blender** 标签页（在 3D 视口按 `N`），点击 **Start MCP Server**。见下文[启动连接](#启动连接)。

## 升级（现有用户）

> 新用户请直接看[快速开始](#快速开始)。老用户请看下文。

**1.** 运行：

```bash
uvx mcp-for-blender@latest update
```

该命令会更新 MCP 服务器（刷新 uv 的缓存副本，或升级 `uv tool install` 的安装）以及每一份已安装的 Blender 插件，并对被替换的文件保留 `.bak` 备份。它不会把比发布版更新的插件降级，也不会碰你本地改过的副本。可先加 `--dry-run` 预览将要改动的内容。

> 第一次请使用 `@latest`：早于 2.1.7 的版本没有 `update` 命令，而 uvx 缓存的可能正是旧版本。

**2.** 重启你的 MCP 客户端（Claude Desktop、Cursor 等），让它启动新的服务器。

**3.** 在 Blender 中：重启 Blender，或在 **Preferences → Add-ons** 中禁用再重新启用 **Interface: MCP for Blender**，然后再次点击 **Start MCP Server**。

如果某个客户端仍在使用旧的 `blender-mcp` 包名，`update` 会提示你；运行 `uvx mcp-for-blender setup` 即可完成切换。

> **注意：** MCP 服务器绝不会自行修改你的 Blender 插件文件。启动时它会检查已安装插件是否落后于随包版本，并打印更新方法；真正执行写入的是 `update` 和 `install-addon`。轨迹记录（trajectory capture）通过 `execute_code` 回退方案在较旧的已加载插件上仍然可用。

---

## 使用方法

### 启动连接

![侧边栏中的 MCP for Blender](assets/addon-instructions.png)

1. 在 Blender 中打开 3D 视图侧边栏（不可见时按 <kbd>N</kbd>）
2. 找到 **MCP for Blender** 标签页
3. 勾选你想使用的选项（更多说明见下文[功能一览](#功能一览)）
4. 点击 **Connect to Claude**
5. 确保终端里的 MCP 服务器正在运行

### 与 Claude 配合使用

配置文件设置到 Claude、插件在 Blender 中运行之后，你会看到一个带 MCP for Blender 工具的锤子图标。

![侧边栏中的 MCP for Blender](assets/hammer-icon.png)

### 功能一览

AI 会自己编写 Blender Python 来完成建模、布局、材质、动画、绑定和重构拓扑。MCP 补充了 Python 单独做不到的部分，共十二个工具：

| 工具 | 用途 |
|---|---|
| `execute_blender_code` | 在你运行中的 Blender 里执行 Python |
| `look` | 以 `viewport`（视口）、`camera`（相机）、`angles`（自动取景的多角度视图，方向任选）或 `frames`（动画条带）查看结果，绘制方式可选 `solid`、`material`、`rendered`、`wireframe` 或 `xray`；也可以展示渲染图或图片文件 |
| `render_scene` | 用场景自身的渲染引擎（含 Cycles）做多角度真实渲染，输出文件并附下载链接 |
| `export_scene` | 把场景、当前选择或指定对象导出为 GLB/FBX |
| `import_file` | 从 Blender 所在机器导入模型、图片或 HDRI（配合 HTTP 上传端点使用） |
| `get_scene_info` | 紧凑的场景摘要，每个对象一行，字段由你选择（位置、材质、拓扑、权重等）；可用 `root` 或 `query` 深入 |
| `generate_3d` | 一次调用即可用 Tripo、Hunyuan3D 或 Hyper3D Rodin 生成并导入模型；自动优先使用 Premium 生成器 |
| `search_assets` / `import_asset` | [Poly Haven](https://polyhaven.com/) 的 HDRI、纹理与模型，[Sketchfab](https://sketchfab.com/) 模型，[Poly Pizza](https://poly.pizza/) 低多边形模型 |
| `get_addon_status` | Blender 版本、插件版本、已启用的库和生成器，HTTP 传输下还会报告附加服务的 URL |
| `disable_telemetry`、`record_trajectory_feedback` | 数据收集控制 |

#### 腾讯云 Hunyuan3D（官方 API 模式）

插件调用哪个腾讯云服务取决于你的账号所在站点：

| 账号 | 插件调用的服务 | 地域 | 侧边栏开关 |
|---|---|---|---|
| 国内站（cloud.tencent.com） | AI3D 3.0（`ai3d`，版本 `2025-05-13`） | `ap-guangzhou` | 保持 **International (Pro) account** 不勾选（默认） |
| 国际站（tencentcloud.com），*Hunyuan-to-3D (Professional)* | `hunyuan`，版本 `2023-09-01`，启用 PBR | `ap-singapore` | 勾选 **International (Pro) account** |

国际站凭据发到国内站端点会报 `AuthFailure.SignatureFailure` 或
`ResourceUnavailable`，因此如果你的 SecretId/SecretKey 来自 tencentcloud.com，
请勾选该开关。开关位于侧边栏 **Tencent Hunyuan 3D → Official API** 之下。

#### Poly Haven

[Poly Haven](https://polyhaven.com/) 发布了约 2,400 个 HDRI、纹理和模型，全部采用 CC0
协议、完全免费，靠捐赠而非售卖资产维持运营。无需 API 密钥、无需账号，也没有值得
担心的速率限制。

在 3D 视图侧边栏勾选 **Poly Haven** 即可，配置到此结束。

实际示例：

> *“用阴天午后的 HDRI 给场景打光，并给墙面贴上生锈金属纹理”*

Claude 会调用 `search_assets(source="polyhaven", query="overcast afternoon", asset_type="hdris")`，
它理解的是意图而非关键词匹配 —— 搜 "couch" 能找到沙发，且支持任何语言。`previews=3`
会在消耗带宽之前附上最佳结果的缩略图；`import_asset(source="polyhaven", id="...", asset_type="textures", apply_to=["Wall"])`
一次调用即可下载纹理并应用。

搜索还可以按分类路径过滤，或按属性过滤 —— HDRI 支持天气、时段等，纹理支持表面用途
与新旧程度等；属性名写错时会报错并列出全部有效属性。

模型一律从 `.blend` 文件导入 —— 那是艺术家实际创作的文件，glTF、FBX 和 USD 版本都
是由它转换生成的，会丢失材质细节。纹理会基于驱动 Principled 材质的贴图组建材质，并
跳过那些没有任何东西读取的重新打包格式与备选约定。HDRI 会被打包进文件，因此光照在
保存并于别处重新打开后依然存在；它们会创建为新的世界环境，而不是覆盖你已建好的。

**许可与署名：** 所有 Poly Haven 资产均为 CC0。无论是否商用、用于什么，你都无需署名
任何人。不过他们的 [API 条款](https://github.com/Poly-Haven/Public-API/blob/master/ToS.md)
要求基于实时 API 构建的软件标明资产来源，因此搜索与导入响应会注明来源并链接资产页面。
导入时，`polyhaven_id`、`polyhaven_url`、`polyhaven_authors`、`polyhaven_resolution`
和 `polyhaven_licence` 会作为自定义属性写入导入的对象、材质、图像和世界环境，后续打
开 `.blend` 的人仍能找到资产及其作者。

#### Poly Pizza

[Poly Pizza](https://poly.pizza/) 收录了约 10,600 个免费低多边形模型，包括被抢救保存
的 Google Poly 存档。它是风格化游戏资产的最佳来源：每个模型都是单个自包含的
`.glb`，几何体也比 Sketchfab 轻量得多。

1. 在 [poly.pizza/settings/api](https://poly.pizza/settings/api) 获取免费 API 密钥
2. 在 3D 视图侧边栏勾选 **Use assets from Poly Pizza**
3. 将密钥粘贴到出现的 **API Key** 输入框（或在 **Edit → Preferences → Add-ons → MCP for Blender**
   中永久保存）

实际示例：

> *“在 Poly Pizza 搜索 CC0 许可的低多边形椅子，导入一个 1 米高的”*

Claude 会调用 `search_assets(source="polypizza", query="chair", licence="CC0")`，返回
每个匹配项的许可与三角面数，然后调用
`import_asset(source="polypizza", id="...", target_size=1.0)`。

也可以按分类过滤（`"Animals"`、`"Furniture & Decor"`、`"Transport"`、`"Nature"`、
`"Buildings"`、`"People & Characters"`、`"Food & Drink"`、`"Weapons"`、`"Clutter"`、
`"Objects"`、`"Scenes & Levels"`、`"Other"`），或只要动画模型。

**署名：** Poly Pizza 目录中约 69% 为 CC-BY，*要求*你在模型出现的任何地方署名创作者。
导入时，格式化好的署名文本会作为自定义属性 `polypizza_attribution` 写入每个导入的根
对象（旁边还有 `polypizza_id` 和 `polypizza_licence`），因此会随 `.blend` 保存、跨会
话保留。如果你只想用无需署名的模型，可用 `licence="CC0"` 过滤。

### 示例指令

以下是一些可以让 Claude 尝试的例子：

| 提示词 | 演示 |
|---|---|
| *"Create a low poly scene in a dungeon, with a dragon guarding a pot of gold"*（创建一个地牢低多边形场景，有一条龙守着一罐金子） | [观看](https://www.youtube.com/watch?v=DqgKuLYUv00) |
| *"Create a beach vibe using HDRIs, textures, and models like rocks and vegetation from Poly Haven"*（用 HDRI、纹理以及 Poly Haven 的岩石和植被模型营造海滩氛围） | [观看](https://www.youtube.com/watch?v=I29rn92gkC4) |
| 给一张参考图，据此创建 Blender 场景 | [观看](https://www.youtube.com/watch?v=FDRb03XPiRo) |
| *"Get information about the current scene, and make a threejs sketch from it"*（获取当前场景信息，并用 threejs 画个草图） | [观看](https://www.youtube.com/watch?v=jxbNI5L7AH8) |
| *"Generate a 3D model of a garden gnome through Hyper3D"*（用 Hyper3D 生成一个花园地精的 3D 模型） | |
| *"Fill this room with low-poly furniture from Poly Pizza"*（用 Poly Pizza 的低多边形家具填满这个房间） | |
| *"Make this car red and metallic"*（把这辆车变成红色金属材质） | |
| *"Create a sphere and place it above the cube"*（创建一个球体，放在立方体上方） | |
| *"Make the lighting like a studio"*（把灯光调成摄影棚风格） | |
| *"Point the camera at the scene, and make it isometric"*（把相机对准场景，调成等轴测视角） | |

---

## 持久化 API 凭据

MCP for Blender 支持通过 Blender 插件偏好设置持久化保存凭据：

**Edit → Preferences → Add-ons → MCP for Blender**

可以把以下值保存在那里，使其在 Blender 重启后仍然生效：

- Sketchfab API Key
- Poly Pizza API Key
- Hyper3D API Key
- Hunyuan3D SecretId / SecretKey
- Hunyuan3D API URL

对于无界面（headless）环境或 CI，凭据也可以通过环境变量注入：

| 变量 |
|---|
| `BLENDERMCP_SKETCHFAB_API_KEY` |
| `BLENDERMCP_POLYPIZZA_API_KEY` |
| `BLENDERMCP_HYPER3D_API_KEY` |
| `BLENDERMCP_HUNYUAN3D_SECRET_ID` |
| `BLENDERMCP_HUNYUAN3D_SECRET_KEY` |
| `BLENDERMCP_HUNYUAN3D_API_URL` |

---

## 故障排查

| 问题 | 解决办法 |
|---|---|
| **连接问题** | 确保 Blender 插件服务器正在运行，且 Claude 上已配置 MCP 服务器。**不要**在终端里手动运行 `uvx` 命令。有时第一次命令不会成功，之后就正常了。 |
| **超时错误** | 试着简化你的请求，或拆分成更小的步骤。 |
| **Poly Haven 下载期间 Blender 卡死** | 资产在 Blender 主线程上下载，传输完成前 UI 会暂时无响应。文件体积随分辨率档位大约翻四倍，除非资产离相机很近，否则建议选 1k 或 2k。 |
| **Poly Pizza 下载遇到 Cloudflare 质询** | `static.poly.pizza` 有反机器人防护，会拦截数据中心、VPN 和云主机 IP。你的 API 密钥没有问题 —— CDN 根本看不到它。换普通网络重试，或手动下载 `.glb` 后用 **File → Import → glTF 2.0**。 |
| **试过关掉再打开吗？** | 如果连接仍然报错，试着同时重启 Claude 和 Blender 服务器。 |

## 技术细节

### 通信协议

系统通过 TCP socket 使用简单的 JSON 协议：

- **命令**以 JSON 对象发送，包含 `type` 和可选的 `params`
- **响应**为 JSON 对象，包含 `status` 以及 `result` 或 `message`

## 限制与安全注意事项

> **警告：** `execute_blender_code` 工具允许在 Blender 中运行任意 Python 代码，功能
> 强大但也可能有危险。在生产环境中请谨慎使用。**使用前请务必保存你的工作。**

- Poly Haven 需要下载模型、纹理和 HDRI 图像。如果不想使用，请在 Blender 的复选框中关闭它。
- 复杂操作可能需要拆分成多个小步骤。

## 遥测控制

遥测为**自愿加入（opt-in）**。默认不收集你的内容，在你明确开启之前会保持关闭。

**默认收集的内容（无需加入）：** 一条最小化的匿名使用记录，用于统计活跃用户并了解哪些工具被使用 —— 包括随机生成的安装 ID、会话 ID、工具名称、是否成功、耗时、MCP for Blender 与 Blender 版本、操作系统和时间戳。

**未加入就绝不收集：** 你的提示词、生成的代码、视口截图、场景数据和轨迹数据。

**如何加入** —— 前往 **Edit → Preferences → Add-ons → MCP for Blender** 勾选遥测同意复选框。部分 MCP 客户端也会在对话开始时提供一次性加入提示。加入后，收集范围会扩展到提示词、生成的代码、截图和轨迹数据；详见条款（TnC）。你可以随时在同一位置关闭。

**彻底关闭遥测**（包括最小化的匿名使用记录），设置环境变量：

```bash
DISABLE_TELEMETRY=true uvx mcp-for-blender
```

或在 MCP 配置中添加：

```json
{
    "mcpServers": {
        "blender": {
            "command": "uvx",
            "args": ["mcp-for-blender"],
            "env": {
                "DISABLE_TELEMETRY": "true"
            }
        }
    }
}
```

遥测数据不与你的姓名或账号关联。它可能被用于改进 MCP for Blender、开展研究以及训练 AI 模型。

收集内容的完整说明，以及加入后授予的许可，见 [TERMS_AND_CONDITIONS.md](TERMS_AND_CONDITIONS.md)。

---

## 反馈

我们正在积极征集 MCP for Blender 的使用反馈。如有想法，请[在这里](https://bit.ly/blender-mcp-form)分享。

如果希望提供更详细的反馈，可以[在这里](https://bit.ly/blender-mcp-call)约个电话 —— 我们会在项目中致谢你。

### 加入社区

交流反馈、获取灵感、基于 MCP 进行构建：[**Discord**](https://discord.gg/SNqPn4TcKQ)

## 参与贡献

欢迎贡献！欢迎随时提交 Pull Request。

## 免责声明

本项目为第三方集成，并非由 Blender 官方出品。作者为 [Siddharth](https://x.com/sidahuj)。

---

## Star History

<a href="https://star-history.com/#ahujasid/blender-mcp&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=ahujasid/blender-mcp&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=ahujasid/blender-mcp&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=ahujasid/blender-mcp&type=Date" width="600" />
  </picture>
</a>

<div align="center">

**如果 MCP for Blender 对你有帮助，欢迎给仓库点个 Star**

</div>

