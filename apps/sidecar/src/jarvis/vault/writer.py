"""Safe, atomic Markdown writing into the owner's vault (one-way mirror, never contains secrets)."""

from __future__ import annotations

import os
import re
import tempfile
from collections.abc import Callable
from pathlib import Path

_FORBIDDEN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
_KEY_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]{20,}"),
]
MIN_SECRET_LEN = 8


class VaultError(Exception):
    """A vault write was refused (bad path, unusable folder, or the text would leak a secret)."""


def safe_filename(name: str) -> str:
    out = _FORBIDDEN.sub("-", name)
    out = re.sub(r"\s+", " ", out).strip(" .-")[:80].strip(" .-")
    if not out:
        return "untitled"
    if out.split(".")[0].upper() in _RESERVED:
        out = f"_{out}"
    return out


def write_atomic(path: Path, text: str) -> None:
    """Write via a temp file in the same folder and rename into place; always LF line endings."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.replace("\r\n", "\n").replace("\r", "\n")
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-", suffix=".md")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(data)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


class VaultWriter:
    def __init__(self, root: Path | str, secrets: Callable[[], list[str]]) -> None:
        self.root = Path(root)
        self._secrets = secrets

    def write(self, rel: str, text: str) -> Path:
        if not self.root.is_dir():
            raise VaultError("The vault folder does not exist.")
        target = (self.root / rel).resolve()
        if self.root.resolve() not in target.parents:
            raise VaultError("Refusing to write outside the vault folder.")
        for secret in self._secrets():
            if len(secret) >= MIN_SECRET_LEN and secret in text:
                raise VaultError("Refusing to write text that contains a stored secret.")
        if any(p.search(text) for p in _KEY_PATTERNS):
            raise VaultError("Refusing to write text that looks like an API key.")
        try:
            write_atomic(target, text)
        except OSError as e:
            raise VaultError(f"Could not write to the vault ({e.strerror or e}).") from e
        return target
