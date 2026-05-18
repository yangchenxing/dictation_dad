import csv
import os
import re

CSV_SUFFIXES = (".ch_word.csv", ".en_word.csv", ".ch_classical.csv")
VALID_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9\u4e00-\u9fa5_.\-]+$")


class FileManager:
    def __init__(self, root: str = "."):
        self.root = os.path.abspath(root)

    def _normalize_path(self, rel_path: str) -> str:
        if rel_path == "":
            abs_path = self.root
        else:
            abs_path = os.path.abspath(os.path.join(self.root, rel_path))
        if abs_path != self.root and not abs_path.startswith(self.root + os.sep):
            raise ValueError("非法路径")
        return abs_path

    def list_directory(self, rel_path: str = "") -> dict:
        abs_path = self._normalize_path(rel_path)
        if not os.path.isdir(abs_path):
            raise ValueError("路径不是目录")

        dirs = []
        files = []
        for name in sorted(os.listdir(abs_path)):
            full = os.path.join(abs_path, name)
            if os.path.isdir(full):
                dirs.append({"name": name, "type": "directory"})
            elif os.path.isfile(full) and any(name.endswith(suffix) for suffix in CSV_SUFFIXES):
                if name.endswith(".ch_word.csv"):
                    icon = "🇨🇳"
                    display_name = name[:-len(".ch_word.csv")]
                elif name.endswith(".en_word.csv"):
                    icon = "🇬🇧"
                    display_name = name[:-len(".en_word.csv")]
                else:
                    icon = "🀄"
                    display_name = name[:-len(".ch_classical.csv")]
                files.append({"name": name, "display_name": display_name, "type": "file", "icon": icon})

        return {"directories": dirs, "files": files}

    def create_directory(self, rel_path: str, name: str) -> None:
        if not VALID_NAME_PATTERN.match(name):
            raise ValueError("目录名包含非法字符")
        target = os.path.join(rel_path, name) if rel_path else name
        abs_path = self._normalize_path(target)
        if os.path.exists(abs_path):
            raise ValueError("目录已存在")
        os.makedirs(abs_path, exist_ok=False)

    def delete_file(self, rel_path: str) -> None:
        abs_path = self._normalize_path(rel_path)
        if not os.path.isfile(abs_path):
            raise ValueError("文件不存在")
        if not any(abs_path.endswith(suffix) for suffix in CSV_SUFFIXES):
            raise ValueError("只能删除CSV词表文件")
        os.remove(abs_path)

    def preview_csv(self, rel_path: str) -> list[dict]:
        abs_path = self._normalize_path(rel_path)
        if not os.path.isfile(abs_path):
            raise ValueError("文件不存在")
        with open(abs_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def save_file(self, rel_path: str, filename: str, content: str, overwrite: bool = False) -> None:
        if not VALID_NAME_PATTERN.match(filename):
            raise ValueError("文件名包含非法字符")
        target = os.path.join(rel_path, filename) if rel_path else filename
        abs_path = self._normalize_path(target)
        if os.path.exists(abs_path) and not overwrite:
            raise FileExistsError("文件已存在")
        dirname = os.path.dirname(abs_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
