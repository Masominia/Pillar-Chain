import json
import subprocess
import sys

from pillarchain.cases import ROOT
from pillarchain.runner import render, run_file

CASE = ROOT / "cases" / "chain_kappa060.pil"


def test_record_is_plain_data():
    record, case, result = run_file(CASE)
    json.dumps(record)
    assert record["case"] == "chain_kappa060" and record["sites"] == 8 and record["links"] == 7
    assert record["total"] == result.total == 8 and set(record["spikes"]) == {str(s) for s in range(1, 9)}
    assert all(c["status"] == "PASS" for c in record["checks"])


def test_render_lists_sites_and_checks():
    record, _, _ = run_file(CASE)
    text = render(record)
    assert "8 sites, 7 links" in text and "site   8" in text and "PASS  each 1 8 1" in text


def cli(*args):
    return subprocess.run([sys.executable, "-m", "pillarchain", *args], capture_output=True, text=True)


def test_cli_check_passes():
    p = cli("check", str(CASE))
    assert p.returncode == 0 and "PASS" in p.stdout


def test_cli_check_fails_on_a_wrong_expectation(tmp_path):
    f = tmp_path / "wrong.pil"
    f.write_text("sites 1\nkick 1 amplitude=2\nrun 200\nexpect total 3\n")
    p = cli("check", str(f))
    assert p.returncode == 1 and "FAIL  total 3" in p.stdout


def test_cli_check_reports_unreadable_files(tmp_path):
    f = tmp_path / "bad.pil"
    f.write_text("sites 2\nlink 1 2\nrun 10\n")
    p = cli("check", str(f))
    assert p.returncode == 2 and "line 2" in p.stderr
    assert cli("check", str(tmp_path / "missing.pil")).returncode == 2
