"""Unit tests for summarize_locust_csv.py"""

# Import functions from the summarizer script
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from summarize_locust_csv import (
    build_table,
    parse_stats_csv,
    scenario_name_from_path,
)


class TestParseStatsCsv:
    """Test CSV parsing and metrics extraction."""

    def test_parse_valid_csv(self, tmp_path: Path) -> None:
        """Parse a valid stats CSV file."""
        csv_file = tmp_path / "test_stats.csv"
        csv_file.write_text(
            "Type,Name,Request Count,Failure Count,Median Response Time,Average Response Time,Min Response Time,Max Response Time,Average Content Size,Requests/s,Failures/s,50%,66%,75%,80%,90%,95%,98%,99%,99.9%,99.99%,100%\n"
            "GET,/api/endpoint,100,5,250,300,100,1000,512,10.5,0.5,250,280,310,340,400,450,500,550,900,990,1000\n",
            encoding="utf-8",
        )
        metrics = parse_stats_csv(csv_file)
        assert metrics["requests"] == 100
        assert metrics["failures"] == 5
        assert metrics["avg_ms"] == 300.0
        assert metrics["p50_ms"] == 250.0
        assert metrics["p95_ms"] == 450.0
        assert metrics["p99_ms"] == 550.0
        assert metrics["rps"] == 10.5

    def test_parse_missing_file(self, tmp_path: Path) -> None:
        """Handle missing CSV file gracefully."""
        csv_file = tmp_path / "nonexistent.csv"
        metrics = parse_stats_csv(csv_file)
        assert metrics.get("_missing") is True

    def test_parse_empty_csv(self, tmp_path: Path) -> None:
        """Handle empty CSV file (header only)."""
        csv_file = tmp_path / "empty_stats.csv"
        csv_file.write_text("Type,Name,Request Count,Failure Count\n", encoding="utf-8")
        metrics = parse_stats_csv(csv_file)
        assert metrics.get("_empty") is True

    def test_parse_zero_requests(self, tmp_path: Path) -> None:
        """Parse CSV with zero requests."""
        csv_file = tmp_path / "zero_stats.csv"
        csv_file.write_text(
            "Type,Name,Request Count,Failure Count,Median Response Time,Average Response Time,Min Response Time,Max Response Time,Average Content Size,Requests/s,Failures/s,50%,66%,75%,80%,90%,95%,98%,99%,99.9%,99.99%,100%\n"
            "GET,/api/endpoint,0,0,0,0,0,0,0,0.0,0.0,0,0,0,0,0,0,0,0,0,0,0\n",
            encoding="utf-8",
        )
        metrics = parse_stats_csv(csv_file)
        assert metrics["requests"] == 0
        assert metrics["failures"] == 0


class TestScenarioNameFromPath:
    """Test scenario name normalization."""

    def test_strip_timestamp(self) -> None:
        """Strip timestamp suffix from scenario name."""
        path = Path("outputs/load_test_light_20251018_161525_stats.csv")
        assert scenario_name_from_path(path) == "light"

    def test_no_timestamp(self) -> None:
        """Handle scenario name without timestamp."""
        path = Path("outputs/load_test_medium_stats.csv")
        assert scenario_name_from_path(path) == "medium"

    def test_non_standard_name(self) -> None:
        """Handle non-standard file names."""
        path = Path("custom_scenario_stats.csv")
        assert scenario_name_from_path(path) == "custom_scenario_stats"


