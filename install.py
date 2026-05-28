#!/usr/bin/env python3
import subprocess
import sys
import os
import shutil
import json
from pathlib import Path


PYTHON_MIN = (3, 10)

PIP_MIRRORS = {
    "aliyun": "https://mirrors.aliyun.com/pypi/simple",
    "tsinghua": "https://pypi.tuna.tsinghua.edu.cn/simple",
    "douban": "https://pypi.douban.com/simple",
    "official": "https://pypi.org/simple",
}

WELCOME = r"""
╔══════════════════════════════════════════════╗
║         lmpsmart Installation Wizard          ║
║   LAMMPS Data Agent — Smart Installer        ║
╚══════════════════════════════════════════════╝
"""


def run(cmd, capture=True, shell=True):
    try:
        if capture:
            r = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
            return r.stdout.strip(), r.stderr.strip(), r.returncode
        else:
            r = subprocess.run(cmd, shell=shell)
            return "", "", r.returncode
    except Exception as e:
        return "", str(e), 1


def detect_pythons():
    results = []

    # 1. conda envs
    out, _, rc = run("conda env list --json")
    if rc == 0:
        try:
            envs = json.loads(out)
            for name, path in envs.items():
                p = Path(path) / "python.exe" if os.name == "nt" else Path(path) / "bin" / "python"
                if p.exists():
                    ver = get_python_ver(str(p))
                    results.append(("conda", name, str(p), ver))
        except Exception:
            pass

    # 2. venv / virtualenv in current dir
    for v in Path(".").glob("venv*"):
        p = v / "Scripts" / "python.exe" if os.name == "nt" else v / "bin" / "python"
        if p.exists():
            ver = get_python_ver(str(p))
            results.append(("venv", v.name, str(p), ver))

    # 3. pyenv (Linux/macOS)
    if os.name != "nt":
        out, _, rc = run("pyenv versions --bare")
        if rc == 0:
            pyenv_root, _, _ = run("pyenv root")
            for name in out.splitlines():
                name = name.strip()
                if not name:
                    continue
                p = Path(pyenv_root) / "versions" / name / "bin" / "python"
                if p.exists():
                    ver = get_python_ver(str(p))
                    results.append(("pyenv", name, str(p), ver))

    # 4. system python
    for name in ["python3.12", "python3.11", "python3.10", "python", "python3"]:
        p = shutil.which(name)
        if p:
            ver = get_python_ver(p)
            if ver and ver >= PYTHON_MIN:
                results.append(("system", name, p, ver))
            break

    # deduplicate by path
    seen = {}
    for kind, name, path, ver in results:
        if path not in seen:
            seen[path] = (kind, name, ver)
    return [(k, n, p, v) for p, (k, n, v) in seen.items()]


def get_python_ver(path):
    try:
        out, _, rc = run(f'"{path}" -c "import sys; print(sys.version_info.major, sys.version_info.minor)"')
        if rc == 0:
            parts = out.split()
            if len(parts) >= 2:
                return (int(parts[0]), int(parts[1]))
    except Exception:
        pass
    return None


def create_conda_env(name="lmpsmart", pyver="3.12"):
    print(f"\n[1/3] Creating conda environment: {name} (Python {pyver})")
    _, err, rc = run(f'conda create -y -n {name} python={pyver} -c conda-forge')
    if rc != 0:
        print(f"  [ERROR] conda create failed: {err}")
        return None
    out, _, rc = run(f'conda env list --json')
    if rc == 0:
        envs = json.loads(out)
        path = envs.get(name)
        if path:
            p = Path(path) / "python.exe" if os.name == "nt" else Path(path) / "bin" / "python"
            if p.exists():
                print(f"  [OK] Environment created: {path}")
                return str(p)
    # fallback
    p = Path(sys.prefix.replace("\\", "/")) / "envs" / name / "python.exe" if os.name == "nt" else Path(f"~/.conda/envs/{name}/bin/python").expanduser()
    if p.exists():
        return str(p)
    return None


