import os

import pytest

from dictation_dad.file_manager import FileManager


class TestFileManager:
    def test_init(self, tmp_path):
        fm = FileManager(str(tmp_path))
        assert fm.root == str(tmp_path)

    def test_normalize_path_empty(self, tmp_path):
        fm = FileManager(str(tmp_path))
        assert fm._normalize_path("") == str(tmp_path)

    def test_normalize_path_normal(self, tmp_path):
        fm = FileManager(str(tmp_path))
        assert fm._normalize_path("foo") == str(tmp_path / "foo")

    def test_normalize_path_traversal(self, tmp_path):
        fm = FileManager(str(tmp_path))
        with pytest.raises(ValueError, match="非法路径"):
            fm._normalize_path("..")

    def test_normalize_path_absolute_outside(self, tmp_path):
        fm = FileManager(str(tmp_path))
        with pytest.raises(ValueError, match="非法路径"):
            fm._normalize_path("/etc/passwd")

    def test_list_directory_normal(self, tmp_path):
        fm = FileManager(str(tmp_path))
        (tmp_path / "dir1").mkdir()
        (tmp_path / "test.ch_word.csv").write_text("speech\n苹果\n", encoding="utf-8")
        (tmp_path / "test.en_word.csv").write_text("speech,answer\n苹果,apple\n", encoding="utf-8")
        (tmp_path / "test.ch_classical.csv").write_text("speech,answer\n寐,睡觉\n", encoding="utf-8")
        (tmp_path / "readme.txt").write_text("hello", encoding="utf-8")
        res = fm.list_directory("")
        assert len(res["directories"]) == 1
        assert len(res["files"]) == 3
        assert res["directories"][0]["name"] == "dir1"
        names = [f["name"] for f in res["files"]]
        assert "test.ch_word.csv" in names
        assert "test.en_word.csv" in names
        assert "test.ch_classical.csv" in names

    def test_list_directory_empty(self, tmp_path):
        fm = FileManager(str(tmp_path))
        res = fm.list_directory("")
        assert res == {"directories": [], "files": []}

    def test_list_directory_not_dir(self, tmp_path):
        fm = FileManager(str(tmp_path))
        (tmp_path / "file.txt").write_text("x")
        with pytest.raises(ValueError, match="路径不是目录"):
            fm.list_directory("file.txt")

    def test_list_directory_invalid_path(self, tmp_path):
        fm = FileManager(str(tmp_path))
        with pytest.raises(ValueError, match="非法路径"):
            fm.list_directory("..")

    def test_list_directory_nested(self, tmp_path):
        fm = FileManager(str(tmp_path))
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "nested.en_word.csv").write_text("speech,answer\na,b\n")
        res = fm.list_directory("sub")
        assert len(res["files"]) == 1
        assert res["files"][0]["name"] == "nested.en_word.csv"

    def test_create_directory_success(self, tmp_path):
        fm = FileManager(str(tmp_path))
        fm.create_directory("", "newdir")
        assert (tmp_path / "newdir").is_dir()

    def test_create_directory_invalid_name(self, tmp_path):
        fm = FileManager(str(tmp_path))
        with pytest.raises(ValueError, match="目录名包含非法字符"):
            fm.create_directory("", "new dir")

    def test_create_directory_exists(self, tmp_path):
        fm = FileManager(str(tmp_path))
        (tmp_path / "exists").mkdir()
        with pytest.raises(ValueError, match="目录已存在"):
            fm.create_directory("", "exists")

    def test_create_directory_nested(self, tmp_path):
        fm = FileManager(str(tmp_path))
        (tmp_path / "parent").mkdir()
        fm.create_directory("parent", "child")
        assert (tmp_path / "parent" / "child").is_dir()

    def test_delete_file_success(self, tmp_path):
        fm = FileManager(str(tmp_path))
        (tmp_path / "test.ch_word.csv").write_text("speech\n苹果\n")
        fm.delete_file("test.ch_word.csv")
        assert not (tmp_path / "test.ch_word.csv").exists()

    def test_delete_file_not_exists(self, tmp_path):
        fm = FileManager(str(tmp_path))
        with pytest.raises(ValueError, match="文件不存在"):
            fm.delete_file("nonexistent.ch_word.csv")

    def test_delete_file_not_csv(self, tmp_path):
        fm = FileManager(str(tmp_path))
        (tmp_path / "readme.txt").write_text("hello")
        with pytest.raises(ValueError, match="只能删除CSV词表文件"):
            fm.delete_file("readme.txt")

    def test_delete_file_invalid_path(self, tmp_path):
        fm = FileManager(str(tmp_path))
        with pytest.raises(ValueError, match="非法路径"):
            fm.delete_file("../test.ch_word.csv")

    def test_preview_csv_success(self, tmp_path):
        fm = FileManager(str(tmp_path))
        (tmp_path / "test.ch_word.csv").write_text("speech\n苹果\n香蕉\n", encoding="utf-8-sig")
        rows = fm.preview_csv("test.ch_word.csv")
        assert len(rows) == 2
        assert rows[0]["speech"] == "苹果"
        assert rows[1]["speech"] == "香蕉"

    def test_preview_file_not_exists(self, tmp_path):
        fm = FileManager(str(tmp_path))
        with pytest.raises(ValueError, match="文件不存在"):
            fm.preview_csv("nonexistent.csv")

    def test_save_file_success(self, tmp_path):
        fm = FileManager(str(tmp_path))
        fm.save_file("", "new.ch_word.csv", "speech\n苹果\n")
        assert (tmp_path / "new.ch_word.csv").exists()
        assert (tmp_path / "new.ch_word.csv").read_text(encoding="utf-8") == "speech\n苹果\n"

    def test_save_file_invalid_name(self, tmp_path):
        fm = FileManager(str(tmp_path))
        with pytest.raises(ValueError, match="文件名包含非法字符"):
            fm.save_file("", "bad name.csv", "x")

    def test_save_file_exists_no_overwrite(self, tmp_path):
        fm = FileManager(str(tmp_path))
        (tmp_path / "exists.ch_word.csv").write_text("x")
        with pytest.raises(FileExistsError, match="文件已存在"):
            fm.save_file("", "exists.ch_word.csv", "y", overwrite=False)

    def test_save_file_exists_overwrite(self, tmp_path):
        fm = FileManager(str(tmp_path))
        (tmp_path / "exists.ch_word.csv").write_text("x")
        fm.save_file("", "exists.ch_word.csv", "y", overwrite=True)
        assert (tmp_path / "exists.ch_word.csv").read_text(encoding="utf-8") == "y"

    def test_save_file_nested_path(self, tmp_path):
        fm = FileManager(str(tmp_path))
        fm.save_file("sub", "file.ch_word.csv", "speech\na\n")
        assert (tmp_path / "sub" / "file.ch_word.csv").exists()
