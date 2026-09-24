from __future__ import annotations

from pathlib import Path

# HEIC 需要额外转换依赖,先不支持,列表里跳过并不是遗漏
_SUPPORTED_EXTENSIONS = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


def list_images(folder: str) -> list[dict]:
    folder_path = Path(folder).expanduser()
    if not folder_path.is_dir():
        raise ValueError(f"不是一个文件夹: {folder}")

    files = sorted(
        p for p in folder_path.iterdir() if p.is_file() and p.suffix.lower() in _SUPPORTED_EXTENSIONS
    )
    return [{"path": str(p), "name": p.name} for p in files]


def read_image_bytes(path: str) -> tuple[bytes, str]:
    """返回 (原始字节, media_type),给多模态生成和缩略图接口共用。"""
    p = Path(path).expanduser()
    media_type = _SUPPORTED_EXTENSIONS.get(p.suffix.lower())
    if media_type is None:
        raise ValueError("不支持的文件类型")
    if not p.is_file():
        raise ValueError("文件不存在")
    return p.read_bytes(), media_type
