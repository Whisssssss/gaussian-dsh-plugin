# Gaussian 09W 适配说明（本机 fork）

> 适用仓库：`D:\DSH\WorkZone\工作集\dsh-Gauss\gp-g09`（本地 fork，上游 github.com/yangdw2024/gaussian-dsh-plugin）。
> 本文记录把后端从“Gaussian 16 默认”改为“Gaussian 09W Rev C.01 默认、保留 G16 兼容”的改动、验证与遗留风险。
> 日期：2026-11-06。

## 1. 背景与本机事实

- 本机只有 **Gaussian 09W Rev C.01（IA32W，32 位）**：`D:\Gauss\g09w\g09.exe`（控制台）、`g09w.exe`（GUI）、`formchk.exe`、`cubegen.exe`、`freqchk.exe`；
- GaussView 5.0.8：`D:\Gauss\g09w\gview.exe`；
- **未安装 Multiwfn / VMD**（后处理出图不可用，属可选）；
- 后端原默认是作者机器的 `D:\G16W\g16.exe`、`%mem=12GB`、`%nprocshared=8`、工作目录 `E:\YDW\ChemDatas\Gjf`，在本机全部不可用。

### 1.1 Lead 在本机的实测结论（2026-11-06，决定默认值）

| 现象 | 结论 |
|------|------|
| `%mem=1.5GB` → `Error parsing percent card` | G09 的 `%mem` **只接受整数 MB**，默认改 `1000MB` |
| `%nprocshared=2` → route 打印后直接退出（exit=1，log 停在 `99/5=...`，无 Normal termination） | 本机 G09W **只能用 1 核**，默认改 `1` |
| `%nprocshared=1` HF/STO-3G H2 → Normal termination，E=-1.1167593 | 1 核可用 |
| 未设 `GAUSS_EXEDIR` → `No executable for file l1.exe`，`Search path GAUSS_EXEDIR is ""` | 后端启动 Gaussian 时必须注入 `GAUSS_EXEDIR=D:\Gauss\g09w` |
| 建议 scratch | `GAUSS_SCRDIR=D:\Gauss\g09w\Scratch`（后端自动创建） |

## 2. 改动清单（仅 backend/** + README.md + 本文档）

### `backend/config.py`

- `GAUSSIAN_EXE` 默认 → `D:\Gauss\g09w\g09.exe`；
- `FORMCHK_EXE` 默认 → `D:\Gauss\g09w\formchk.exe`；
- `GAUSSIAN_WORK_DIR` 默认 → `D:\DSH\WorkZone\dsh-gauss-work`（纯 ASCII，`Settings.__init__` 自动创建）；
- `GAUSSIAN_DEFAULT_MEM` 默认 → `1000MB`（G09 只接受整数 MB）；
- `GAUSSIAN_DEFAULT_NPROC` 默认 → `1`（G09W 多核实测崩溃）；
- 新增 `GAUSSIAN_MEM_BUDGET_MB`（默认 `2048`）与 `GAUSSIAN_MAX_NPROC`（默认 `2`），供 `validate_gjf` 做提交边界校验；
- 新增 `GAUSS_EXEDIR`（默认取 gaussian_exe 所在目录）与 `GAUSS_SCRDIR`（默认 exe 目录下 `Scratch`）；`Settings.__init__` 尝试创建 scratch（失败不致命，status 会如实报告）；
- 新增纯函数 `gaussian_version_hint(exe)`：按文件名推断 `09`/`16`（不执行 Gaussian）。

所有默认值仍可用环境变量覆盖（G16 用法见 README 配置表）。

### `backend/gaussian_input.py`

- 模块说明改为 G09/G16 通用；
- `generate_gjf`：G09 场景下把 `%mem=1.5GB` / 小数 MB **自动改写为整数 MB**（如 `1536MB`）并给出 warning；`%nprocshared>1` 时按 G09 给出“本机会崩溃”的 warning；
- `validate_gjf`：签名默认值由硬编码 `12288 / 8` 改为从 `settings` 惰性取（`GAUSSIAN_MEM_BUDGET_MB` / `GAUSSIAN_MAX_NPROC`），并**返回警告列表**（G09 下 nproc>1、%mem 写成小数/GB 等）；
- `validate_gjf` 错误文案不再写死“15.1GB 物理内存 / 12GB 预算”，改为解释 G09W 32 位约 2GB 上限与如何用环境变量放宽；
- word 单位换算注释补充：G09W 32 位 1 word=4B，代码按 8B 换算属 fail-closed（宁可误拒，不低估放行）。

### `backend/job_manager.py`

