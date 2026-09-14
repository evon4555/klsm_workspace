# QA Workspace 部署配置文档

## 用途

给 Team Lead 和新组员使用，在新的 Windows 电脑上部署 QA Workspace。

仓库：`https://github.com/evon4555/klsm_workspace.git`

## 前置条件

- Windows 10/11 或 Windows Server 2019+
- Git
- Python 3.10+
- Node.js 18+
- 至少 1.5 GB 可用空间，建议 5 GB
- 可访问 GitHub、Python 包源、npm 包源和组件下载地址

真实账号、密码、API Key、Cookie 和 token 只保存在本机或秘密管理系统，不提交 Git。

## 新人部署

### 1. 确认软件

```powershell
git --version
python --version
node --version
npm --version
```

### 2. 克隆仓库

```powershell
git clone https://github.com/evon4555/klsm_workspace.git
cd klsm_workspace\qa-harness
```

### 3. 安装平台

```powershell
.\bootstrap.ps1
```

脚本会创建 Python 虚拟环境，安装 Python、前端和 Playwright 依赖，并安装 Prometheus、Loki、Grafana。组件位置是 `D:\prometheus`、`D:\loki`、`D:\grafana`。

需要重新下载组件时：

```powershell
.\bootstrap.ps1 -Force
```

### 4. 配置项目环境

模板位于：

```text
west-kowloon\02-automation\06-envs\.env.example
standard product\02-automation\06-envs\.env.example
```

按项目复制模板，在本机创建 `.env.local`、`.env.sit` 或 `.env.uat`，再由 Team Lead 提供授权变量值。填写后的文件不要上传。

### 5. 启动验证

```powershell
.\smoke-docs.ps1
.\start-all.bat
```

打开 `http://127.0.0.1:5174` 检查 Dashboard。停止服务：

```powershell
.\stop-all.bat
```

## Team Lead 验收清单

| 项目 | 记录内容 |
| --- | --- |
| 使用人 | 姓名 / 工号 |
| 电脑 | 主机名 / Windows 版本 |
| 仓库 | clone 路径和当前 commit |
| 软件 | Git、Python、Node 版本 |
| 安装 | bootstrap 成功时间 |
| 验证 | smoke-docs 结果 |
| Dashboard | 5174 是否可访问 |
| 范围 | API / UI / Dashboard / 文档 |
| 环境 | 已配置环境，不记录密码 |
| 验收 | Team Lead 和日期 |

检查命令：

```powershell
cd <clone路径>\klsm_workspace\qa-harness
git status --short --branch
git log -1 --oneline
```

确认分支为 `main`、工作区没有未授权修改，commit 与团队指定版本一致。

## 日常更新

```powershell
cd <clone路径>\klsm_workspace
git pull --ff-only
cd qa-harness
.\bootstrap.ps1
.\smoke-docs.ps1
```

有未提交修改时，先提交到个人分支或备份。

## 常见问题

### Python 或 Node 未找到

安装 Python 3.10+ 或 Node.js 18+，加入 PATH 后重新打开 PowerShell。

### 脚本被阻止

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\bootstrap.ps1
```

### GitHub 无法连接

```powershell
git ls-remote https://github.com/evon4555/klsm_workspace.git
```

检查公司网络、代理和 GitHub 登录状态。

### 缺少环境变量

从 `.env.example` 创建本机文件，并联系 Team Lead 获取授权配置，不要复制其他组员的完整 `.env`。

## 责任边界

- Team Lead 负责发布 commit、环境变量分发、机器验收和权限回收。
- 组员负责部署、保存本机配置、更新前报告未提交修改。
- 依赖版本以 `bootstrap.ps1`、`pyproject.toml` 和前端 `package.json` 为准。
