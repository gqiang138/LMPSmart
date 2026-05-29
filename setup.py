#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import os
import shutil
import json
import subprocess
import sys
import yaml
from pathlib import Path


PROG = "LMPSmart"

PYTHON_MIN = (3, 10)

PIP_MIRRORS = {
    "tsinghua": "https://pypi.tuna.tsinghua.edu.cn/simple",
    "tencent": "https://mirrors.cloud.tencent.com/pypi/simple",
    "official": "https://pypi.org/simple",
}

SETUP_CONFIG_PATH = Path(__file__).parent / "configs" / "setup.json"


def get_setup_config():
    path = SETUP_CONFIG_PATH
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_setup_config(data):
    path = SETUP_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    merged = {**existing, **data}
    merged["version"] = 1
    merged["timestamp"] = datetime.datetime.now().isoformat()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)


WELCOME = r"""
+==============================================+
|     LMPSmart Setup Wizard                    |
|   LAMMPS Data Agent - Smart Installer        |
+==============================================+
"""


def run(cmd, capture=True, shell=True):
    try:
        if capture:
            r = subprocess.run(cmd, shell=shell, capture_output=True, text=True, encoding="utf-8", errors="replace")
            return r.stdout.strip(), r.stderr.strip(), r.returncode
        else:
            r = subprocess.run(cmd, shell=shell)
            return "", "", r.returncode
    except Exception as e:
        return "", str(e), 1


def detect_pythons():
    results = []
    seen_paths = set()
    conda_env_roots = []

    # 1. conda envs
    out, _, rc = run("conda env list --json")
    if rc == 0:
        try:
            json_start = out.find("{")
            if json_start >= 0:
                data = json.loads(out[json_start:])
                for path in data.get("envs", []):
                    p = Path(path) / "python.exe" if os.name == "nt" else Path(path) / "bin" / "python"
                    if p.exists():
                        conda_env_roots.append(Path(path).parent)
                        ver = get_python_ver(str(p))
                        if ver and ver >= PYTHON_MIN:
                            name = Path(path).name
                            results.append(("conda", name, str(p), ver))
                            seen_paths.add(str(p))
        except Exception:
            pass

    def is_inside_conda_env(p):
        for root in conda_env_roots:
            try:
                p.resolve().relative_to(root.resolve())
                return True
            except ValueError:
                continue
        return False

    # 2. py launcher (Windows) - discovers Python versions installed via py launcher
    if os.name == "nt":
        # Parse "py -0" output to find all available versions
        out, _, rc = run("py -0")
        if rc == 0:
            for line in out.splitlines():
                line = line.strip()
                if not line or line.startswith("-"):
                    continue
                # Format: "-V:3.13 *        Python 3.13 (64-bit)"
                # or: "-V:3.2-32        Python 3.2-32"
                parts = line.split()
                if not parts or not parts[0].startswith("-V:"):
                    continue
                ver_str = parts[0][3:]  # "3.13" or "3.2-32"
                if "-" in ver_str:
                    ver_str = ver_str.split("-")[0]  # "3.2"
                try:
                    major, minor = ver_str.split(".")
                    ver = (int(major), int(minor))
                except Exception:
                    continue
                if ver < PYTHON_MIN:
                    continue
                # Get executable path for this version
                exe_out, _, exe_rc = run(f'py -{ver_str} -c "import sys; print(sys.executable)"')
                if exe_rc == 0 and exe_out.strip():
                    exe_path = exe_out.strip()
                    if exe_path not in seen_paths:
                        name = f"py-{ver_str}"
                        results.append(("py-launcher", name, exe_path, ver))
                        seen_paths.add(exe_path)

    # 3. venv / virtualenv in current dir + user-wide + project dir
    venv_search_paths = [Path(".")]
    if os.name == "nt":
        venv_search_paths.append(Path.home() / "venvs")
        venv_search_paths.append(Path.home() / ".virtualenvs")
        venv_search_paths.append(Path(os.environ.get("WORKON_HOME", "")))
    for search_base in venv_search_paths:
        if not search_base.exists():
            continue
        for v in search_base.glob("**/python.exe") if os.name == "nt" else search_base.glob("**/bin/python"):
            if str(v) in seen_paths:
                continue
            if is_inside_conda_env(v):
                continue
            try:
                ver = get_python_ver(str(v))
                if ver and ver >= PYTHON_MIN:
                    name = v.parent.parent.name
                    results.append(("venv", name, str(v), ver))
                    seen_paths.add(str(v))
            except Exception:
                pass

    # 4. pyenv (Linux/macOS)
    if os.name != "nt":
        out, _, rc = run("pyenv versions --bare")
        if rc == 0:
            pyenv_root, _, _ = run("pyenv root")
            for line in out.splitlines():
                name = line.strip()
                if not name:
                    continue
                p = Path(pyenv_root) / "versions" / name / "bin" / "python"
                if p.exists() and str(p) not in seen_paths:
                    ver = get_python_ver(str(p))
                    if ver and ver >= PYTHON_MIN:
                        results.append(("pyenv", name, str(p), ver))
                        seen_paths.add(str(p))

    # 5. system python via PATH
    for name in ["python3.12", "python3.11", "python3.10", "python", "python3"]:
        p = shutil.which(name)
        if p:
            ver = get_python_ver(p)
            if ver and ver >= PYTHON_MIN:
                if p not in seen_paths:
                    results.append(("system", name, p, ver))
                    seen_paths.add(p)
            break

    return results


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


