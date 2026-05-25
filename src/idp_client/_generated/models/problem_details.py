from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.problem_details_extra_type_0 import ProblemDetailsExtraType0


T = TypeVar("T", bound="ProblemDetails")


@_attrs_define
class ProblemDetails:
    """RFC 7807 problem document. Returned with `Content-Type: application/problem+json`.

    Attributes:
        type_ (str):  Default: 'about:blank'.
        title (str):
        status (int):
        detail (str):
        extra (None | ProblemDetailsExtraType0 | Unset):
    """

    title: str
    status: int
    detail: str
    type_: str = "about:blank"
    extra: None | ProblemDetailsExtraType0 | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.problem_details_extra_type_0 import ProblemDetailsExtraType0

        type_ = self.type_

        title = self.title

        status = self.status

        detail = self.detail

        extra: dict[str, Any] | None | Unset
        if isinstance(self.extra, Unset):
            extra = UNSET
        elif isinstance(self.extra, ProblemDetailsExtraType0):
            extra = self.extra.to_dict()
        else:
            extra = self.extra

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "title": title,
                "status": status,
                "detail": detail,
            }
        )
        if extra is not UNSET:
            field_dict["extra"] = extra

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.problem_details_extra_type_0 import ProblemDetailsExtraType0

        d = dict(src_dict)
        type_ = d.pop("type")

        title = d.pop("title")

        status = d.pop("status")

        detail = d.pop("detail")

        def _parse_extra(data: object) -> None | ProblemDetailsExtraType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                extra_type_0 = ProblemDetailsExtraType0.from_dict(data)

                return extra_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ProblemDetailsExtraType0 | Unset, data)

        extra = _parse_extra(d.pop("extra", UNSET))

        problem_details = cls(
            type_=type_,
            title=title,
            status=status,
            detail=detail,
            extra=extra,
        )

        problem_details.additional_properties = d
        return problem_details

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
