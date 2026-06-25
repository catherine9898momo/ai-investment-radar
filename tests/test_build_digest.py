import datetime as dt
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


def load_build_digest():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "build_digest.py"
    spec = importlib.util.spec_from_file_location("build_digest", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BuildDigestOutputTests(unittest.TestCase):
    def test_write_outputs_creates_chinese_digest(self):
        build_digest = load_build_digest()
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch.object(build_digest, "DIST_DIR", Path(temp_dir)):
                with mock.patch.dict(os.environ, {"LOOKBACK_DAYS": "14"}):
                    item = {
                        "feed": "AI Data Center Capex",
                        "tags": ["data_center", "power"],
                        "title": "AI data center power purchase agreement",
                        "link": "https://example.com/item",
                        "published": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "summary": "A new power purchase agreement supports AI data center capacity.",
                        "signals": {
                            "hard_signal": ["power purchase", "capacity"],
                            "risk_signal": [],
                            "ai_value_chain": ["data center", "power"],
                        },
                        "signal_score": 4,
                    }

                    build_digest.write_outputs([item], [])

                    zh_digest = next(Path(temp_dir).glob("daily-digest-*.zh.md")).read_text(encoding="utf-8")

        self.assertIn("# AI 投资雷达", zh_digest)
        self.assertIn("回看窗口：14 天", zh_digest)
        self.assertIn("## 重点信号条目", zh_digest)
        self.assertIn("- 来源：AI Data Center Capex", zh_digest)
        self.assertIn("- 信号：硬信号: power purchase, capacity; AI 价值链: data center, power", zh_digest)
        self.assertIn("- 中文摘要：这条信息属于硬信号", zh_digest)
        self.assertIn("电力采购协议", zh_digest)
        self.assertIn("数据中心", zh_digest)
        self.assertIn("- 阅读重点：", zh_digest)
        self.assertIn("- 原文摘要：A new power purchase agreement supports AI data center capacity.", zh_digest)

    def test_no_signal_items_use_title_context_for_chinese_summary(self):
        build_digest = load_build_digest()
        base_item = {
            "feed": "AI Data Center Capex",
            "tags": ["data_center", "capex", "power"],
            "link": "https://example.com/item",
            "published": dt.datetime.now(dt.timezone.utc).isoformat(),
            "summary": "",
            "signals": {
                "hard_signal": [],
                "risk_signal": [],
                "ai_value_chain": [],
            },
            "signal_score": 0,
        }
        stock_item = {
            **base_item,
            "title": "SCHG: A Bet On Massive AI CapEx Growth",
        }
        forecast_item = {
            **base_item,
            "title": "AI Capex Forecast Raised to $5.5tn: Who Captures the Next Dollar?",
        }

        stock_summary = build_digest.chinese_summary(stock_item)
        forecast_summary = build_digest.chinese_summary(forecast_item)
        stock_focus = build_digest.chinese_focus(stock_item)
        forecast_focus = build_digest.chinese_focus(forecast_item)

        self.assertNotEqual(stock_summary, forecast_summary)
        self.assertNotEqual(stock_focus, forecast_focus)
        self.assertIn("SCHG", stock_summary)
        self.assertIn("股票或 ETF", stock_summary)
        self.assertIn("资本开支预测", forecast_summary)
        self.assertIn("预测", forecast_focus)

    def test_write_outputs_creates_daily_investment_concept_report(self):
        build_digest = load_build_digest()
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch.object(build_digest, "DIST_DIR", Path(temp_dir)):
                with mock.patch.dict(os.environ, {"LOOKBACK_DAYS": "14"}):
                    build_digest.write_outputs([], [])

                    concept_report = next(Path(temp_dir).glob("daily-concept-*.zh.md")).read_text(encoding="utf-8")

        self.assertIn("# 每日价值投资课程", concept_report)
        self.assertIn("## 今日章节", concept_report)
        self.assertIn("《The Intelligent Investor》", concept_report)
        self.assertIn("## 本章要点", concept_report)
        self.assertIn("## 执行要点", concept_report)
        self.assertIn("怎么做：", concept_report)
        self.assertIn("怎么检查：", concept_report)
        self.assertIn("## 简单理解", concept_report)
        self.assertIn("## 今天可以做", concept_report)
        self.assertIn("## 参考来源", concept_report)

    def test_write_outputs_uses_dated_filenames_and_removes_legacy_names(self):
        build_digest = load_build_digest()
        with tempfile.TemporaryDirectory() as temp_dir:
            dist_dir = Path(temp_dir)
            legacy_names = [
                "daily-digest.md",
                "daily-digest.zh.md",
                "daily-items.json",
                "daily-concept.zh.md",
                "value-investing-progress.json",
            ]
            for name in legacy_names:
                (dist_dir / name).write_text("legacy", encoding="utf-8")

            with mock.patch.object(build_digest, "DIST_DIR", dist_dir):
                with mock.patch.dict(os.environ, {"LOOKBACK_DAYS": "14"}):
                    build_digest.write_outputs([], [])

            dated_files = {path.name for path in dist_dir.iterdir()}

        self.assertIn("daily-digest-2026-06-25.md", dated_files)
        self.assertIn("daily-digest-2026-06-25.zh.md", dated_files)
        self.assertIn("daily-items-2026-06-25.json", dated_files)
        self.assertIn("daily-concept-2026-06-25.zh.md", dated_files)
        self.assertIn("value-investing-progress-2026-06-25.json", dated_files)
        self.assertTrue(set(legacy_names).isdisjoint(dated_files))

    def test_learning_progress_loads_latest_dated_snapshot(self):
        build_digest = load_build_digest()
        with tempfile.TemporaryDirectory() as temp_dir:
            dist_dir = Path(temp_dir)
            old_progress = {"last_date": "2026-06-24", "current_index": 0, "next_index": 1}
            latest_progress = {"last_date": "2026-06-25", "current_index": 1, "next_index": 2}
            (dist_dir / "value-investing-progress-2026-06-24.json").write_text(
                json.dumps(old_progress), encoding="utf-8"
            )
            (dist_dir / "value-investing-progress-2026-06-25.json").write_text(
                json.dumps(latest_progress), encoding="utf-8"
            )

            with mock.patch.object(build_digest, "DIST_DIR", dist_dir):
                progress = build_digest.load_learning_progress()

        self.assertEqual(progress["last_date"], "2026-06-25")
        self.assertEqual(progress["next_index"], 2)

    def test_daily_investment_concept_follows_book_chapter_sequence(self):
        build_digest = load_build_digest()
        first = build_digest.concept_for_date(dt.date(2026, 6, 24))
        second = build_digest.concept_for_date(dt.date(2026, 6, 25))

        self.assertEqual(first["book"], "The Intelligent Investor")
        self.assertEqual(first["chapter_number"], 1)
        self.assertEqual(second["chapter_number"], 2)
        self.assertNotEqual(first["chapter_title"], second["chapter_title"])
        self.assertIn("how", first["key_points"][0])
        self.assertIn("check", first["key_points"][0])

    def test_daily_investment_progress_advances_once_per_day(self):
        build_digest = load_build_digest()
        with tempfile.TemporaryDirectory() as temp_dir:
            dist_dir = Path(temp_dir)
            with mock.patch.object(build_digest, "DIST_DIR", dist_dir):
                build_digest.write_daily_concept(dt.date(2026, 6, 24))
                first_report = (dist_dir / "daily-concept-2026-06-24.zh.md").read_text(encoding="utf-8")
                first_progress = json.loads((dist_dir / "value-investing-progress-2026-06-24.json").read_text(encoding="utf-8"))

                build_digest.write_daily_concept(dt.date(2026, 6, 24))
                same_day_report = (dist_dir / "daily-concept-2026-06-24.zh.md").read_text(encoding="utf-8")
                same_day_progress = json.loads((dist_dir / "value-investing-progress-2026-06-24.json").read_text(encoding="utf-8"))

                build_digest.write_daily_concept(dt.date(2026, 6, 25))
                next_day_report = (dist_dir / "daily-concept-2026-06-25.zh.md").read_text(encoding="utf-8")
                next_day_progress = json.loads((dist_dir / "value-investing-progress-2026-06-25.json").read_text(encoding="utf-8"))

        self.assertIn("第 1 章", first_report)
        self.assertEqual(first_report, same_day_report)
        self.assertEqual(first_progress, same_day_progress)
        self.assertIn("第 2 章", next_day_report)
        self.assertEqual(next_day_progress["current_chapter"], 2)
        self.assertEqual(next_day_progress["next_index"], 2)

    def test_learning_progress_records_supplied_booklist_route(self):
        build_digest = load_build_digest()

        _lesson, progress = build_digest.concept_for_progress(dt.date(2026, 6, 24), {})

        self.assertEqual(progress["route_name"], "路线 A：想学投资")
        self.assertEqual(progress["current_book"], "The Intelligent Investor")
        self.assertEqual(progress["current_book_zh"], "聪明的投资者")
        self.assertEqual(progress["current_route_position"], 1)
        self.assertEqual(progress["route_total_books"], 6)
        self.assertEqual(progress["next_book"], "The Intelligent Investor")
        self.assertEqual(progress["next_book_zh"], "聪明的投资者")

    def test_learning_progress_moves_to_next_book_when_current_book_is_finished(self):
        build_digest = load_build_digest()
        last_intelligent_investor_index = max(
            index
            for index, lesson in enumerate(build_digest.VALUE_INVESTING_CURRICULUM)
            if lesson["book"] == "The Intelligent Investor"
        )
        previous_progress = {
            "last_date": "2026-06-24",
            "current_index": last_intelligent_investor_index,
            "next_index": last_intelligent_investor_index + 1,
        }

        lesson, progress = build_digest.concept_for_progress(dt.date(2026, 6, 25), previous_progress)

        self.assertEqual(lesson["book"], "Common Stocks and Uncommon Profits")
        self.assertEqual(progress["current_book"], "Common Stocks and Uncommon Profits")
        self.assertEqual(progress["current_book_zh"], "怎样选择成长股")
        self.assertEqual(progress["current_route_position"], 2)
        self.assertIn("聪明的投资者", progress["completed_books_zh"])


if __name__ == "__main__":
    unittest.main()
