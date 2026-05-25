from typing import Literal, cast

ResultFormat = Literal["doctags", "json", "markdown", "text"]

RESULT_FORMAT_VALUES: set[ResultFormat] = {
    "doctags",
    "json",
    "markdown",
    "text",
}


def check_result_format(value: str) -> ResultFormat:
    if value in RESULT_FORMAT_VALUES:
        return cast(ResultFormat, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {RESULT_FORMAT_VALUES!r}")
