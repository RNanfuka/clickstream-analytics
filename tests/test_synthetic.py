import pytest

from omnihealth.pipeline import run_pipeline
from omnihealth.synthetic import generate_events


def test_generator_is_repeatable_and_expected_metrics_match_pipeline(tmp_path):
    first, second = tmp_path / "first.csv", tmp_path / "second.csv"
    expected = generate_events(first, sessions=23, seed=17)
    assert generate_events(second, sessions=23, seed=17) == expected
    assert first.read_bytes() == second.read_bytes()
    actual = run_pipeline(first, tmp_path / "out", "synthetic_fixture")
    for key in ("sessions", "converted_sessions", "session_conversion_rate"):
        assert actual[key] == expected[key]
    assert actual["valid_events"] == expected["events"] == 92


def test_generator_protects_existing_file_and_supports_zero_conversions(tmp_path):
    target = tmp_path / "events.csv"
    assert generate_events(target, 3, conversion_probability=0)["converted_sessions"] == 0
    original = target.read_bytes()
    with pytest.raises(FileExistsError):
        generate_events(target)
    assert target.read_bytes() == original