def create_conda_env(name="LMPSmart", pyver="3.12"):
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


def _pip_install(pip, pkgs, index_arg):
    _, err, rc = run(f"{pip} install {pkgs}{index_arg}")
    return rc, err

def install_deps(python_path, extras=True, mirror_url=None, fallback_url=None):
    pip = f'"{python_path}" -m pip'
    root = Path(__file__).parent.absolute()
    mirrors = []
    if mirror_url:
        mirrors.append(mirror_url)
    if fallback_url and fallback_url != mirror_url:
        mirrors.append(fallback_url)
    mirrors.append("https://mirrors.cloud.tencent.com/pypi/simple")

    def mirror_args(url):
        if not url:
            return ""
        if "tuna" in url:
            return f" -i {url} --trusted-host pypi.tuna.tsinghua.edu.cn"
        if "tencent" in url:
            return f" -i {url} --trusted-host mirrors.cloud.tencent.com"
        if "pypi.org" in url:
            return f" -i {url} --trusted-host pypi.org"
        return f" -i {url}" if url else ""

    last_err = ""
    for url in mirrors:
        idx = mirror_args(url)
        rc, err = _pip_install(pip, f"-e {root}", idx)
        if rc == 0:
            if extras:
                _pip_install(pip, "pykalman pywavelets matplotlib", idx)
            return True
        last_err = err
    return False


def verify(python_path):
    print(f"\n[VERIFY] Running verification...")
    _, err, rc = run(f'"{python_path}" -m lmpsmart config --show')
    if rc == 0:
        print(f"  [OK] LMPSmart is working correctly!")
        return True
    else:
        print(f"  [WARN] Verification failed:\n  {err}")
        return False


