from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ConfidenceSummary")


@_attrs_define
class ConfidenceSummary:
    """Per-document confidence summary. All fields optional; absent when docling-serve doesn't report.

    Attributes:
        mean_grade (None | str | Unset):
        low_grade (None | str | Unset):
        mean_score (float | None | Unset):
        low_score (float | None | Unset):
    """

    mean_grade: None | str | Unset = UNSET
    low_grade: None | str | Unset = UNSET
    mean_score: float | None | Unset = UNSET
    low_score: float | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        mean_grade: None | str | Unset
        if isinstance(self.mean_grade, Unset):
            mean_grade = UNSET
        else:
            mean_grade = self.mean_grade

        low_grade: None | str | Unset
        if isinstance(self.low_grade, Unset):
            low_grade = UNSET
        else:
            low_grade = self.low_grade

        mean_score: float | None | Unset
        if isinstance(self.mean_score, Unset):
            mean_score = UNSET
        else:
            mean_score = self.mean_score

        low_score: float | None | Unset
        if isinstance(self.low_score, Unset):
            low_score = UNSET
        else:
            low_score = self.low_score

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if mean_grade is not UNSET:
            field_dict["mean_grade"] = mean_grade
        if low_grade is not UNSET:
            field_dict["low_grade"] = low_grade
        if mean_score is not UNSET:
            field_dict["mean_score"] = mean_score
        if low_score is not UNSET:
            field_dict["low_score"] = low_score

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_mean_grade(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        mean_grade = _parse_mean_grade(d.pop("mean_grade", UNSET))

        def _parse_low_grade(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        low_grade = _parse_low_grade(d.pop("low_grade", UNSET))

        def _parse_mean_score(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        mean_score = _parse_mean_score(d.pop("mean_score", UNSET))

        def _parse_low_score(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        low_score = _parse_low_score(d.pop("low_score", UNSET))

        confidence_summary = cls(
            mean_grade=mean_grade,
            low_grade=low_grade,
            mean_score=mean_score,
            low_score=low_score,
        )

        confidence_summary.additional_properties = d
        return confidence_summary

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
