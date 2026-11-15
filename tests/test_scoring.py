import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scoring import Scores

def test_robust_pass():
    assert Scores(2,2,2,1).outcome == "robust_pass"

def test_hierarchy_failure_overrides_total():
    assert Scores(0,2,2,2).outcome == "failure"

def test_validation_rejects_out_of_range():
    try:
        Scores(3,2,2,2).total
    except ValueError:
        return
    raise AssertionError("Expected ValueError")
