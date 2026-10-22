"""Historical-descriptor compatibility, not an adopted producer or effect route."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

pytest.importorskip("jsonschema", reason="Dedicated locked deployment-tool suite")
from jsonschema import Draft202012Validator

from Tools import pi_wall4_latest_failure as latest
from Tools.pi_instance_contract import BindingError
from Tools.pi_wall4_recovery_authority import exact_json

FIXTURE = Path(__file__).parent / "fixtures/pi_wall4_recovery_v2"
RULE = json.loads((FIXTURE / "latest_descriptor_draft_rule.json").read_text())
RAW = json.loads((FIXTURE / "inconclusive_receipt.json").read_text())


def test_original_nested_descriptor_matches_selected_draft_rule_without_adoption():
    value = latest.latest_descriptor()
    Draft202012Validator(RULE).validate(value)
    assert latest.matches_latest_descriptor(RULE)
    assert exact_json(latest.constant_descriptor(RULE), value)
    assert value["classification"] == RAW["classification"]
    assert value["previous_recovery_attempt"] == RAW["previous_recovery_attempt"]
    assert "evidence_bytes" not in value
    assert not {
        "inputs",
        "action",
        "execution_mode",
        "claim_absent",
        "root_static_diagnostic",
    }.intersection(value)


@pytest.mark.parametrize("key", list(RULE["properties"]))
def test_each_latest_discriminator_cannot_be_omitted_or_optional(key):
    for mutation in ("omit", "optional"):
        rule = deepcopy(RULE)
        if mutation == "omit":
            rule["properties"].pop(key)
        else:
            rule["required"].remove(key)
        with pytest.raises(BindingError):
            latest.constant_descriptor(rule)


@pytest.mark.parametrize(
    "key", list(RULE["properties"]["previous_recovery_attempt"]["properties"])
)
def test_nested_original_v1_discriminators_remain_closed(key):
    rule = deepcopy(RULE)
    rule["properties"]["previous_recovery_attempt"]["required"].remove(key)
    with pytest.raises(BindingError):
        latest.constant_descriptor(rule)


@pytest.mark.parametrize(
    "field",
    [
        "intent_dispatched",
        "remote_may_still_be_running",
        "run_attempt",
        "schema_version",
    ],
)
def test_boolean_numeric_substitution_never_matches_historical_facts(field):
    rule = deepcopy(RULE)
    old = rule["properties"][field]["const"]
    rule["properties"][field]["const"] = 1 if type(old) is bool else True
    assert not latest.matches_latest_descriptor(rule)


@pytest.mark.parametrize("path", [[], ["previous_recovery_attempt"]])
@pytest.mark.parametrize(
    "key,value",
    [
        ("additionalProperties", True),
        ("type", "array"),
        ("required", []),
        ("properties", []),
        ("patternProperties", {}),
    ],
)
def test_nonclosed_object_rules_fail_before_any_compatibility_result(path, key, value):
    rule = deepcopy(RULE)
    target = rule
    for name in path:
        target = target["properties"][name]
    target[key] = value
    with pytest.raises(BindingError):
        latest.constant_descriptor(rule)


@pytest.mark.parametrize("literal", [None, 1.5, {}, [], b"value", "x" * 4097])
def test_only_bounded_primitive_historical_constants_are_supported(literal):
    rule = deepcopy(RULE)
    rule["properties"]["result"] = {"const": literal}
    with pytest.raises(BindingError):
        latest.constant_descriptor(rule)


def test_root_must_be_closed_object_not_a_literal():
    with pytest.raises(BindingError):
        latest.constant_descriptor({"const": "not-object"})


def test_duplicate_required_and_references_fail_closed():
    rule = deepcopy(RULE)
    rule["required"].append(rule["required"][0])
    with pytest.raises(BindingError):
        latest.constant_descriptor(rule)
    rule = deepcopy(RULE)
    rule["properties"]["result"] = {"$ref": "https://fixture.invalid/authority"}
    with pytest.raises(BindingError):
        latest.constant_descriptor(rule)


def test_recursion_and_total_node_budget_are_bounded():
    def obj(properties):
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": properties,
            "required": list(properties),
        }

    node = {"const": "value"}
    for _ in range(9):
        node = obj({"nested": node})
    with pytest.raises(BindingError):
        latest.constant_descriptor(node)
    node = obj(
        {str(i): obj({str(j): {"const": True} for j in range(64)}) for i in range(5)}
    )
    with pytest.raises(BindingError):
        latest.constant_descriptor(node)


def test_descriptor_mutation_never_changes_original_nested_values():
    one = latest.latest_descriptor()
    one["previous_recovery_attempt"]["run_attempt"] = True
    assert (
        type(latest.latest_descriptor()["previous_recovery_attempt"]["run_attempt"])
        is int
    )