def ask_llm_config(python_path):
    print("\n" + "=" * 50)
    print("  LLM Configuration")
    print("=" * 50)

    print("\n  Choose LLM configuration strategy:")
    print("  1) [A] Auto        - Detect local Ollama, test connectivity")
    print("  2) [M] Manual      - Enter Ollama / API endpoint manually")
    print("  3) [L] LAN        - Remote Ollama server (e.g. 192.168.1.x)")
    print("  4) [O] Online     - OpenRouter / OpenAI API only")
    print("  5) [S] Skip       - Use keyword fallback, configure later")
    print()
    ans = input("  Select [A]: ").strip().lower()

    if ans in ("s", "5"):
        print("  [SKIP] LLM config skipped. Run `lmpsmart llm setup` anytime.")
        return

    if ans in ("", "a", "1"):
        prov, base_url, model = "local", "http://localhost:11434", "qwen3.5-9b"
        print("\n  Testing local Ollama connectivity...")
        test_out, test_err, test_rc = run(f'curl -s -o nul -w "%{{http_code}}" --connect-timeout 3 {base_url}')
        if test_rc == 0 and test_out.strip() == "200":
            print(f"  [OK] Ollama reachable at {base_url}")
        else:
            print(f"  [WARN] Ollama not reachable at {base_url}")
            print(f"         Will fall back to keyword matching.")
            prov, base_url, model = None, None, None

    elif ans in ("m", "2"):
        base_url = input("  Ollama / API endpoint [http://localhost:11434]: ").strip()
        if not base_url:
            base_url = "http://localhost:11434"
        model = input("  Model name [qwen3.5-9b]: ").strip() or "qwen3.5-9b"
        prov = "local"
        print("\n  Validating endpoint...")
        test_out, test_err, test_rc = run(f'curl -s -o nul -w "%{{http_code}}" --connect-timeout 5 {base_url}')
        if test_rc == 0 and test_out.strip() == "200":
            print(f"  [OK] Endpoint reachable")
        else:
            print(f"  [WARN] Endpoint not reachable: {test_err or test_out}")
        print(f"  [INFO] Configured: {base_url} / {model}")

    elif ans in ("l", "3"):
        base_url = input("  Remote Ollama address [http://10.103.8.240:11434]: ").strip()
        if not base_url:
            base_url = "http://10.103.8.240:11434"
        else:
            base_url = base_url.strip()
            if not base_url.startswith("http"):
                base_url = f"http://{base_url}"
            parts = base_url.split("://")[1].split("/")[0].split(":")
            host = parts[0]
            if len(parts) == 1:
                base_url = f"{base_url}:11434"
        prov = "local"
        print("\n  Testing LAN Ollama...")
        test_out, test_err, test_rc = run(f'curl -s -o nul -w "%{{http_code}}" --connect-timeout 5 {base_url}')
        if test_rc == 0 and test_out.strip() == "200":
            print(f"  [OK] LAN Ollama reachable at {base_url}")
            out_json, _, rc = run(f'curl -s --connect-timeout 10 {base_url}/api/tags')
            models = []
            if rc == 0:
                try:
                    data = json.loads(out_json)
                    models = [m["name"] for m in data.get("models", [])]
                except Exception:
                    pass
            if models:
                print(f"\n  Available models ({len(models)}):")
                for i, m in enumerate(models, 1):
                    print(f"    {i}. {m}")
                sel = input(f"\n  Select model [1]: ").strip()
                if sel:
                    try:
                        idx = int(sel) - 1
                        if 0 <= idx < len(models):
                            model = models[idx]
                    except ValueError:
                        pass
                if not sel or not model:
                    model = models[0]
                print(f"  Model: {model}")
            else:
                print("  [WARN] No models found, using default")
                model = input("  Model name [qwen3.5-9b]: ").strip() or "qwen3.5-9b"
        else:
            http_code = test_out.strip()
            err_msg = test_err.strip() if test_err.strip() else "(no response)"
            print(f"  [WARN] LAN Ollama not reachable at {base_url}")
            print(f"         HTTP code: {http_code}, error: {err_msg}")
            print(f"         Check: server running? firewall? network accessible?")
            model = input("  Model name [qwen3.5-9b]: ").strip() or "qwen3.5-9b"

    elif ans in ("o", "4"):
        base_url = input("  Base URL [https://openrouter.ai/api/v1]: ").strip()
        if not base_url:
            base_url = "https://openrouter.ai/api/v1"
        api_key = input("  API Key (sk-or-xxx / sk-xxx): ").strip()
        model = input("  Model [anthropic/claude-3-haiku]: ").strip() or "anthropic/claude-3-haiku"
        prov = "online"
        print("\n  Testing API endpoint...")
        test_out, test_err, test_rc = run(f'curl -s -o nul -w "%{{http_code}}" --connect-timeout 5 -H "Authorization: Bearer {api_key}" {base_url}/models')
        if test_rc == 0 and test_out.strip() == "200":
            print(f"  [OK] API endpoint reachable")
        else:
            print(f"  [WARN] API test failed (non-critical): {test_err or test_out}")
    else:
        print("  Invalid choice. Run `lmpsmart llm setup` later to configure.")
        return

    if prov:
        cmd = f'"{python_path}" -m lmpsmart llm setup --provider {prov}'
        if base_url:
            cmd += f' --base-url {base_url}'
        if model:
            cmd += f' --model {model}'
        if prov == "online" and api_key:
            cmd += f' --api-key {api_key}'
        print(f"\n  Running: {cmd}")
        out, err, rc = run(cmd)
        if rc == 0:
            print(f"  [OK] LLM configured: {out}")
        else:
            print(f"  [WARN] LLM config failed: {err}")
    print("\n" + "=" * 50)
    print("  LLM Configuration (optional)")
    print("=" * 50)
    print("  You can configure LLM later with:")
    print("    python -m lmpsmart llm setup --provider local --model qwen3.5-9b")
    print("  Or skip for now - keyword fallback is always available.")
    print()


