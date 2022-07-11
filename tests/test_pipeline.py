import json

from pillarchain.pipeline import run


def test_fast_pipeline(tmp_path):
    m = run(out=tmp_path, fast=True)
    assert not [c for c in m["checks"] if c["status"] == "FAIL"]
    assert m["cases"] >= 25 and m["largest_differences"]["spike time"] < 5e-3
    assert 0.0415 < m["studies"]["critical_coupling"] < 0.0422
    assert len(m["studies"]["gates"]) == 12
    assert (tmp_path / "report.md").exists() and (tmp_path / "figures" / "overview.png").exists()
    records = list((tmp_path / "cases").glob("*.json"))
    assert len(records) == m["cases"] == len(list((tmp_path / "figures" / "cases").glob("*.png")))
    assert "against_reference" in json.loads(records[0].read_text())