def create_venv(path="venv"):
    print(f"\n[1/3] Creating venv: {path}")
    _, err, rc = run(f'python -m venv {path}')
    if rc != 0:
        print(f"  [ERROR] venv create failed: {err}")
        return None
    p = Path(path) / "Scripts" / "python.exe" if os.name == "nt" else Path(path) / "bin" / "python"
    if p.exists():
        print(f"  [OK] venv created: {path}")
        return str(p)
    return None


def install_deps(python_path, extras=True, mirror_url=None):
    print(f"\n[2/3] Installing dependencies with: {python_path}")
    pip = f'"{python_path}" -m pip'
    index_arg = f" -i {mirror_url}" if mirror_url else ""

    _, err, rc = run(f"{pip} install --upgrade pip{index_arg}")
    if rc != 0:
        print(f"  [WARN] pip upgrade failed (continuing): {err}")

    root = Path(__file__).parent.absolute()
    _, err, rc = run(f"{pip} install -e {root}{index_arg}")
    if rc != 0:
        print(f"  [ERROR] Package install failed: {err}")
        return False
    print(f"  [OK] lmpsmart installed (core deps included)")

    if extras:
        opt = "pykalman pywavelets matplotlib"
        print(f"  Installing optional packages (all smoothers)...")
        _, err, rc = run(f"{pip} install {opt}{index_arg}")
        if rc == 0:
            print(f"  [OK] All smoothers available")
        else:
            print(f"  [WARN] Some optional deps failed (non-critical)")

    return True


def install_package(python_path, mirror_url=None):
    pass


def verify(python_path):
    print(f"\n[VERIFY] Running verification...")
    _, err, rc = run(f'"{python_path}" -m lmpsmart config --show')
    if rc == 0:
        print(f"  [OK] lmpsmart is working correctly!")
        return True
    else:
        print(f"  [WARN] Verification failed:\n  {err}")
        return False


def offer_llm_config():
    print("\n" + "=" * 50)
    print("  LLM Configuration (optional)")
    print("=" * 50)
    print("  You can configure LLM later with:")
    print("    python -m lmpsmart llm setup --provider local --model qwen3:8b")
    print("  Or skip for now — keyword fallback is always available.")
    print()
    while True:
        ans = input("  Configure LLM now? [y/N]: ").strip().lower()
        if ans in ("n", ""):
            print("  [SKIP] LLM config skipped. Run `llm setup` later anytime.")
            return
        if ans == "y":
            print("\n  Choose provider:")
            print("    1) local  — Ollama (local/LAN, no API key needed)")
            print("    2) online — OpenRouter / OpenAI (requires API key)")
            while True:
                p = input("  Choice [1]: ").strip()
                if p in ("", "1"):
                    prov, base_url, model = "local", "http://localhost:11434", "qwen3:8b"
                    break
                if p == "2":
                    base_url = input("    Base URL [https://openrouter.ai/api/v1]: ").strip()
                    if not base_url:
                        base_url = "https://openrouter.ai/api/v1"
                    api_key = input("    API Key (sk-or-xxx / sk-xxx): ").strip()
                    model = input("    Model [anthropic/claude-3-haiku]: ").strip()
                    if not model:
                        model = "anthropic/claude-3-haiku"
                    prov = "online"
                    break
                print("    Invalid choice.")
            cmd = f'"{python_path}" -m lmpsmart llm setup --provider {prov} --base-url {base_url} --model {model}'
            if prov == "online":
                cmd += f' --api-key {api_key}'
            print(f"\n  Running: {cmd}")
            out, err, rc = run(cmd)
            if rc == 0:
                print(f"  [OK] LLM configured: {out}")
            else:
                print(f"  [WARN] LLM config failed: {err}")
            return
        print("  Please enter y or n.")