def ask_mcp_config(python_path):
    print("\n" + "=" * 50)
    print("  MCP Server Configuration (OpenCode)")
    print("=" * 50)

    print("\n  lmpsmart can auto-configure OpenCode's MCP server.")
    print("  This exposes all 24 tools (arrange, smooth, plot, etc.)")
    print("  to OpenCode — the host's own LLM handles planning.")
    print()
    print("  1) [A] Auto    - Auto-detect opencode, add lmpsmart MCP")
    print("  2) [M] Manual  - Show command to run manually later")
    print("  3) [S] Skip    - Skip (can configure anytime)")
    print()
    ans = input("  Select [A]: ").strip().lower()

    if ans in ("s", "3"):
        print("  [SKIP] MCP config skipped. Run manually:")
        print("    opencode mcp add lmpsmart python -m lmpsmart.api.mcp_server")
        return

    if ans in ("", "a", "1"):
        opencode_path = shutil.which("opencode")
        if not opencode_path:
            candidates = [
                Path(os.environ.get("LOCALAPPDATA", "")) / "opencode" / "bin" / "opencode.exe",
                Path.home() / ".local" / "bin" / "opencode",
                Path.home() / "AppData" / "Local" / "opencode" / "opencode.exe",
            ]
            for c in candidates:
                if c.exists():
                    opencode_path = str(c)
                    break

        if not opencode_path:
            print("  [WARN] opencode not found in PATH.")
            print("         Install OpenCode first: https://opencode.ai/")
            print("  Or run manually after installing OpenCode:")
            print("    opencode mcp add lmpsmart python -m lmpsmart.api.mcp_server")
            return

        py_exe = shutil.which("python") or python_path
        mcp_cmd = [py_exe, "-m", "lmpsmart.api.mcp_server"]

        print(f"\n  Adding lmpsmart MCP to OpenCode...")
        print(f"  Command: opencode mcp add lmpsmart {' '.join(mcp_cmd)}")

        result = subprocess.run(
            ["opencode", "mcp", "add", "lmpsmart"] + mcp_cmd,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            shell=(os.name == "nt")
        )

        if result.returncode == 0:
            print("  [OK] lmpsmart MCP server added!")
            print("       Verify with: opencode mcp list")
        else:
            print(f"  [WARN] Failed:")
            print(f"         {result.stderr or result.stdout}")
            print("  Manual command:")
            print(f"    opencode mcp add lmpsmart {' '.join(mcp_cmd)}")
    else:
        print("  [INFO] Run manually after installing OpenCode:")
        print("    opencode mcp add lmpsmart python -m lmpsmart.api.mcp_server")


