"""
E2E tests for Linux text processing commands.
Tests: cat, head, tail, less, wc, sort, uniq, cut, tr, diff
"""

import pytest
from nlp2cmd.intelligent.command_detector import CommandDetector


class TestTextProcessingCommands:
    """Test text processing commands detection and generation."""

    @pytest.fixture
    def detector(self):
        return CommandDetector()

    # ===== CAT =====
    def test_cat_basic(self, detector):
        result = detector.detect_command("cat plik.txt")
        assert result[0].command == "cat"

    def test_cat_polish(self, detector):
        result = detector.detect_command("pokaż zawartość pliku config.txt")
        assert any(r.command == "cat" for r in result)

    def test_cat_view_file(self, detector):
        result = detector.detect_command("view file content")
        assert any(r.command == "cat" for r in result)

    # ===== HEAD =====
    def test_head_basic(self, detector):
        result = detector.detect_command("head -n 10 file.log")
        assert result[0].command == "head"

    def test_head_polish(self, detector):
        result = detector.detect_command("pokaż pierwsze linie pliku")
        assert any(r.command == "head" for r in result)

    def test_head_top_lines(self, detector):
        result = detector.detect_command("show top 20 lines of file")
        assert any(r.command == "head" for r in result)

    # ===== TAIL =====
    def test_tail_basic(self, detector):
        result = detector.detect_command("tail -n 50 app.log")
        assert result[0].command == "tail"

    def test_tail_polish(self, detector):
        result = detector.detect_command("pokaż ostatnie linie pliku")
        assert any(r.command == "tail" for r in result)

    def test_tail_follow(self, detector):
        result = detector.detect_command("follow log file")
        assert any(r.command == "tail" for r in result)

    def test_tail_end_of_file(self, detector):
        result = detector.detect_command("end of file content")
        assert any(r.command == "tail" for r in result)

    # ===== LESS =====
    def test_less_basic(self, detector):
        result = detector.detect_command("less largefile.txt")
        assert result[0].command == "less"

    def test_less_pager(self, detector):
        result = detector.detect_command("page through file")
        assert any(r.command == "less" for r in result)

    def test_less_scroll(self, detector):
        result = detector.detect_command("scroll file content")
        assert any(r.command == "less" for r in result)

    # ===== WC =====
    def test_wc_basic(self, detector):
        result = detector.detect_command("wc file.txt")
        assert result[0].command == "wc"

    def test_wc_count_lines(self, detector):
        result = detector.detect_command("count lines in file")
        assert any(r.command == "wc" for r in result)

    def test_wc_count_words(self, detector):
        result = detector.detect_command("count words in document")
        assert any(r.command == "wc" for r in result)

    def test_wc_polish(self, detector):
        result = detector.detect_command("policz linie w pliku")
        assert any(r.command == "wc" for r in result)

    # ===== SORT =====
    def test_sort_basic(self, detector):
        result = detector.detect_command("sort names.txt")
        assert result[0].command == "sort"

    def test_sort_polish(self, detector):
        result = detector.detect_command("sortuj plik alfabetycznie")
        assert any(r.command == "sort" for r in result)

    def test_sort_order(self, detector):
        result = detector.detect_command("order file content")
        assert any(r.command == "sort" for r in result)

    # ===== UNIQ =====
    def test_uniq_basic(self, detector):
        result = detector.detect_command("uniq duplicates.txt")
        assert result[0].command == "uniq"

    def test_uniq_remove_duplicates(self, detector):
        result = detector.detect_command("remove duplicates from file")
        assert any(r.command == "uniq" for r in result)

    def test_uniq_polish(self, detector):
        result = detector.detect_command("usuń duplikaty z pliku")
        assert any(r.command == "uniq" for r in result)

    def test_uniq_unique(self, detector):
        result = detector.detect_command("show unique lines")
        assert any(r.command == "uniq" for r in result)

    # ===== CUT =====
    def test_cut_basic(self, detector):
        result = detector.detect_command("cut -d',' -f1 data.csv")
        assert result[0].command == "cut"

    def test_cut_extract_column(self, detector):
        result = detector.detect_command("extract column from file")
        assert any(r.command == "cut" for r in result)

    def test_cut_extract_field(self, detector):
        result = detector.detect_command("extract field with delimiter")
        assert any(r.command == "cut" for r in result)

    # ===== TR =====
    def test_tr_basic(self, detector):
        result = detector.detect_command("tr 'a-z' 'A-Z'")
        assert result[0].command == "tr"

    def test_tr_uppercase(self, detector):
        result = detector.detect_command("convert to uppercase")
        assert any(r.command == "tr" for r in result)

    def test_tr_lowercase(self, detector):
        result = detector.detect_command("convert to lowercase")
        assert any(r.command == "tr" for r in result)

    def test_tr_translate(self, detector):
        result = detector.detect_command("translate characters")
        assert any(r.command == "tr" for r in result)

    # ===== DIFF =====
    def test_diff_basic(self, detector):
        result = detector.detect_command("diff file1.txt file2.txt")
        assert result[0].command == "diff"

    def test_diff_compare(self, detector):
        result = detector.detect_command("compare two files")
        assert any(r.command == "diff" for r in result)

    def test_diff_differences(self, detector):
        result = detector.detect_command("show differences between files")
        assert any(r.command == "diff" for r in result)

    def test_diff_polish(self, detector):
        result = detector.detect_command("porównaj pliki")
        assert any(r.command == "diff" for r in result)
