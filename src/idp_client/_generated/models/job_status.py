from typing import Literal, cast

JobStatus = Literal["cancelled", "failed", "queued", "running", "succeeded"]

JOB_STATUS_VALUES: set[JobStatus] = {
    "cancelled",
    "failed",
    "queued",
    "running",
    "succeeded",
}


def check_job_status(value: str) -> JobStatus:
    if value in JOB_STATUS_VALUES:
        return cast(JobStatus, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {JOB_STATUS_VALUES!r}")
