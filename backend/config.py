"""Gaussian DSH 插件后端配置。"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional


def _env_bool(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _env_path(name: str, default: Optional[str]) -> Optional[Path]:
    val = os.environ.get(name)
    if val is None or val == "":
        return Path(default) if default else None
    return Path(val)


# 本机默认 Gaussian 可执行文件（Gaussian 09W Rev C.01，32 位）。
# 使用 Gaussian 16 时用环境变量 GAUSSIAN_EXE=D:\G16W\g16.exe 覆盖即可。
DEFAULT_GAUSSIAN_EXE = r"D:\Gauss\g09w\g09.exe"


def gaussian_version_hint(exe: Optional[str]) -> Optional[str]:
    """按可执行文件名推断 Gaussian 主版本（不执行程序，纯字符串判断）。

    - g09.exe / g09w.exe / formchk(在 G09W 目录下) → "09"
    - g16.exe                                       → "16"
    返回主版本号字符串（"09"/"16"…），无法判断时返回 None。
    """
    if not exe:
        return None
    name = Path(str(exe)).name.lower()
    m = re.match(r"g(\d{2})\w*\.exe$", name)
    if m:
        ver = m.group(1)
        return "09" if ver == "09" else ver
    return None


class Settings:
    """运行时配置，可用环境变量覆盖。"""

    # Gaussian 可执行文件（默认见模块常量 DEFAULT_GAUSSIAN_EXE，可被 GAUSSIAN_EXE 覆盖）
    gaussian_exe: str = os.environ.get("GAUSSIAN_EXE", DEFAULT_GAUSSIAN_EXE)
    # formchk 可执行文件（Gaussian 工具，chk → fchk）
    formchk_exe: Optional[Path] = _env_path("FORMCHK_EXE", r"D:\Gauss\g09w\formchk.exe")
    # 默认工作目录（输入/输出/chk 存放），不存在时由 Settings.__init__ 创建
    work_dir: Path = Path(
        os.environ.get(
            "GAUSSIAN_WORK_DIR", r"D:\DSH\WorkZone\dsh-gauss-work"
        )
    )
    # 默认内存与核数（已按本机 G09W 实测结论设定）。
    # - G09 的 %mem 不接受小数：写 "1.5GB" 会报 "Error parsing percent card"，
    #   必须用整数 MB，故默认 "1000MB"；
    # - 本机 IA32W-G09RevC.01 在 %nprocshared=2 时会在 route 打印后直接退出
    #   （exit=1，无 Normal termination），%nprocshared=1 才能正常结束，故默认 1。
    # 使用 Gaussian 16 时可用 GAUSSIAN_DEFAULT_MEM=12GB / GAUSSIAN_DEFAULT_NPROC=8 覆盖。
    default_mem: str = os.environ.get("GAUSSIAN_DEFAULT_MEM", "1000MB")
    default_nproc: int = int(os.environ.get("GAUSSIAN_DEFAULT_NPROC", "1"))
    # 后端监听
    host: str = os.environ.get("GAUSSIAN_BACKEND_HOST", "127.0.0.1")
    port: int = int(os.environ.get("GAUSSIAN_BACKEND_PORT", "8765"))
    # Sobko 知识库项目路径（直接 import 检索引擎，不走 MCP 协议）
    sobko_project_dir: Optional[Path] = Path(
        os.environ.get("SOBKO_PROJECT_DIR", r"E:\YDW\Trae_Sob\Sobko_MCP_project-main")
    )
    # Sobko 检索模式：bm25_only（轻量，默认）或 hybrid（需 Ollama embedding + rerank）
    sobko_mode: str = os.environ.get("SOBKO_MODE", "bm25_only")
    # PyInstaller 冻结模式下，运行 Sobko 子进程使用的 Python 解释器
    sobko_python_exe: Optional[Path] = _env_path("SOBKO_PYTHON_EXE", None)
    # BSE 基组库 API
    bse_api_base: str = os.environ.get("BSE_API_BASE", "https://www.basissetexchange.org/api")
    # 数据目录（任务数据库、日志）
    data_dir: Path = Path(os.environ.get("GAUSSIAN_DATA_DIR", str(Path.home() / ".gaussian-dsh")))

    # ===== Multiwfn / VMD 后处理配置 =====
    multiwfn_exe: Optional[Path] = _env_path("MULTIWFN_EXE", r"D:\Multiwfn\Multiwfn_3.8_bin_Win64\Multiwfn.exe")
    vmd_exe: Optional[Path] = _env_path("VMD_EXE", r"D:\VMD\vmd.exe")
    # OpenBabel：用于从 mol/sdf/cdxml/xyz 等文件识别结构并转 SMILES（自动判键）。
    # 优先用插件内嵌 thirdparty/openbabel（便携），找不到再回退环境变量/本机路径。
    obabel_exe: Optional[Path] = None
    multiwfn_threads: int = int(os.environ.get("MULTIWFN_THREADS", "2"))
    postprocess_max_grid_points: int = int(
        os.environ.get("POSTPROCESS_MAX_GRID_POINTS", "16000000")
    )

    # ===== 后端内存监控 =====
    backend_rss_soft_mb: int = int(os.environ.get("BACKEND_RSS_SOFT_MB", "1024"))
    backend_rss_hard_mb: int = int(os.environ.get("BACKEND_RSS_HARD_MB", "1800"))

    # ===== Managed 模式 token（DSH 插件 spawn 时注入） =====
    managed_token: Optional[str] = os.environ.get("GAUSSIAN_MANAGED_TOKEN")

    # ===== M6 加固：大体系预检 =====
    # 原子数硬上限（超过直接拒绝，避免内存不足时排队后崩溃）
    max_atoms: int = int(os.environ.get("GAUSSIAN_MAX_ATOMS", "300"))

    # ===== 提交边界资源预算（validate_gjf 使用） =====
    # G09W 32 位程序单进程内存上限约 2GB：默认预算 2048MB，配合 default_mem=1000MB。
    # nproc 上限默认 2（可配置）；但本机 G09W 实测 >1 会崩溃，故 validate_gjf
    # 在 nproc>1 时会给出警告（不改硬校验、仍允许用户自己决定）。
    # 使用 Gaussian 16 时可放宽：GAUSSIAN_MEM_BUDGET_MB=12288 GAUSSIAN_MAX_NPROC=8。
    gaussian_mem_budget_mb: int = int(os.environ.get("GAUSSIAN_MEM_BUDGET_MB", "2048"))
    gaussian_max_nproc: int = int(os.environ.get("GAUSSIAN_MAX_NPROC", "2"))

    # ===== G09W 运行环境（GAUSS_EXEDIR / GAUSS_SCRDIR） =====
    # G09W 必须能找到 l1.exe 等辅助程序，否则报
    # "No executable for file l1.exe"（Search path GAUSS_EXEDIR is ""）。
    # 默认从 gaussian_exe 所在目录派生，也可用环境变量显式覆盖。
    gauss_exedir: Path = Path(
        os.environ.get(
            "GAUSS_EXEDIR",
            str(Path(os.environ.get("GAUSSIAN_EXE", DEFAULT_GAUSSIAN_EXE)).parent),
        )
    )
    # scratch 目录：默认 exe 目录下 Scratch；GAUSS_SCRDIR=-1 表示不注入该环境变量
    gauss_scrdir: Optional[Path] = _env_path(
        "GAUSS_SCRDIR",
        str(Path(os.environ.get("GAUSSIAN_EXE", DEFAULT_GAUSSIAN_EXE)).parent / "Scratch"),
    )

    # ===== M6 加固：Artifact GC（天） =====
    cube_ttl_days: int = int(os.environ.get("GC_CUBE_TTL_DAYS", "7"))
    image_ttl_days: int = int(os.environ.get("GC_IMAGE_TTL_DAYS", "30"))
    log_ttl_days: int = int(os.environ.get("GC_LOG_TTL_DAYS", "30"))
    gc_on_startup: bool = _env_bool("GC_ON_STARTUP", True)

    # ===== M6 加固：Multiwfn 期望版本（profile fail-fast） =====
    expected_multiwfn_version: str = os.environ.get("MULTIWFN_EXPECTED_VERSION", "3.8")

    def __init__(self) -> None:
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "logs").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "jobs").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "postprocess").mkdir(parents=True, exist_ok=True)
        self._prepare_gauss_env()
        self._resolve_obabel()

    def _prepare_gauss_env(self) -> None:
        """准备 G09W 运行环境：GAUSS_SCRDIR 不存在则尝试创建。

        创建失败不致命（可能是只读安装目录），只是运行时 Gaussian 会退回到
        默认 scratch；status 端点会如实报告目录是否存在。
        """
        scr = str(self.gauss_scrdir) if self.gauss_scrdir is not None else ""
        if not scr or scr.lower() in {"-1", "none", "off"}:
            return
        try:
            self.gauss_scrdir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    def _resolve_obabel(self) -> None:
        """定位 obabel.exe：内嵌 thirdparty > 环境变量 > 本机固定路径。"""
        import sys
        candidates = []
        if getattr(sys, "frozen", False):
            # exe: runtimes/win32-x64/gaussian-backend/gaussian-backend.exe
            # 内嵌: runtimes/win32-x64/openbabel/bin/obabel.exe
            exe_dir = Path(sys.executable).resolve().parent
            candidates.append(exe_dir.parent / "openbabel" / "bin" / "obabel.exe")
        else:
            # 开发模式：config.py 在 <root>/backend/config.py → root = parent.parent
            candidates.append(
                Path(__file__).resolve().parent.parent
                / "thirdparty" / "openbabel" / "bin" / "obabel.exe"
            )
        env = os.environ.get("OBABEL_EXE")
        if env:
            candidates.append(Path(env))
        candidates.append(Path(r"E:\openbabel-install-msvc\bin\obabel.exe"))
        for c in candidates:
            if c.exists():
                self.obabel_exe = c
                return
        self.obabel_exe = candidates[-1]


settings = Settings()