- `submit()` 调用 `validate_gjf` 时传入 `settings.gaussian_mem_budget_mb` / `settings.gaussian_max_nproc`，不再走 12GB/8 核默认；把校验警告写日志并随 `submit` 返回值返回（`warnings` 字段）；
- 启动 Gaussian 时构造子进程 env：`GAUSS_EXEDIR`（默认 g09.exe 目录）、`GAUSS_SCRDIR`（默认 Scratch），用 `setdefault` 不覆盖用户已有设置——修复 `No executable for file l1.exe`；
- 启动命令 `[settings.gaussian_exe, gjf, log]` 保持不变（G09 与 G16 接受相同形式）；注释由 g16.exe 改为 g09.exe/g16.exe；
- `_normalize_chk` 文档补充 G09 兼容性：`%NoSave`/`%Chk` 语义与 G16 一致（NoSave 只影响其之前命名的 scratch），顺序规范化对 G09W 安全；并注明中文工作目录的 ANSI 路径风险。

### `backend/gaussian_output.py`

- 模块说明补充 G09/G16 兼容点；
- 错误终止解析重写：捕获 `Error termination via Lnk1e in <exe> at <time>` 的同行信息（原实现取下一行会抓到 `Job cpu time`）；新增 `Error termination request processed by link 9999`（优化/IRC 未收敛）与 `Error termination in NtrErr` 识别；
- 优化步数：`Optimization cycle` 之外兼容 `Step number N out of a maximum of M`；
- 收敛判据正则修复：原正则未考虑 `Value  Threshold  Converged?` 的阈值列，标准 G09/G16 输出**永远匹配不到**；现在阈值列可选，`Maximum Force/RMS Force/...` 可正常解析并据此判定 `opt_converged`；
- 其余（`Normal termination of Gaussian`、`SCF Done`、`EUMP2`、`E(CCSD)`、`Alpha occ./virt. eigenvalues`、`Dipole moment`、`Frequencies --`、`Zero-point correction=`、`Thermal correction to ...`、`Job cpu time:`、`Elapsed time:`）经 G09 风格样本验证可直接复用，未改动。

### `backend/keywords.py`

- `scf=tight`：改为“G09/G16 默认都是 Tight”（原写“G09 默认是常规”不准确）；
- `int=fine`：注明 G09 默认 fine（75,302）、G16 默认改为 ultrafine（99,590）；
- `opt=calcfc`：补充 G09W 32 位 `%mem` 上限约 2GB、calcfc 易 OOM 的提示；
- `Out-of-memory` 条目：示例改为 `%mem=1000MB`（G09W），并说明 G16 可写 12GB；
- 新增错误条目：`link 9999`、`No executable for file l1.exe`；
- 新增分类 **“Gaussian 09W 注意”**：`%mem`、`%nprocshared`、`%nosave`、`%chk`、`GAUSS_EXEDIR`、`GAUSS_SCRDIR`。

### `backend/app.py`

- `_check_atom_count` 文案去掉“15GB/12GB 预算”硬编码，改为报告 `settings.gaussian_mem_budget_mb` 与 G09W 32 位说明；
- `GET /v1/status` 的 `gaussian` 块补充：`version`/`version_name`（按 exe 名推断 09/16）、`formchk_exe`/`formchk_exists`、`mem_budget_mb`、`max_nproc`、`gauss_exedir`(+exists)、`gauss_scrdir`(+exists)、`notes`（G09W 注意事项与环境变量提示）；不执行 Gaussian。

### `backend/memory_guard.py`

- 头部注释由“Gaussian 已占 12GB”改为“G09W 默认 %mem=1000MB（32 位上限约 2GB）”；阈值逻辑未改。

### `README.md`

- 标题/简介标注 G09W 本地适配版；工具表“需 Gaussian 16”改为“09W/16”；
- 前置条件改为 G09W 默认 + G16 二选一；默认 mem=1000MB / nproc=1 / GAUSS_EXEDIR / GAUSS_SCRDIR；
- 安装后配置表、配置表、快速测试、局限性同步更新。

## 3. 验证（本机实跑）

环境：Windows，Python 3.14.7；测试用 `GAUSSIAN_WORK_DIR` / `GAUSSIAN_DATA_DIR` / `GAUSS_SCRDIR` 指向临时目录，未污染真实目录、未执行 Gaussian。

### 3.1 语法编译

```
cd gp-g09 && python -m py_compile backend/config.py backend/app.py \
  backend/job_manager.py backend/gaussian_input.py backend/gaussian_output.py \
  backend/keywords.py backend/memory_guard.py
# → COMPILE_OK
```

### 3.2 默认值与 gjf 生成

```
gaussian_exe   : D:\Gauss\g09w\g09.exe
formchk_exe    : D:\Gauss\g09w\formchk.exe
default_mem    : 1000MB
default_nproc  : 1
mem_budget_mb  : 2048
max_nproc      : 2
gauss_exedir   : D:\Gauss\g09w
version_hint   : 09

苯 B3LYP/6-31G(d,p) opt 生成结果：
%mem=1000MB
%nprocshared=1
%nosave
%chk=benzene.chk
# B3LYP/6-31G(d,p) opt
（title、空行、0 1、12 行坐标、坐标块后恰好一个空行）
```

