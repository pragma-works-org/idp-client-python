from __future__ import annotations

from collections.abc import Mapping
from io import BytesIO
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from .. import types
from ..models.result_format import ResultFormat, check_result_format
from ..types import UNSET, File, Unset

T = TypeVar("T", bound="ExtractSyncBody")


@_attrs_define
class ExtractSyncBody:
    """
    Attributes:
        file (File):
        format_ (ResultFormat | Unset): Extraction output format. Default: `markdown`.
        languages (str | Unset): Comma-separated OCR language hints (e.g. 'en,es').
    """

    file: File
    format_: ResultFormat | Unset = UNSET
    languages: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        file = self.file.to_tuple()

        format_: str | Unset = UNSET
        if not isinstance(self.format_, Unset):
            format_ = self.format_

        languages = self.languages

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "file": file,
            }
        )
        if format_ is not UNSET:
            field_dict["format"] = format_
        if languages is not UNSET:
            field_dict["languages"] = languages

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        files.append(("file", self.file.to_tuple()))

        if not isinstance(self.format_, Unset):
            files.append(("format", (None, str(self.format_).encode(), "text/plain")))

        if not isinstance(self.languages, Unset):
            files.append(("languages", (None, str(self.languages).encode(), "text/plain")))

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        file = File(payload=BytesIO(d.pop("file")))

        _format_ = d.pop("format", UNSET)
        format_: ResultFormat | Unset
        if isinstance(_format_, Unset):
            format_ = UNSET
        else:
            format_ = check_result_format(_format_)

        languages = d.pop("languages", UNSET)

        extract_sync_body = cls(
            file=file,
            format_=format_,
            languages=languages,
        )

        extract_sync_body.additional_properties = d
        return extract_sync_body

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
