import base64
import os
import subprocess
import sys
import venv
import zipfile
from pathlib import Path

BASE64_ZIP = (
    "UEsDBBQAAAAIAOcWLlz8Gma2KQAAACcAAAAQAAAAcmVxdWlyZW1lbnRzLnR4dEtLLC5JLMjkKi3LTM4vyuMqqExJzCvJTOZSVkgpzc2tVMjJzEvl4gIAUEsDBBQAAAAIAOcWLlxXY55kGwAAABkAAAAKAAAAUkVBRE1FLnR4dEspzc2tVCjIL08tysgvLU5VSCxKzsgsS+UCAFBLAQIUAxQAAAAIAOcWLlz8Gma2KQAAACcAAAAQAAAAAAAAAAAAAACAAQAAAAByZXF1aXJlbWVudHMudHh0UEsBAhQDFAAAAAgA5xYuXFdjnmQbAAAAGQAAAAoAAAAAAAAAAAAAAIABVwAAAFJFQURNRS50eHRQSwUGAAAAAAIAAgB2AAAAmgAAAAAA"
)


def print_step(message: str) -> None:
    print(f"[install_powerhouse] {message}")


def decode_zip(zip_path: Path) -> None:
    print_step("Decoding embedded archive...")
    data = base64.b64decode(BASE64_ZIP)
    zip_path.write_bytes(data)
    print_step(f"Wrote archive to {zip_path}")


def extract_zip(zip_path: Path, target_dir: Path) -> None:
    print_step(f"Extracting archive to {target_dir}...")
    target_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(target_dir)
    print_step("Extraction complete")


def ensure_requirements(target_dir: Path) -> Path:
    requirements_path = target_dir / "requirements.txt"
    if not requirements_path.exists():
        print_step("requirements.txt missing; creating dummy requirements")
        requirements_path.write_text(
            "fastapi\nuvicorn\npydantic\n# dummy line\n\n", encoding="utf-8"
        )
    return requirements_path


def create_venv(target_dir: Path) -> Path:
    venv_dir = target_dir / "venv"
    if not venv_dir.exists():
        print_step(f"Creating virtual environment at {venv_dir}...")
        builder = venv.EnvBuilder(with_pip=True, clear=False, symlinks=True)
        builder.create(venv_dir)
        print_step("Virtual environment created")
    else:
        print_step("Virtual environment already exists; skipping creation")
    return venv_dir


def venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def install_requirements(venv_dir: Path, requirements_path: Path) -> None:
    python_path = venv_python(venv_dir)
    print_step(f"Installing requirements from {requirements_path}...")
    subprocess.check_call(
        [str(python_path), "-m", "pip", "install", "-r", str(requirements_path)]
    )
    print_step("Requirements installed")


def install_powerhouse() -> None:
    script_dir = Path(__file__).resolve().parent
    zip_path = script_dir / "powerhouse.zip"
    target_dir = script_dir / "powerhouse"

    first_run = not target_dir.exists()
    if first_run:
        print_step("Starting first-run installation")
        decode_zip(zip_path)
        extract_zip(zip_path, target_dir)
    else:
        print_step("Powerhouse directory already exists; skipping archive extraction")

    requirements_path = ensure_requirements(target_dir)
    venv_dir = create_venv(target_dir)
    install_requirements(venv_dir, requirements_path)

    print_step("Installation complete")
    print_step("To start the platform, run the following command from this directory:")
    print_step(
        "python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000"
    )
    # Uncomment the following line to start the server automatically:
    # subprocess.check_call([
    #     str(venv_python(venv_dir)),
    #     "-m",
    #     "uvicorn",
    #     "backend.api.main:app",
    #     "--host",
    #     "0.0.0.0",
    #     "--port",
    #     "8000",
    # ])


if __name__ == "__main__":
    install_powerhouse()
