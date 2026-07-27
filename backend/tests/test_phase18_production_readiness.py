from config import (
    Settings,
    build_health_payload,
    origin_is_allowed,
    public_error_detail,
)


def make_settings(environment="development", previews=False):
    return Settings(
        app_name="Smart Pantry",
        app_version="test",
        environment=environment,
        log_level="INFO",
        allowed_origins=("http://localhost:5173",),
        allow_vercel_previews=previews,
    )


def test_health_payload_exposes_release_metadata_without_secrets():
    payload = build_health_payload(make_settings())
    assert payload == {
        "status": "ok",
        "service": "Smart Pantry",
        "version": "test",
        "environment": "development",
    }


def test_known_local_origin_is_allowed():
    assert origin_is_allowed("http://localhost:5173", make_settings())


def test_unknown_non_vercel_origin_is_rejected():
    assert not origin_is_allowed("https://example.invalid", make_settings())


def test_vercel_preview_requires_explicit_setting():
    origin = "https://smart-pantry-git-demo.vercel.app"
    assert not origin_is_allowed(origin, make_settings(previews=False))
    assert origin_is_allowed(origin, make_settings(previews=True))


def test_production_errors_do_not_leak_exception_details():
    detail = public_error_detail(
        "The recommendation engine failed",
        RuntimeError("secret detail"),
        make_settings(environment="production"),
    )
    assert detail == "The recommendation engine failed"


def test_development_errors_remain_diagnostic():
    detail = public_error_detail(
        "The recommendation engine failed",
        RuntimeError("diagnostic"),
        make_settings(environment="development"),
    )
    assert "RuntimeError" in detail
    assert "diagnostic" in detail
