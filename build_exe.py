"""Воспроизводимая сборка автономного VideoFlow.exe."""
from pathlib import Path
import ast
import shutil
import subprocess
import sys



ROOT = Path(__file__).resolve().parent
PNG = ROOT / "assets" / "brand.png"
ICO = ROOT / "assets" / "brand.ico"


def make_icon() -> None:
    from branding import generate_assets
    generate_assets(ROOT / "assets")


def build() -> None:
    make_icon()
    tree = ast.parse((ROOT / "videoflow.py").read_text(encoding="utf-8"))
    version = next(node.value.value for node in tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == "VERSION" for target in node.targets))
    release = ROOT / "releases" / version
    release.mkdir(parents=True, exist_ok=True)
    work = ROOT / "build" / version
    work.mkdir(parents=True, exist_ok=True)
    separator = ";" if sys.platform == "win32" else ":"
    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onefile", "--windowed",
        "--name", f"VideoFlow-{version}",
        "--distpath", str(release),
        "--workpath", str(work),
        "--specpath", str(work),
        "--icon", str(ICO),
        "--add-data", f"{PNG}{separator}assets",
        "--add-data", f"{ICO}{separator}assets",
        "--collect-all", "customtkinter",
        "--hidden-import", "truststore",
        str(ROOT / "videoflow.py"),
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    # Каждый релиз остаётся в своей папке; dist содержит актуальную копию.
    (ROOT / "dist").mkdir(exist_ok=True)
    try:
        shutil.copy2(release / f"VideoFlow-{version}.exe", ROOT / "dist" / "VideoFlow.exe")
    except PermissionError:
        print(f"Current dist/VideoFlow.exe is in use; the new release is ready at {release}")


if __name__ == "__main__":
    build()
