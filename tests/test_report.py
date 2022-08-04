import pandas as pd

from pillarchain.report import md_table


def test_md_table():
    text = md_table(pd.DataFrame({"a": [1.23456, 2.0], "b": ["x", "y"]}), 2, index=False)
    assert text.splitlines()[0].startswith("| a") and "1.23" in text and len(text.splitlines()) == 4