def main():
    print(WELCOME)

    root = Path(__file__).parent.absolute()
    print(f"Project root: {root}\n")

    # Step 0: check if already installed
    already_installed = False
    try:
        out, _, rc = run(f'"{sys.executable}" -m lmpsmart config --show')
        if rc == 0:
            already_installed = True
    except Exception:
        pass

    saved = get_setup_config()
    python_path_saved = saved.get("python_path") if saved else None
    mirror_url_saved = saved.get("mirror_url") if saved else None

    selected_python = None
    ok = False

    if already_installed:
        print("[FOUND] LMPSmart is already installed!")
        print()
        print("  R) Reuse last setup  - Python + mirror (fast path)")
        print("  U) Update installation (reinstall current version)")
        print("  W) Run wizard from scratch (select env, configure LLM + MCP)")
        print("  Q) Quit")
        print()
        while True:
            ans = input("Select [R]: ").strip().lower()
            if ans in ("", "r"):
                if python_path_saved and Path(python_path_saved).exists():
                    print(f"[REUSE] Python: {python_path_saved}")
                    primary = mirror_url_saved or PIP_MIRRORS["tsinghua"]
                    if install_deps(python_path_saved, extras=True,
                                   mirror_url=primary,
                                   fallback_url=PIP_MIRRORS["official"]):
                        verify(python_path_saved)
                        if saved and not saved.get("llm_configured"):
                            ask_llm_config(python_path_saved)
                            ask_mcp_config(python_path_saved)
                            saved["llm_configured"] = True
                            save_setup_config(saved)
                        print(f"[READY] Launching lmpsmart agent...")
                        agent_proc = subprocess.run(
                            [str(python_path_saved), "-m", "lmpsmart", "agent", "--interactive"],
                            cwd=str(root),
                        )
                        return
                else:
                    print(f"  [WARN] Saved Python not found: {python_path_saved}")
                    print("  Falling back to wizard...")
                    already_installed = False
                    print()
                break
            elif ans == "u":
                print(f"\n[UPDATE] Reinstalling with current Python ({sys.executable})...")
                break
            elif ans == "w":
                already_installed = False
                print()
                break
            elif ans == "q":
                print("Cancelled.")
                return
            print("Please enter R, U, W or Q.")
        if already_installed:
            primary = PIP_MIRRORS["tsinghua"]
            print("[UPDATE] Reinstalling...")
            if install_deps(sys.executable, extras=True,
                           mirror_url=primary,
                           fallback_url=PIP_MIRRORS["official"]):
                verify(sys.executable)
            return

    mirror_url = PIP_MIRRORS["tsinghua"]

    print("[STEP 1] Detecting Python environments...")
    envs = detect_pythons()
    if envs:
        print(f"  Found {len(envs)} Python environment(s):")
        for i, (_, name, path, ver) in enumerate(envs):
            tag = " (current)" if path == sys.executable else ""
            ver_str = f"{ver[0]}.{ver[1]}"
            print(f"  {i + 1}. {name} {ver_str}{tag}")
    else:
        print("  No compatible Python found.")

    print()
    print("  A) Use an existing environment")
    print("  B) Create new conda env (Python 3.12)")
    print("  C) Create new venv (in project dir)")
    print("  Q) Quit")

    choice = ""

    while choice not in ("A", "B", "C", "Q", "q", "a", "b", "c"):
        choice = input("\nSelect option [A]: ").strip()

    if choice.lower() == "q":
        print("Cancelled.")
        return

    env_name_saved = None
    env_kind_saved = None
    if choice.lower() in ("a", ""):
        if envs:
            while True:
                sel = input(f"\nSelect environment [1-{len(envs)}]: ").strip()
                if not sel:
                    sel = "1"
                try:
                    idx = int(sel) - 1
                    if 0 <= idx < len(envs):
                        selected_python = envs[idx][2]
                        p = Path(selected_python).parts
                        if len(p) >= 3 and p[-2] in ("Scripts", "bin", "Lib"):
                            env_name_saved = p[-3]
                        elif len(p) >= 2:
                            env_name_saved = p[-2]
                        else:
                            env_name_saved = Path(selected_python).stem
                        env_kind_saved = "existing"
                        break
                except ValueError:
                    pass
                print("Invalid selection.")
        else:
            print("  No existing envs. Creating conda env instead.")
            choice = "B"

    if choice.lower() in ("b", ""):
        name = input("  Conda env name [LMPSmart]: ").strip() or "LMPSmart"
        pyver = input("  Python version [3.12]: ").strip() or "3.12"
        selected_python = create_conda_env(name, pyver)
        if not selected_python:
            print("  [ERROR] Conda env creation failed.")
            return
        env_name_saved = name
        env_kind_saved = "conda"

    elif choice.lower() == "c":
        venv_path = input("  venv folder name [venv]: ").strip() or "venv"
        selected_python = create_venv(venv_path)
        if not selected_python:
            print("  [ERROR] venv creation failed.")
            return
        env_name_saved = venv_path
        env_kind_saved = "venv"

    if not selected_python:
        print("[ERROR] No Python selected.")
        return

    print(f"\n[SELECTED] {selected_python}")
    print("\n  All smoothers (9 algorithms) will be installed automatically.")

    if not install_deps(selected_python, extras=True,
                       mirror_url=mirror_url,
                       fallback_url=PIP_MIRRORS["official"]):
        return

    ok = verify(selected_python)

    ask_llm_config(selected_python)
    ask_mcp_config(selected_python)
    saved_cfg = {
        "python_path": selected_python,
        "mirror_url": mirror_url,
        "env_name": env_name_saved,
        "env_kind": env_kind_saved,
        "llm_configured": True,
    }
    save_setup_config(saved_cfg)

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
    return


if __name__ == "__main__":
    main()
