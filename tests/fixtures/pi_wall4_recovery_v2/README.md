# Original failed V2 recovery fixture

inconclusive_receipt.json is the exact original public/redacted artifact member
from run39775941080, artifact12423814908,3058 bytes, SHA256
 eb57af222e6be4f9d7e9e40be488f3f395ae2e6e94a583e6d4ea7e9d839c6b4d.

The five code/ files are exact git bytes at the actual qualified consumer Final
2e7479d0d15aa11ad3bff4c8103c18dbb1f2c32a. Their fixed SHA256 pins are in
Tools/pi_wall4_latest_failure.py. They are historical evidence, not code to run
against a device. Tests use synthetic HTTP envelopes and intercept qualification;
they do not cancel, retry, create/clear a claim, or execute an installer.

Keep these bytes and the nested original V1 failure unchanged. This V2 fixture
has schema/kind/helper/observer fields; absent inputs or local diagnostic fields
must not be manufactured. Historical uncertainty remains historical uncertainty.

latest_descriptor_draft_rule.json is an extracted, normalized JSON rule from
Core's selected V3 draft, independently compared with the corrected PR1290 head
fe3a235b8b811d893d3362b20d33245084da245d. It is only a test fixture for the
historical descriptor's shape. It is not a full normative file, released
producer, adopted Tools/pi_contract pin or dispatch permission. The normative
contract/request/manifest remain separately gated. Original V2 raw/code files
above are unchanged.
