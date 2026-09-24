from __future__ import annotations

import base64
import hashlib
import platform
import stat
from pathlib import Path
from zipfile import ZipFile

import pytest
from pytest import TempPathFactory

from wheel.wheelfile import WheelFile

from .util import run_command


def _sha256_record(data: bytes) -> str:
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=")
    return f"sha256={digest.decode('ascii')},{len(data)}"


def test_unpack_dist_info_case_mismatch(tmp_path_factory: TempPathFactory) -> None:
    # The wheel filename starts with an uppercase name (Django-...) while the
    # .dist-info directory inside the archive is all lowercase. Both casings
    # are valid per PEP 427, so unpacking should still work.
    wheel_path = tmp_path_factory.mktemp("build") / "Django-3.2.5-py3-none-any.whl"
    init_source = b"VERSION = (3, 2, 5)\n"
    metadata = b"Metadata-Version: 2.4\nName: Django\nVersion: 3.2.5\n"
    with ZipFile(wheel_path, "w") as zf:
        zf.writestr("django/__init__.py", init_source)
        zf.writestr("django-3.2.5.dist-info/METADATA", metadata)
        zf.writestr(
            "django-3.2.5.dist-info/RECORD",
            f"django/__init__.py,{_sha256_record(init_source)}\n"
            f"django-3.2.5.dist-info/METADATA,{_sha256_record(metadata)}\n"
            "django-3.2.5.dist-info/RECORD,,\n",
        )

    extract_root = tmp_path_factory.mktemp("extract")
    output = run_command("unpack", "--dest", extract_root, wheel_path)
    assert output == f"Unpacking to: {extract_root / 'Django-3.2.5'}...OK\n"

    extract_path = extract_root / "Django-3.2.5"
    assert (
        extract_path.joinpath("django-3.2.5.dist-info", "METADATA").read_bytes()
        == metadata
    )
    assert extract_path.joinpath("django", "__init__.py").read_bytes() == init_source


def test_unpack(tmp_path_factory: TempPathFactory) -> None:
    wheel_path = tmp_path_factory.mktemp("build") / "test-1.0-py3-none-any.whl"
    with WheelFile(wheel_path, "w") as wf:
        wf.writestr(
            "test-1.0.dist-info/METADATA",
            "Metadata-Version: 2.4\nName: test\nVersion: 1.0\n",
        )
        wf.writestr("test-1.0/package/__init__.py", "")
        wf.writestr("test-1.0/package/module.py", "print('hello world')\n")

    extract_path = tmp_path_factory.mktemp("extract")
    run_command("unpack", "--dest", extract_path, wheel_path)

    extract_path /= "test-1.0"
    assert extract_path.joinpath("test-1.0.dist-info", "METADATA").read_text(
        "utf-8"
    ) == ("Metadata-Version: 2.4\nName: test\nVersion: 1.0\n")
    assert (
        extract_path.joinpath("test-1.0", "package", "__init__.py").read_text("utf-8")
        == ""
    )
    assert extract_path.joinpath("test-1.0", "package", "module.py").read_text(
        "utf-8"
    ) == ("print('hello world')\n")


@pytest.mark.skipif(
    platform.system() == "Windows", reason="Windows does not support the executable bit"
)
def test_unpack_executable_bit(tmp_path: Path) -> None:
    wheel_path = tmp_path / "test-1.0-py3-none-any.whl"
    script_path = tmp_path / "script"
    script_path.write_bytes(b"test script")
    script_path.chmod(0o755)
    with WheelFile(wheel_path, "w") as wf:
        wf.write(str(script_path), "nested/script")

    script_path.unlink()
    script_path = tmp_path / "test-1.0" / "nested" / "script"
    run_command("unpack", "--dest", tmp_path, wheel_path)
    assert not script_path.is_dir()
    assert stat.S_IMODE(script_path.stat().st_mode) == 0o755


@pytest.mark.skipif(
    platform.system() == "Windows", reason="Windows does not support chmod()"
)
def test_chmod_outside_unpack_tree(tmp_path_factory: TempPathFactory) -> None:
    wheel_path = tmp_path_factory.mktemp("build") / "test-1.0-py3-none-any.whl"
    with WheelFile(wheel_path, "w") as wf:
        wf.writestr(
            "test-1.0.dist-info/METADATA",
            "Metadata-Version: 2.4\nName: test\nVersion: 1.0\n",
        )
        wf.writestr("../../system-file", b"malicious data")

    extract_root_path = tmp_path_factory.mktemp("extract")
    system_file = extract_root_path / "system-file"
    extract_path = extract_root_path / "subdir"
    system_file.write_bytes(b"important data")
    system_file.chmod(0o755)
    run_command("unpack", "--dest", extract_path, wheel_path)

    assert system_file.read_bytes() == b"important data"
    assert stat.S_IMODE(system_file.stat().st_mode) == 0o755