断言全部通过：`%nosave` 在 `%chk` 之前；内容以 `\n\n` 结尾且仅一个空行；`%mem`/`%nprocshared`/`%chk` 正确。

### 3.3 资源校验（validate_gjf）

| 输入 | 结果 |
|------|------|
| 默认 1000MB / 1 核 | 通过，无警告 |
| `%mem=12GB` | 拒绝：超过 2.00GB 预算（G09W 说明） |
| `%mem=1.5GB` | 通过（1536MB < 2048MB），返回“G09 只接受整数 MB，请改 1536MB”警告 |
| `%nprocshared=8` | 拒绝：超过上限 2 |
| `%nprocshared=2` | 通过（上限 2），返回“G09W >1 核会崩溃”警告 |
| 多重度 0 | 拒绝 |

### 3.4 G09 风格日志解析

构造含 `Normal termination of Gaussian 09`、`SCF Done`、`Alpha occ./virt. eigenvalues`、`Dipole moment`、`Frequencies --`、`Zero-point correction=`、`Thermal correction to Enthalpy/Gibbs Free Energy=`、`Job cpu time`、`Elapsed time`、`Step number` + 四行收敛判据的日志：

```
normal_termination: True      final_energy: -232.259728211
method: B3LYP                 basis: 6-31G(d,p)
atom_count: 12                basis_functions: 72
homo_energy: -11.234          lumo_energy: 0.12345    gap: 11.35745
dipole_moment: 0.0            frequencies: 6 个
opt_steps: 1                  opt_converged: True
zero_point_energy: 0.089324   thermal_enthalpy: 0.093456
thermal_free_energy: 0.06321  cpu_time/wall_time: 有值
```

错误样式：`Error termination via Lnk1e in C:\G09W\l1.exe at ...` → `error_message="Lnk1e: C:\G09W\l1.exe at ..."`；`Error termination request processed by link 9999.` → 识别为优化未收敛终止。

### 3.5 keywords 自检

`search_keywords("nprocs")` 命中新增分类“Gaussian 09W 注意”的 `%nprocshared`。

## 4. 由 Lead 负责、本任务未改动

- `gp-g09/src/**`（前端工具 schema 与提示词）、`package.json`、`cordis.patch.yml`、`runtimes/**`（打包后的 `gaussian-backend.exe`）；
- **重要**：`runtimes/win32-x64/gaussian-backend/gaussian-backend.exe` 是 PyInstaller 打包产物，本次后端源码改动**不会自动生效**，需要重新打包（或改用 external 模式直接跑 Python 源码）。

## 5. 遗留风险与建议

1. **打包 exe 未重建**：当前 runtimes 里的 exe 仍是旧默认值（G16/12GB/8 核），若继续用 managed 模式跑旧 exe，本适配不生效。需 Lead 重新打包。
2. **G09W 只能 1 核**：`%nprocshared>1` 在本机实测崩溃；`GAUSSIAN_MAX_NPROC` 默认 2 只是硬上限，用户传 2 会收到警告但不会被拒。若希望直接拒绝，可把 `GAUSSIAN_MAX_NPROC=1`。
3. **中文工作目录**：G09W 是 ANSI 程序，部分版本对非 ASCII 路径报 `File operation error`。默认已改为纯 ASCII `D:\DSH\WorkZone\dsh-gauss-work`；若自行改到含中文路径需注意。已在 README 与 job_manager 注释标注。
4. **本机缺少 fastapi/pydantic/psutil/rdkit**：`backend.app` 与 `backend.job_manager` 只做了 `py_compile` 语法验证，未做运行时端到端导入测试（依赖缺包）。纯逻辑模块（config/gaussian_input/gaussian_output/keywords）已实测。
5. **formchk → fchk**：默认路径已改 `D:\Gauss\g09w\formchk.exe`，但本机无 Multiwfn，未做 chk→fchk 端到端验证；G09 的 fchk 格式与 G16 略有差异，后续若接后处理需确认 `fchk_reader.py` 兼容。
6. **%nosave 语义**：G09 与 G16 一致（NoSave 之前命名的 scratch 会被删除），`_normalize_chk` 保证 `%nosave` 在 `%chk` 前，对 G09W 安全；但 G09 的 `%nosave` 在任务结束时会删除 rwf 等临时文件，长时间任务请确保 scratch 空间足够。
7. **G16 路径未实机复测**：只保留配置入口（`GAUSSIAN_EXE` / `GAUSSIAN_DEFAULT_MEM` / `GAUSSIAN_DEFAULT_NPROC` / `GAUSSIAN_MEM_BUDGET_MB` / `GAUSSIAN_MAX_NPROC`），未在本机验证。
8. **G09W 与 GaussView**：GaussView 5.0.8 不在插件调用链内，用户手动看图不影响后端。
