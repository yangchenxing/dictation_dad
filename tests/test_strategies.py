import pytest

from dictation_dad.strategies import (
    ChClassicalStrategy,
    ChWordStrategy,
    EnWordStrategy,
    get_strategy,
)


class TestChWordStrategy:
    def test_get_suffix(self):
        assert ChWordStrategy().get_suffix() == ".ch_word.csv"

    def test_validate_csv_valid(self):
        content = "speech\n苹果\n香蕉\n"
        assert ChWordStrategy().validate_csv(content) == []

    def test_validate_csv_missing_column(self):
        content = "answer\n苹果\n"
        assert ChWordStrategy().validate_csv(content) == ["缺少必需列 'speech'"]

    def test_validate_csv_empty_value(self):
        content = "speech\n苹果\n \n"
        assert "第3行 'speech' 为空" in ChWordStrategy().validate_csv(content)

    def test_validate_csv_malformed(self):
        from unittest.mock import patch
        import csv
        content = "speech\n苹果\n"
        with patch("dictation_dad.strategies.csv.DictReader", side_effect=csv.Error("bad csv")):
            errors = ChWordStrategy().validate_csv(content)
        assert len(errors) == 1
        assert "CSV格式错误" in errors[0]

    def test_validate_csv_no_header(self):
        content = ""
        assert ChWordStrategy().validate_csv(content) == ["无法读取CSV标题行"]

    def test_get_entries(self, tmp_path):
        filepath = tmp_path / "test.ch_word.csv"
        filepath.write_text("speech\n苹果\n香蕉\n", encoding="utf-8-sig")
        entries = ChWordStrategy().get_entries(str(filepath))
        assert len(entries) == 2
        assert entries[0]["speech"] == "苹果"
        assert entries[0]["answer"] == "苹果"
        assert "audio_url" in entries[0]
        assert entries[1]["speech"] == "香蕉"

    def test_get_entries_skips_empty(self, tmp_path):
        filepath = tmp_path / "test.ch_word.csv"
        filepath.write_text("speech\n苹果\n\n", encoding="utf-8-sig")
        entries = ChWordStrategy().get_entries(str(filepath))
        assert len(entries) == 1
        assert entries[0]["speech"] == "苹果"

    def test_get_play_params(self):
        params = ChWordStrategy().get_play_params()
        assert params["play_count"] == 2
        assert "wait_time" in params


class TestEnWordStrategy:
    def test_get_suffix(self):
        assert EnWordStrategy().get_suffix() == ".en_word.csv"

    def test_validate_csv_valid(self):
        content = "speech,answer\n苹果,apple\n"
        assert EnWordStrategy().validate_csv(content) == []

    def test_validate_csv_missing_speech(self):
        content = "answer\napple\n"
        assert "缺少必需列 'speech'" in EnWordStrategy().validate_csv(content)

    def test_validate_csv_missing_answer(self):
        content = "speech\n苹果\n"
        assert "缺少必需列 'answer'" in EnWordStrategy().validate_csv(content)

    def test_validate_csv_empty_value(self):
        content = "speech,answer\n苹果,\n"
        assert "第2行 'answer' 为空" in EnWordStrategy().validate_csv(content)

    def test_validate_csv_malformed(self):
        from unittest.mock import patch
        import csv
        content = "speech,answer\n苹果,apple\n"
        with patch("dictation_dad.strategies.csv.DictReader", side_effect=csv.Error("bad csv")):
            errors = EnWordStrategy().validate_csv(content)
        assert len(errors) == 1
        assert "CSV格式错误" in errors[0]

    def test_validate_csv_no_header(self):
        content = ""
        assert EnWordStrategy().validate_csv(content) == ["无法读取CSV标题行"]

    def test_get_entries(self, tmp_path):
        filepath = tmp_path / "test.en_word.csv"
        filepath.write_text("speech,answer\n苹果,apple\n", encoding="utf-8-sig")
        entries = EnWordStrategy().get_entries(str(filepath))
        assert len(entries) == 1
        assert entries[0]["speech"] == "苹果"
        assert entries[0]["answer"] == "apple"
        assert "audio_url" in entries[0]

    def test_get_entries_skips_empty(self, tmp_path):
        filepath = tmp_path / "test.en_word.csv"
        filepath.write_text("speech,answer\n苹果,apple\n,\n", encoding="utf-8-sig")
        entries = EnWordStrategy().get_entries(str(filepath))
        assert len(entries) == 1

    def test_get_play_params(self):
        params = EnWordStrategy().get_play_params()
        assert params["play_count"] == 2


class TestChClassicalStrategy:
    def test_get_suffix(self):
        assert ChClassicalStrategy().get_suffix() == ".ch_classical.csv"

    def test_validate_csv_valid(self):
        content = "speech,answer\n寐,睡觉\n"
        assert ChClassicalStrategy().validate_csv(content) == []

    def test_validate_csv_missing_column(self):
        content = "speech\n寐\n"
        assert "缺少必需列 'answer'" in ChClassicalStrategy().validate_csv(content)

    def test_validate_csv_empty_value(self):
        content = "speech,answer\n寐,\n"
        assert "第2行 'answer' 为空" in ChClassicalStrategy().validate_csv(content)

    def test_validate_csv_malformed(self):
        from unittest.mock import patch
        import csv
        content = "speech,answer\n寐,睡觉\n"
        with patch("dictation_dad.strategies.csv.DictReader", side_effect=csv.Error("bad csv")):
            errors = ChClassicalStrategy().validate_csv(content)
        assert len(errors) == 1
        assert "CSV格式错误" in errors[0]

    def test_validate_csv_no_header(self):
        content = ""
        assert ChClassicalStrategy().validate_csv(content) == ["无法读取CSV标题行"]

    def test_get_entries(self, tmp_path):
        filepath = tmp_path / "test.ch_classical.csv"
        filepath.write_text("speech,answer\n寐,睡觉\n", encoding="utf-8-sig")
        entries = ChClassicalStrategy().get_entries(str(filepath))
        assert len(entries) == 1
        assert entries[0]["speech"] == "寐"
        assert entries[0]["answer"] == "睡觉"
        assert "audio_url" in entries[0]

    def test_get_play_params(self):
        params = ChClassicalStrategy().get_play_params()
        assert params["play_count"] == 1


class TestGetStrategy:
    def test_ch_word(self):
        assert isinstance(get_strategy(".ch_word.csv"), ChWordStrategy)
        assert isinstance(get_strategy("test.ch_word.csv"), ChWordStrategy)

    def test_en_word(self):
        assert isinstance(get_strategy(".en_word.csv"), EnWordStrategy)

    def test_ch_classical(self):
        assert isinstance(get_strategy(".ch_classical.csv"), ChClassicalStrategy)

    def test_invalid(self):
        with pytest.raises(ValueError, match="不支持的文件类型"):
            get_strategy(".invalid.csv")
