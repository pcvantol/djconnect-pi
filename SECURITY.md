# DJConnect Security Policy

## Reporting A Vulnerability

Please report security vulnerabilities privately by email:

```text
security@djconnect.dev
```

Do not open a public GitHub issue for suspected security vulnerabilities, leaked secrets, credentials, private URLs, exploit details or sensitive logs. Private reporting gives the maintainer time to investigate and prepare a fix before details are widely visible.

Useful report details include:

- Affected repository, version, release tag, commit and component.
- A clear description of the issue and expected impact.
- Steps to reproduce or a proof of concept, when safe to share.
- Relevant logs, screenshots, URLs or configuration details with secrets removed.
- Whether tokens, credentials, local network access, audio, diagnostics or user data may be exposed.

Please do not include real Spotify OAuth credentials, Home Assistant tokens, DJConnect bearer tokens, WiFi passwords, private network URLs, raw diagnostics or other secrets in the report. Redacted examples are preferred.

Do not include secrets, private data or proprietary third-party material in AI prompts, agent logs, screenshots, issues or test fixtures.

## What To Expect

The project maintainer will review security reports as soon as practical. DJConnect is a small community project, so response times may vary, but reports sent to `security@djconnect.dev` are the preferred path and will be handled with care.

The maintainer may ask for clarifying details and will coordinate any fix, release or disclosure timing privately before public discussion. When a vulnerability is confirmed, the maintainer will work on an appropriate fix, document user impact where needed and publish release notes once the fix is available.

If a report crosses repository boundaries, email `security@djconnect.dev` and include the affected component names. The report can be routed across the Home Assistant integration, Apple app, ESP32 firmware, website or Raspberry Pi client as needed.

## Supported Versions

Security fixes for the DJConnect Raspberry Pi client are normally targeted at the latest published DJConnect Pi release and the current `main` branch unless otherwise stated by the maintainer.

## Security Scope

In scope for this repository:

- DJConnect Raspberry Pi client code, installer and release assets.
- Local Client API behavior, pairing code handling, bearer-token storage and diagnostics.
- Web portal behavior, service setup and updater/release tooling.
- Documentation that could expose credentials or private artifacts.

Out of scope for this repository:

- Vulnerabilities in Raspberry Pi OS, system packages, Spotify, Home Assistant, GitHub or third-party services themselves.
- Home Assistant integration, Apple app, ESP32 firmware or website issues that belong in a separate DJConnect repository, unless the report crosses repository boundaries.

## Safe Research Guidelines

Please avoid actions that could harm users or services:

- Use your own Home Assistant instance, DJConnect device/client, website test session and Spotify account when testing.
- Do not access, modify or delete data that is not yours.
- Do not attempt denial-of-service attacks.
- Do not publicly disclose a vulnerability before a fix or mitigation is available.
- Do not exfiltrate tokens, passwords, audio, local-network data, private URLs, diagnostics or personal configuration.

Good-faith security research that follows these guidelines is welcome.
