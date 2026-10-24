"""Actions archive negotiation differs from immutable release-asset download."""
from __future__ import annotations

import io
from urllib.error import HTTPError

import pytest

pytest.importorskip("jsonschema", reason="Dedicated locked deployment-tool suite")

from Tools.pi_instance_authority import BindingError, GitHubRead


class Response(io.BytesIO):
    def __init__(self, value):
        super().__init__(value)
        self.headers = {}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


@pytest.mark.parametrize("host", [
    "production-results.blob.core.windows.net",
    "release-assets.githubusercontent.com",
    "objects.githubusercontent.com",
])
def test_actions_zip_accepts_rest_negotiation_before_anonymous_download(host):
    client = GitHubRead("synthetic-not-a-credential")
    calls = []
    zip_bytes = b"PK\x03\x04synthetic evidence archive"

    class Opener:
        def open(self, request, timeout):
            calls.append(request)
            if len(calls) == 1:
                assert request.full_url == (
                    "https://api.github.com/repos/pcvantol/djconnect-pi/actions/artifacts/123/zip")
                # Reproduce GitHub's observed HTTP415 for octet-stream on this REST endpoint.
                if request.get_header("Accept") != "application/vnd.github+json":
                    raise HTTPError(request.full_url, 415, "synthetic", {}, io.BytesIO())
                assert request.get_header("Authorization") == "Bearer synthetic-not-a-credential"
                raise HTTPError(request.full_url, 302, "synthetic", {
                    "Location": "https://"+host+"/fixture?synthetic_signed_lease=one"}, io.BytesIO())
            assert request.get_header("Authorization") is None
            assert request.get_header("Cookie") is None
            assert request.get_header("Accept") is None
            return Response(zip_bytes)

    client.opener = Opener()
    assert client.archive(123) == zip_bytes
    assert len(calls) == 2


@pytest.mark.parametrize("status", [401, 403, 415, 500])
def test_archive_http_failure_is_not_retried_or_replayed(status):
    client = GitHubRead("synthetic-not-a-credential")
    calls = []

    class Opener:
        def open(self, request, timeout):
            calls.append(request)
            raise HTTPError(request.full_url, status, "synthetic", {}, io.BytesIO())

    client.opener = Opener()
    with pytest.raises(BindingError, match="GITHUB_READ_NOT_READY"):
        client.archive(123)
    assert len(calls) == 1


@pytest.mark.parametrize("host", ["release-assets.githubusercontent.com", "objects.githubusercontent.com"])
def test_release_asset_still_negotiates_octet_stream(host):
    client = GitHubRead("synthetic-not-a-credential")
    calls = []

    class Opener:
        def open(self, request, timeout):
            calls.append(request)
            if len(calls) == 1:
                assert request.get_header("Accept") == "application/octet-stream"
                raise HTTPError(request.full_url, 302, "synthetic", {
                    "Location": "https://"+host+"/fixture"}, io.BytesIO())
            assert request.get_header("Authorization") is None
            return Response(b"immutable release bytes")

    client.opener = Opener()
    assert client.asset(123, 100) == b"immutable release bytes"
    assert len(calls) == 2


@pytest.mark.parametrize("location", [
    "https://untrusted.invalid/fixture", "http://production-results.blob.core.windows.net/fixture",
    "https://user:synthetic@production-results.blob.core.windows.net/fixture",
])
def test_actions_archive_redirect_denies_untrusted_or_credential_bearing_urls(location):
    client = GitHubRead("synthetic-not-a-credential")
    calls = []

    class Opener:
        def open(self, request, timeout):
            calls.append(request)
            raise HTTPError(request.full_url, 302, "synthetic", {"Location": location}, io.BytesIO())

    client.opener = Opener()
    with pytest.raises(BindingError):
        client.archive(123)
    assert len(calls) == 1
