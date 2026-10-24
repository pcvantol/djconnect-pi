"""Synthetic successor integration; no real operative manifest or device effects."""

import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("jsonschema", reason="Dedicated locked deployment-tool suite")
from test_pi_wall4_recovery_contract import CONSUMER, authority, fixtures
from test_pi_wall4_recovery_release import BOOT, OBS, RUN, SERVICES, Client

from Tools import pi_wall4_previous_failure as original_v1
from Tools import pi_wall4_recovery_authority as wire
from Tools import pi_wall4_recovery_release as release
from Tools.pi_instance_contract import BindingError
from Tools.pi_instance_release import PhaseFailure
from Tools.pi_wall4_latest_failure import constant_descriptor, latest_descriptor


def test_original_v1_descriptor_still_equals_original_released_v2_schema():
    s = json.loads(
        (
            Path(wire.__file__).parent
            / "pi_contract/PI_RC6_WALL4_RECOVERY_MANIFEST_V2.schema.json"
        ).read_bytes()
    )
    original = constant_descriptor(
        s["properties"]["recovery"]["properties"]["previous_recovery_attempt"]
    )
    assert wire.exact_json(original_v1.previous_spec(), original)
    assert wire.exact_json(wire.previous_spec(), latest_descriptor())
    assert wire.exact_json(wire.previous_spec()["previous_recovery_attempt"], original)


@pytest.mark.parametrize(
    "sha",
    [
        "0dde0abe22a0859f170a7c1d3eab41f1ade44d37",
        "77fc4047f797066876c5345e8e43b346ab96d782",
        "2e7479d0d15aa11ad3bff4c8103c18dbb1f2c32a",
    ],
)
def test_old_runtime_v1_and_latest_failed_v2_cannot_be_new_consumer(sha):
    req, m, p = fixtures()
    m["consumer"]["source_sha"] = sha
    with pytest.raises(BindingError, match="RECOVERY_CONSUMER_MISMATCH"):
        wire.validate(req, m, sha, p)


@pytest.mark.parametrize(
    "schema,prefix",
    [(4, "recovery-"), (5, "recovery-v2-"), (6, "recovery-v2-"), (5, "recovery-v3-")],
)
def test_no_old_or_mixed_version_manifest(schema, prefix):
    req, m, p = fixtures()
    m["schema_version"] = schema
    m["manifest_id"] = "release-4.0.0-rc.6-pi-wall4-" + prefix + "SYNTHETIC"
    req["manifest_id"] = m["manifest_id"]
    with pytest.raises(BindingError):
        wire.validate(req, m, CONSUMER, p)


@pytest.mark.parametrize(
    "key",
    ["PI_RC6_WALL4_RECOVERY_V2_CORE_SHA", "PI_RC6_WALL4_RECOVERY_V2_MANIFEST_SHA256"],
)
def test_old_public_config_names_are_never_fallbacks(key):

    class NoNetwork:
        def json(self, *_):
            raise AssertionError("network before closed V3 pair")

    with pytest.raises(BindingError):
        wire.resolve(NoNetwork(), fixtures()[0], CONSUMER, {key: "d" * 40})


@pytest.mark.parametrize(
    "core,manifest",
    [
        ("83744790decc6ef8940795dc2c9c0e3fb058173b", "e" * 64),
        ("d" * 40, "c63ca35c9974b701e70d649a0cbc77a187a2ee83dc329602d6c887a680fcc51d"),
        (
            "83744790decc6ef8940795dc2c9c0e3fb058173b",
            "c63ca35c9974b701e70d649a0cbc77a187a2ee83dc329602d6c887a680fcc51d",
        ),
    ],
)
def test_old_v2_pair_cannot_be_relabelled_v3(core, manifest):

    class NoNetwork:
        def json(self, *_):
            raise AssertionError("historical pair admitted")

    with pytest.raises(BindingError, match="RECOVERY_ORIGINAL_PAIR_REJECTED"):
        wire.resolve(
            NoNetwork(),
            fixtures()[0],
            CONSUMER,
            dict(zip(wire.CONFIG, (core, manifest), strict=True)),
        )


@pytest.mark.parametrize("denied", [wire.CORE_SOURCE, wire.CORE_FINALIZATION])
def test_unqualified_real_source_or_finalization_fails_before_network_or_effect(
    monkeypatch, denied
):
    seen = []

    def qualified(client, repo, sha):
        seen.append(sha)
        if sha == denied:
            raise BindingError("EXACT_MAIN_RELEASE_EVIDENCE_MISSING")

    monkeypatch.setattr(wire, "qualified", qualified)

    class NoNetwork:
        def json(self, *_):
            raise AssertionError("producer file before qualified Final")

    with pytest.raises(BindingError, match="EXACT_MAIN_RELEASE_EVIDENCE_MISSING"):
        wire.resolve(
            NoNetwork(),
            fixtures()[0],
            CONSUMER,
            dict(zip(wire.CONFIG, ("d" * 40, "e" * 64), strict=True)),
        )
    assert seen[-1] == denied


