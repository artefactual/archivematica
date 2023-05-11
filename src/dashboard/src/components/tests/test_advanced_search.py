import pytest
from components.advanced_search import _normalize_date


@pytest.mark.parametrize(
    "date_input,end_date,expected_timestamp,raises_value_error",
    [
        # Test properly formatted input for start date.
        ("2021-10-01", False, 1633046400, False),
        ("2021-10-01", None, 1633046400, False),
        # Test properly formatted input for end date. This should be the Unix
        # timestamp for the following day.
        ("2021-10-01", True, 1633132800, False),
        # Test improperly formatted inputs.
        ("Dec 1 1999", False, None, True),
        ("2021-10-01T01:14:36Z", False, None, True),
        ("not a date", False, None, True),
    ],
)
def test_filesizeformat(date_input, end_date, expected_timestamp, raises_value_error):
    if raises_value_error:
        with pytest.raises(ValueError):
            _normalize_date(date_input, end_date=end_date)
    else:
        assert _normalize_date(date_input, end_date=end_date) == expected_timestamp