class TestBuildTable:
    """Test Markdown table generation."""

    def test_basic_table(self) -> None:
        """Generate basic table without optional columns."""
        entries = [
            (
                "light",
                {
                    "requests": 100,
                    "failures": 0,
                    "avg_ms": 250.0,
                    "p50_ms": 200.0,
                    "p95_ms": 400.0,
                    "p99_ms": 500.0,
                    "rps": 10.5,
                },
            ),
        ]
        table = build_table(entries, ascii_status=True, with_success_rate=False, with_overall=False)
        assert "| Scenario | Total | Fail | Avg (ms) | P50 | P95 | P99 | Req/s | Status |" in table
        assert "| light | 100 | 0 | 250 | 200 | 400 | 500 | 10.5 | OK |" in table
        assert "Overall" not in table
        assert "Success (%)" not in table

    def test_table_with_success_rate(self) -> None:
        """Generate table with Success (%) column."""
        entries = [
            (
                "light",
                {
                    "requests": 100,
                    "failures": 10,
                    "avg_ms": 250.0,
                    "p50_ms": 200.0,
                    "p95_ms": 400.0,
                    "p99_ms": 500.0,
                    "rps": 10.5,
                },
            ),
        ]
        table = build_table(entries, ascii_status=True, with_success_rate=True, with_overall=False)
        assert (
            "| Scenario | Total | Fail | Success (%) | Avg (ms) | P50 | P95 | P99 | Req/s | Status |"
            in table
        )
        assert "| light | 100 | 10 | 90% |" in table

    def test_table_with_overall(self) -> None:
        """Generate table with Overall aggregation row."""
        entries = [
            (
                "light",
                {
                    "requests": 50,
                    "failures": 0,
                    "avg_ms": 200.0,
                    "p50_ms": 180.0,
                    "p95_ms": 300.0,
                    "p99_ms": 400.0,
                    "rps": 5.0,
                },
            ),
            (
                "heavy",
                {
                    "requests": 100,
                    "failures": 5,
                    "avg_ms": 800.0,
                    "p50_ms": 700.0,
                    "p95_ms": 1200.0,
                    "p99_ms": 1500.0,
                    "rps": 8.0,
                },
            ),
        ]
        table = build_table(entries, ascii_status=True, with_success_rate=False, with_overall=True)
        assert "Overall" in table
        # Overall Total = 50 + 100 = 150
        assert "| Overall | 150 | 5 |" in table
        # Overall RPS = 5.0 + 8.0 = 13.0
        assert "| 13.0 |" in table

    def test_table_with_success_rate_and_overall(self) -> None:
        """Generate table with both Success (%) and Overall."""
        entries = [
            (
                "light",
                {
                    "requests": 50,
                    "failures": 0,
                    "avg_ms": 200.0,
                    "p50_ms": 180.0,
                    "p95_ms": 300.0,
                    "p99_ms": 400.0,
                    "rps": 5.0,
                },
            ),
            (
                "heavy",
                {
                    "requests": 100,
                    "failures": 10,
                    "avg_ms": 800.0,
                    "p50_ms": 700.0,
                    "p95_ms": 1200.0,
                    "p99_ms": 1500.0,
                    "rps": 8.0,
                },
            ),
        ]
        table = build_table(entries, ascii_status=True, with_success_rate=True, with_overall=True)
        assert "Success (%)" in table
        assert "Overall" in table
        # light: 100%, heavy: 90%, Overall: (50+90)/150 = 93.33% ~= 93%
        assert "| light | 50 | 0 | 100% |" in table
        assert "| heavy | 100 | 10 | 90% |" in table
        assert "| Overall | 150 | 10 | 93% |" in table

    def test_missing_file_handling(self) -> None:
        """Handle missing files in table generation."""
        entries = [
            ("missing", {"_missing": True}),
        ]
        table = build_table(entries, ascii_status=True, with_success_rate=False, with_overall=False)
        assert "| missing | - | - | - | - | - | - | - | missing |" in table

    def test_empty_file_handling(self) -> None:
        """Handle empty CSV files in table generation."""
        entries = [
            ("empty", {"_empty": True}),
        ]
        table = build_table(entries, ascii_status=True, with_success_rate=False, with_overall=False)
        assert "| empty | 0 | 0 | 0 | 0 | 0 | 0 | 0 | empty |" in table

    def test_zero_requests_success_rate(self) -> None:
        """Handle zero requests when calculating success rate."""
        entries = [
            (
                "zero",
                {
                    "requests": 0,
                    "failures": 0,
                    "avg_ms": 0.0,
                    "p50_ms": 0.0,
                    "p95_ms": 0.0,
                    "p99_ms": 0.0,
                    "rps": 0.0,
                },
            ),
        ]
        table = build_table(entries, ascii_status=True, with_success_rate=True, with_overall=False)
        # Success rate should be 0% when there are no requests
        assert "| zero | 0 | 0 | 0% |" in table

    def test_all_failures(self) -> None:
        """Handle scenario with 100% failure rate."""
        entries = [
            (
                "fail",
                {
                    "requests": 50,
                    "failures": 50,
                    "avg_ms": 500.0,
                    "p50_ms": 450.0,
                    "p95_ms": 600.0,
                    "p99_ms": 700.0,
                    "rps": 5.0,
                },
            ),
        ]
        table = build_table(entries, ascii_status=True, with_success_rate=True, with_overall=False)
        assert "| fail | 50 | 50 | 0% |" in table
        assert "FAIL" in table

    def test_emoji_status(self) -> None:
        """Test emoji status symbols (when not using ASCII)."""
        entries = [
            (
                "ok",
                {
                    "requests": 100,
                    "failures": 0,
                    "avg_ms": 250.0,
                    "p50_ms": 200.0,
                    "p95_ms": 400.0,
                    "p99_ms": 500.0,
                    "rps": 10.5,
                },
            ),
            (
                "fail",
                {
                    "requests": 100,
                    "failures": 10,
                    "avg_ms": 250.0,
                    "p50_ms": 200.0,
                    "p95_ms": 400.0,
                    "p99_ms": 500.0,
                    "rps": 10.5,
                },
            ),
        ]
        table = build_table(
            entries, ascii_status=False, with_success_rate=False, with_overall=False
        )
        # Should contain emoji (or OK/FAIL if encoding not supported)
        assert "✅" in table or "OK" in table
        assert "❌" in table or "FAIL" in table
