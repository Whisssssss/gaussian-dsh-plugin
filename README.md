# gaussian-dsh-plugin（Gaussian 09W 本地适配版）

> 一个在 [DSH (DeepSeek Harness)](https://github.com/) 客户端里运行的 Gaussian 计算辅助插件，把 Gaussian、RDKit、Multiwfn、VMD 串成一条 AI 可调用的工具链。
>
> **本 fork 默认面向本机 Gaussian 09W Rev C.01（32 位）**，同时保留 Gaussian 16 支持（改环境变量即可切换）。
>
> A DSH (DeepSeek Harness) plugin that turns Gaussian 09W/16, RDKit, Multiwfn and VMD into an AI-callable toolchain.

---

## 这是什么 / What it does

你用自然语言跟 DSH 说一句"帮我优化这个分子"，插件会自动：

- SMILES / ChemDraw 文件 → 3D 建模 → 生成 Gaussian `.gjf` 输入；
- 串行提交 Gaussian 计算（防止在多核机器上并行跑崩）；
- 解析 `.out/.log`（能量、收敛、HOMO-LUMO、偶极、频率、热力学量）；
- 算完自动调 Multiwfn + VMD 出 **HOMO/LUMO 轨道图、ESP 表面图、RDG/NCI 弱相互作用图**。

You just talk to DSH in natural language. The plugin handles:
SMILES/ChemDraw file → 3D geometry → Gaussian input → serial job →
output parsing → Multiwfn/VMD post-processing (orbitals / ESP / RDG).

## 功能工具 / Tools

| 工具 | 作用 | 是否开箱即用 |
|------|------|-------------|
| `gaussian_status` | 后端与 Gaussian 可执行文件状态 | 需本机有 Gaussian 09W/16 |
| `generate_gaussian_input` | 生成 `.gjf`（校验方法/基组） | ✅ 开箱即用 |
| `generate_gaussian_input_from_smiles` | SMILES → RDKit 3D → Gaussian 输入 | ✅ 开箱即用 |
| `extract_structure_from_file` | 从 `.mol/.cdxml/.gjf/.out/.log/.xyz/.pdb` 识别 SMILES | ✅ 开箱即用 |
| `submit_gaussian_job` / `get_gaussian_job` / `list_gaussian_jobs` / `stop_gaussian_job` | 任务管理（串行） | 需本机有 Gaussian 09W/16 |
| `parse_gaussian_output` | 解析能量/收敛/HOMO-LUMO/频率/热力学 | ✅ 开箱即用 |
| `search_basis_sets` / `get_basis_set` | BSE 官方基组库（在线 API） | ✅ 联网即用 |
| `search_gaussian_keywords` | Gaussian 关键词查询 | ✅ 开箱即用 |
| `diagnose_gaussian_error` | 常见报错诊断 | ✅ 开箱即用 |
| `postprocess_capabilities` | 探测 Multiwfn/VMD/formchk 是否就绪 | 需自行安装后处理软件 |
| `create_postprocess_task` / `get_postprocess_task` / `list_postprocess_tasks` | 轨道/ESP/RDG 出图（异步） | 需 Multiwfn + VMD |
| `sobko_search` / `sobko_fetch` | 检索本地 Sobko 知识库 | ❌ 作者本地专用，需自行部署 |

> 共 **19 个工具**。RDKit 和 OpenBabel 已随插件打包，目标机**无需**单独安装 Python/RDKit/OpenBabel。

## 前置条件 / Prerequisites

插件本身自带后端（已编译为 exe，含 RDKit/OpenBabel），但以下专业软件需要你自己装在本机：

### 必需（不装则部分功能不可用）

- **Gaussian 09W Rev C.01**（`g09.exe` + `formchk.exe`）—— 商业软件，需自行购买授权，**本 fork 默认配置**
  - 默认路径：`D:\Gauss\g09w\g09.exe`、`D:\Gauss\g09w\formchk.exe`
  - **G09W 是 32 位程序**：`%mem` 只接受整数 MB（默认 `1000MB`），且实测 `%nprocshared>1` 会在 route 打印后直接退出，默认必须 `%nprocshared=1`
  - 运行时必须让 `GAUSS_EXEDIR` 指向 `g09.exe` 所在目录（`D:\Gauss\g09w`），否则报 `No executable for file l1.exe`；插件后端会自动注入，也可在系统环境变量里手动设置
  - 可选：`GAUSS_SCRDIR` 指定 scratch 目录（默认 `D:\Gauss\g09w\Scratch`，由插件自动创建）

- **或 Gaussian 16**（`g16.exe` + `formchk.exe`）—— 二选一
  - 改环境变量：`GAUSSIAN_EXE=D:\G16W\g16.exe`、`FORMCHK_EXE=D:\G16W\formchk.exe`、`GAUSSIAN_DEFAULT_MEM=12GB`、`GAUSSIAN_DEFAULT_NPROC=8`
  - 同时放宽资源校验：`GAUSSIAN_MEM_BUDGET_MB=12288`、`GAUSSIAN_MAX_NPROC=8`

### 可选（不装则后处理出图不可用，但生成输入/解析输出仍可用）

- **Multiwfn ≥ 3.8**（http://sobereva.com/multiwfn/ ，免费学术使用）
  - 装完后设置 `MULTIWFN_EXE` 指向 `Multiwfn.exe`
- **VMD**（https://www.ks.uiuc.edu/Research/vmd/ ）
  - 装完后设置 `VMD_EXE` 指向 `vmd.exe`

### 不需要装的（已打包）

- ✅ Python 运行时（后端 exe 内置）
- ✅ RDKit（已编译进后端 exe）
- ✅ OpenBabel（在 `runtimes/win32-x64/openbabel/` 里）

> 硬件/默认值：本机 15.1GB 内存。**G09W 默认 `%mem=1000MB` / `%nprocshared=1`**（32 位程序上限约 2GB，实测多核会崩）；
> 若切到 Gaussian 16，用环境变量改成 `12GB` / `8` 核。任务串行执行，不要并行提交多个 Gaussian 任务。

## 安装 / Installation

### 方式 A：从 npm 安装（推荐）

在 DSH 客户端 → 插件 → 添加插件，搜索包名安装：

```
@yangdw2024/gp
```

后端 exe 已随 npm 包携带，无需单独下载。

> 包名说明：npm 上的正式包名是 `@yangdw2024/gp`。这是短包名——DSH 会根据包名生成快照目录，包名太长会触发 Windows MAX_PATH 260 限制导致后端启动失败。

### 方式 B：从 GitHub Release 下载

1. 到 [Releases 页面](https://github.com/yangdw2024/gaussian-dsh-plugin/releases) 下载最新的 `gaussian-dsh-plugin-vX.X.X-win32-x64.zip`
2. 解压到**短路径**（例如 `D:\plugins\gaussian-dsh\`，不要放在深层目录或含空格/中文的路径下）
3. DSH → 设置 → 插件 → 添加插件 → 选择解压后的目录

### 安装后配置

本 fork 的默认值已改成本机 G09W 路径，**本机开箱即用**；如果换机器或换 Gaussian 版本，用环境变量覆盖：

| 环境变量 | 本机默认 | 指向 |
|----------|----------|------|
| `GAUSSIAN_EXE` | `D:\Gauss\g09w\g09.exe` | Gaussian 主程序（G16 改为 `D:\G16W\g16.exe`） |
| `FORMCHK_EXE` | `D:\Gauss\g09w\formchk.exe` | chk → fchk |
| `GAUSS_EXEDIR` | `D:\Gauss\g09w` | G09W 辅助程序目录（l1.exe 等），**G09W 必需** |
| `GAUSS_SCRDIR` | `D:\Gauss\g09w\Scratch` | G09W scratch 目录 |
| `GAUSSIAN_WORK_DIR` | `D:\DSH\WorkZone\dsh-gauss-work` | 输入/输出/chk 工作目录（建议用纯 ASCII 路径，G09W 对中文路径敏感） |
| `GAUSSIAN_DEFAULT_MEM` | `1000MB` | Gaussian 内存（G09W 只接受整数 MB；G16 可写 `12GB`） |
| `GAUSSIAN_DEFAULT_NPROC` | `1` | 核数（G09W 多核实测会崩；G16 可写 8） |
| `MULTIWFN_EXE` | `D:\Multiwfn\...\Multiwfn.exe` | Multiwfn（可选，本机未安装） |
| `VMD_EXE` | `D:\VMD\vmd.exe` | VMD（可选，本机未安装） |

设完环境变量后，**完全退出 DSH（托盘退出、进程结束）再重开**。

## 快速测试 / Quick test

装好后跟 DSH 说：

> 用 `gaussian_status` 查后端状态（确认 `gaussian.version` 为 `09`、`gauss_exedir` 存在、`default_mem=1000MB`、`default_nproc=1`）。然后用 SMILES `c1ccccc1`（苯）生成一个 B3LYP/6-31G(d,p) 的优化输入，先不要提交。

如果 `gaussian_status` 返回 `status: ok`，说明后端已正常拉起。本机未安装 Multiwfn/VMD，`postprocess_capabilities` 里这两项为 `false` 属预期。

## 配置 / Configuration

默认值已按本机 G09W 设定，**不一致就用环境变量覆盖**（重启后端 / 完全退出重启 DSH 生效）。

| 环境变量 | 默认（G09W） | 说明 |
|----------|--------------|------|
| `GAUSSIAN_BACKEND_MODE` | `managed` | `managed`=插件自行拉起后端；`external`=复用已运行的外部后端 |
| `GAUSSIAN_BACKEND_URL` | `http://127.0.0.1:8765` | external 模式下连接的后端地址 |
| `GAUSSIAN_EXE` | `D:\Gauss\g09w\g09.exe` | Gaussian 主程序（G16 改 `D:\G16W\g16.exe`） |
| `FORMCHK_EXE` | `D:\Gauss\g09w\formchk.exe` | chk → fchk |
| `GAUSS_EXEDIR` | `D:\Gauss\g09w` | G09W 辅助程序目录（未设置会报 `No executable for file l1.exe`） |
| `GAUSS_SCRDIR` | `D:\Gauss\g09w\Scratch` | G09W scratch 目录（后端会自动创建） |
| `GAUSSIAN_MEM_BUDGET_MB` | `2048` | `%mem` 校验预算（G09W 32 位上限约 2GB；G16 设 12288） |
| `GAUSSIAN_MAX_NPROC` | `2` | `%nprocshared` 硬校验上限（G09W 默认用 1；G16 设 8） |
| `GAUSSIAN_MAX_ATOMS` | `300` | 原子数硬上限 |
| `MULTIWFN_EXE` | `D:\Multiwfn\Multiwfn_3.8_bin_Win64\Multiwfn.exe` | Multiwfn（可选） |
| `VMD_EXE` | `D:\VMD\vmd.exe` | VMD（可选） |
| `GAUSSIAN_WORK_DIR` | `D:\DSH\WorkZone\dsh-gauss-work` | 输入 / 输出 / chk 工作目录 |
| `GAUSSIAN_DATA_DIR` | `%USERPROFILE%\.gaussian-dsh` | 任务记录 / 后处理产物 / 日志目录 |
| `GAUSSIAN_DEFAULT_MEM` | `1000MB` | Gaussian 内存（G09W 只接受整数 MB） |
| `GAUSSIAN_DEFAULT_NPROC` | `1` | 核数（G09W 保持 1；串行，勿并行） |

> 版本探测：`gaussian_status`（`GET /v1/status`）按可执行文件名报告 `Gaussian 09/16`、
> `formchk`/`GAUSS_EXEDIR`/`GAUSS_SCRDIR` 是否存在，并给出 G09W 注意事项，不会执行 Gaussian。

## 局限性 / Limitations

- 本 fork 在 **Windows + Gaussian 09W Rev C.01（IA32W，32 位）** 上适配与验证；G16 路径保留但未在实机复测；
- G09W 实测：`%nprocshared>1` 会在 route 打印后直接退出，**只能用 1 核**；`%mem` 只接受整数 MB；
- 本机未安装 **Multiwfn / VMD**，后处理出图（轨道/ESP/RDG）不可用；生成输入、解析输出、能量/频率/热力学解析不受影响；
- `sobko_search` / `sobko_fetch` 两个工具依赖作者本地部署的知识库（Ollama + 1700 篇论文索引），**其他用户这两个工具不可用**，忽略即可；
- G09W 是 ANSI 程序，工作目录路径务必用纯 ASCII（本机默认已改为 `D:\DSH\WorkZone\dsh-gauss-work`），若自行改到含中文路径，个别版本可能报 File operation error；
- Gaussian/Multiwfn/VMD 是商业/专有软件，本插件不包含它们，也不提供下载。

## 许可 / License

[MIT](./LICENSE)。本插件本身开源，但调用的 Gaussian 归 Gaussian Inc.、Multiwfn 归 Tian Lu、VMD 归 UIUC，各自遵循其许可。
