from typing import Literal, cast

OpenAIEmbeddingRequestEncodingFormat = Literal["base64", "float"]

OPEN_AI_EMBEDDING_REQUEST_ENCODING_FORMAT_VALUES: set[OpenAIEmbeddingRequestEncodingFormat] = {
    "base64",
    "float",
}


def check_open_ai_embedding_request_encoding_format(
    value: str,
) -> OpenAIEmbeddingRequestEncodingFormat:
    if value in OPEN_AI_EMBEDDING_REQUEST_ENCODING_FORMAT_VALUES:
        return cast(OpenAIEmbeddingRequestEncodingFormat, value)
    raise TypeError(
        f"Unexpected value {value!r}. Expected one of {OPEN_AI_EMBEDDING_REQUEST_ENCODING_FORMAT_VALUES!r}"
    )