@pytest.mark.parametrize("operation", ["recover", "smoke"])
@pytest.mark.parametrize("stage", ["before", "after"])
@pytest.mark.parametrize("proof", ["original", "v1", "v2", "newer_intent"])
def test_all_three_historical_proofs_fail_closed_before_and_after_one_intent(
    monkeypatch, operation, stage, proof
):
    a = authority()
    c = Client(operation)
    calls = []
    counts = {"original": 0, "v1": 0, "v2": 0}

    def check(name):

        def f(*_):
            counts[name] += 1
            if proof == "newer_intent" and name == "v2" and counts[name] == (1 if stage == "before" else 2):
                own = next(rows[0] for rows in c.rows.values() if rows)
                c.rows["recover-rc6-wall4.yml"].append({**own, "id":int(RUN)+1, "status":"queued", "path":release.WORKFLOWS["recover"], "display_title":"Pi recovery / wall-4inch / "+a.binding.request["manifest_id"], "updated_at":"2026-10-22T17:00:00Z"})
            if name == proof and counts[name] == (1 if stage == "before" else 2):
                raise BindingError("HISTORICAL_PROOF_WITHDRAWN")

        return f

    monkeypatch.setattr(release.component, "original_failure", check("original"))
    monkeypatch.setattr(release, "previous_failure", check("v1"))
    monkeypatch.setattr(release, "latest_failure", check("v2"))
    monkeypatch.setattr(release, "verified_artifact", lambda *_: b"SYNTHETIC")
    monkeypatch.setattr(
        release,
        "inspect_artifact",
        lambda *_: SimpleNamespace(
            wheel_name="djconnect_pi-4.0.0rc6-py3-none-any.whl", wheel_sha256="f" * 64
        ),
    )
    monkeypatch.setattr(release.authority_module, "current", lambda *_: None)
    monkeypatch.setattr(release, "download_recovery", lambda *_: {})
    monkeypatch.setattr(release, "recovery_record", lambda *_: OBS)

    class Channel:
        sent = False
        recovery_boot_id = BOOT

        def __init__(self, *_, **__):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def intent(self, payload, **_):
            self.sent = True
            calls.append(deepcopy(payload))
            if operation == "recover":
                return {
                    "result": "RECOVERED_PENDING_SMOKE",
                    "configuration_preserved_by_installer": True,
                    "watchdog_restored": True,
                    "verified_packaged_files": 80,
                    "original_deployment_workflow_run": release.component.ORIGINAL_RUN,
                    "services": SERVICES,
                    "recovery_observation": OBS,
                }
            return {
                "result": "SMOKE_PASS",
                "installed_source": release.component.SOURCE,
                "installed_version": a.binding.version,
                "installed_device_profile": release.component.PROFILE,
                "paired": True,
                "verified_packaged_files": 80,
                "api_reachable": True,
                "client_active": True,
                "api_active": True,
                "services": SERVICES,
                "recovery_observation": OBS,
            }

    monkeypatch.setattr(release, "Channel", Channel)
    with pytest.raises(PhaseFailure) as failure:
        release.execute(
            c, a, operation, RUN, "49999999999" if operation == "smoke" else ""
        )
    assert len(calls) == (0 if stage == "before" else 1)
    assert failure.value.record["intent_dispatched"] is (stage == "after")
    assert failure.value.record["remote_may_still_be_running"] is (
        stage == "after" and operation == "recover"
    )
    assert counts["v2" if proof == "newer_intent" else proof] == (1 if stage == "before" else 2)
    assert wire.exact_json(
        failure.value.record["previous_recovery_attempt"], latest_descriptor()
    )

@pytest.mark.parametrize('suffix',['','&extra=1','/../contents/file','\n'])
def test_http_admits_only_the_fixed_latest_v2_ancestor_route(suffix):
    from test_pi_instance_authority import Response

    from Tools.pi_instance_authority import GitHubRead
    calls=[]
    class Opener:
        def open(self,request,timeout):
            calls.append(request.full_url);return Response(b'{}')
    reader=GitHubRead('synthetic-not-a-credential');reader.opener=Opener()
    path='repos/pcvantol/djconnect-pi/compare/2e7479d0d15aa11ad3bff4c8103c18dbb1f2c32a...'+'a'*40+'?per_page=1&page=2'+suffix
    if suffix:
        with pytest.raises(BindingError,match='GITHUB_PATH_INVALID'):reader.get(path)
        assert not calls
    else:
        assert reader.get(path)==b'{}'
        assert calls==['https://api.github.com/'+path]


def test_both_actual_workflows_use_only_closed_v3_pair_and_smoke():
    root=Path(wire.__file__).parent.parent
    for name in ('recover-rc6-wall4.yml','smoke-rc6-wall4-recovery.yml'):
        text=(root/'.github/workflows'/name).read_text()
        assert all(key in text for key in wire.CONFIG)
        assert 'RECOVERY_V2_' not in text
        assert 'smoke_contract: '+wire.SMOKE in text
        assert 'cancel-in-progress: false' in text
