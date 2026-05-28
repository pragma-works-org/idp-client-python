from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.open_ai_embedding_request_encoding_format import (
    OpenAIEmbeddingRequestEncodingFormat,
    check_open_ai_embedding_request_encoding_format,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="OpenAIEmbeddingRequest")


@_attrs_define
class OpenAIEmbeddingRequest:
    """OpenAI's `POST /v1/embeddings` request shape.

    `input` accepts string, list[str], list[int], list[list[int]] per the spec.
    Pre-tokenized inputs (the int variants) are rejected with 400 in v1 (Q5:A).

        Attributes:
            model (str):
            input_ (list[int] | list[list[int]] | list[str] | str):
            encoding_format (OpenAIEmbeddingRequestEncodingFormat | Unset):  Default: 'float'.
            dimensions (int | None | Unset):
            user (None | str | Unset):
    """

    model: str
    input_: list[int] | list[list[int]] | list[str] | str
    encoding_format: OpenAIEmbeddingRequestEncodingFormat | Unset = "float"
    dimensions: int | None | Unset = UNSET
    user: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        model = self.model

        input_: list[int] | list[list[int]] | list[str] | str
        if isinstance(self.input_, list):
            input_ = self.input_

        elif isinstance(self.input_, list):
            input_ = self.input_

        elif isinstance(self.input_, list):
            input_ = []
            for input_type_3_item_data in self.input_:
                input_type_3_item = input_type_3_item_data

                input_.append(input_type_3_item)

        else:
            input_ = self.input_

        encoding_format: str | Unset = UNSET
        if not isinstance(self.encoding_format, Unset):
            encoding_format = self.encoding_format

        dimensions: int | None | Unset
        if isinstance(self.dimensions, Unset):
            dimensions = UNSET
        else:
            dimensions = self.dimensions

        user: None | str | Unset
        if isinstance(self.user, Unset):
            user = UNSET
        else:
            user = self.user

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "model": model,
                "input": input_,
            }
        )
        if encoding_format is not UNSET:
            field_dict["encoding_format"] = encoding_format
        if dimensions is not UNSET:
            field_dict["dimensions"] = dimensions
        if user is not UNSET:
            field_dict["user"] = user

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        model = d.pop("model")

        def _parse_input_(data: object) -> list[int] | list[list[int]] | list[str] | str:
            try:
                if not isinstance(data, list):
                    raise TypeError()
                input_type_1 = cast(list[str], data)

                return input_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, list):
                    raise TypeError()
                input_type_2 = cast(list[int], data)

                return input_type_2
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, list):
                    raise TypeError()
                input_type_3 = []
                _input_type_3 = data
                for input_type_3_item_data in _input_type_3:
                    input_type_3_item = cast(list[int], input_type_3_item_data)

                    input_type_3.append(input_type_3_item)

                return input_type_3
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[int] | list[list[int]] | list[str] | str, data)

        input_ = _parse_input_(d.pop("input"))

        _encoding_format = d.pop("encoding_format", UNSET)
        encoding_format: OpenAIEmbeddingRequestEncodingFormat | Unset
        if isinstance(_encoding_format, Unset):
            encoding_format = UNSET
        else:
            encoding_format = check_open_ai_embedding_request_encoding_format(_encoding_format)

        def _parse_dimensions(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        dimensions = _parse_dimensions(d.pop("dimensions", UNSET))

        def _parse_user(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        user = _parse_user(d.pop("user", UNSET))

        open_ai_embedding_request = cls(
            model=model,
            input_=input_,
            encoding_format=encoding_format,
            dimensions=dimensions,
            user=user,
        )

        open_ai_embedding_request.additional_properties = d
        return open_ai_embedding_request

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
