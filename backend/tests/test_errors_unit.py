from lands_ai_backend.api.errors import error_payload


def test_error_payload_without_details() -> None:
    payload = error_payload("QUERY_FAILED", "Unable to process request")
    assert payload == {
        "error": {
            "code": "QUERY_FAILED",
            "message": "Unable to process request",
        }
    }


def test_error_payload_with_details() -> None:
    payload = error_payload("VALIDATION_ERROR", "Invalid data", [{"loc": ["body", "name"]}])
    assert payload["error"]["code"] == "VALIDATION_ERROR"
    assert payload["error"]["details"] == [{"loc": ["body", "name"]}]
