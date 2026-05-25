from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.confidence_summary import ConfidenceSummary


T = TypeVar("T", bound="ExtractResponse")


@_attrs_define
class ExtractResponse:
    """Synchronous-extraction response and async result envelope (same shape).

    Attributes:
        pages (list[str]): One string per page in document order.
        page_count (int):
        processing_time_seconds (float):
        confidence (ConfidenceSummary | None | Unset):
    """

    pages: list[str]
    page_count: int
    processing_time_seconds: float
    confidence: ConfidenceSummary | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.confidence_summary import ConfidenceSummary

        pages = self.pages

        page_count = self.page_count

        processing_time_seconds = self.processing_time_seconds

        confidence: dict[str, Any] | None | Unset
        if isinstance(self.confidence, Unset):
            confidence = UNSET
        elif isinstance(self.confidence, ConfidenceSummary):
            confidence = self.confidence.to_dict()
        else:
            confidence = self.confidence

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "pages": pages,
                "page_count": page_count,
                "processing_time_seconds": processing_time_seconds,
            }
        )
        if confidence is not UNSET:
            field_dict["confidence"] = confidence

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.confidence_summary import ConfidenceSummary

        d = dict(src_dict)
        pages = cast(list[str], d.pop("pages"))

        page_count = d.pop("page_count")

        processing_time_seconds = d.pop("processing_time_seconds")

        def _parse_confidence(data: object) -> ConfidenceSummary | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                confidence_type_0 = ConfidenceSummary.from_dict(data)

                return confidence_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ConfidenceSummary | None | Unset, data)

        confidence = _parse_confidence(d.pop("confidence", UNSET))

        extract_response = cls(
            pages=pages,
            page_count=page_count,
            processing_time_seconds=processing_time_seconds,
            confidence=confidence,
        )

        extract_response.additional_properties = d
        return extract_response

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