def main():
    print(WELCOME)

    root = Path(__file__).parent.absolute()
    print(f"Project root: {root}\n")

    # Step 0: check if already installed
    try:
        out, _, rc = run(f'"{sys.executable}" -m lmpsmart config --show')
        if rc == 0:
            print("[FOUND] lmpsmart is already installed!")
            print("  Run `pip install -e .` in the project root to update.")
            return
    except Exception:
        pass

    # Step 0b: select pip mirror
    print("[MIRROR] Select PyPI mirror (for faster download in China):")
    mirror_keys = list(PIP_MIRRORS.keys())
    for i, k in enumerate(mirror_keys):
        tag = " (default)" if k == "aliyun" else ""
        print(f"  {i + 1}. {k}{tag}")
    sel = input(f"Select [1]: ").strip() or "1"
    try:
        idx = int(sel) - 1
        if 0 <= idx < len(mirror_keys):
            mirror_key = mirror_keys[idx]
        else:
            mirror_key = "aliyun"
    except ValueError:
        mirror_key = "aliyun"
    mirror_url = PIP_MIRRORS[mirror_key]
    print(f"  Using: {mirror_url}\n")

    # Step 1: detect environments
    print("[STEP 1] Detecting Python environments...")
    envs = detect_pythons()
    if envs:
        print(f"  Found {len(envs)} Python environment(s):")
        for i, (kind, name, path, ver) in enumerate(envs):
            tag = " (current)" if path == sys.executable else ""
            print(f"  {i + 1}. [{kind}] {name} {ver}{tag}")
            print(f"     {path}")
    else:
        print("  No compatible Python found.")

    print()
    print("  A) Use an existing environment")
    print("  B) Create new conda env (Python 3.12)")
    print("  C) Create new venv (in project dir)")
    print("  Q) Quit")

    choice = ""
    selected_python = None

    while choice not in ("A", "B", "C", "Q", "q", "a", "b", "c"):
        choice = input("\nSelect option [A]: ").strip()

    if choice.lower() == "q":
        print("Cancelled.")
        return

    if choice.lower() in ("a", ""):
        if envs:
            print("\nSelect environment:")
            for i, (kind, name, path, ver) in enumerate(envs):
                print(f"  {i + 1}. [{kind}] {name} {ver}")
            while True:
                sel = input(f"Select [1-{len(envs)}]: ").strip()
                if not sel:
                    sel = "1"
                try:
                    idx = int(sel) - 1
                    if 0 <= idx < len(envs):
                        selected_python = envs[idx][2]
                        break
                except ValueError:
                    pass
                print("Invalid selection.")
        else:
            print("  No existing envs. Creating conda env instead.")
            choice = "B"

    if choice.lower() in ("b", ""):
        name = input("  Conda env name [lmpsmart]: ").strip() or "lmpsmart"
        pyver = input("  Python version [3.12]: ").strip() or "3.12"
        selected_python = create_conda_env(name, pyver)
        if not selected_python:
            print("  [ERROR] Conda env creation failed.")
            return

    if choice.lower() == "c":
        venv_path = input("  venv folder name [venv]: ").strip() or "venv"
        selected_python = create_venv(venv_path)
        if not selected_python:
            print("  [ERROR] venv creation failed.")
            return

    if not selected_python:
        print("[ERROR] No Python selected.")
        return

    print(f"\n[SELECTED] {selected_python}")

    extras_yn = input("\nInstall optional packages (all 9 smoothers)? [Y/n]: ").strip().lower()
    extras = extras_yn != "n"

    if not install_deps(selected_python, extras=extras, mirror_url=mirror_url):
        return

    ok = verify(selected_python)

    if ok:
        offer_llm_config()

    print("\n" + "=" * 50)
    if ok:
        print("  Installation complete!")
        print(f"  Run: {selected_python} -m lmpsmart --help")
        print("  Or (with activated env): python -m lmpsmart --help")
    else:
        print("  Installation completed but verify failed.")
        print("  Check errors above or run manually:")
        print(f"    {selected_python} -m lmpsmart config --show")
    print("=" * 50)


if __name__ == "__main__":
    main()
