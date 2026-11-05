# Release checklist

1. Run the protocol and packaging tests; check compilation.
2. Require passing GitHub Actions tests, HACS validation (no ignored checks), and hassfest.
3. Confirm versions in manifest, diagnostics and release tag match.
4. Review the complete diff for credentials, personal data, logs and local configuration.
5. Publish a full GitHub release only after validation passes.
6. Check installation from the repository link on Home Assistant 2026.11+.
7. Test another account/device before claiming wider model compatibility. Never automatically send commands to a household for release validation.
8. Set repository description, topics and enable issues.
9. Submit to hacs/default only with links to successful checks and the full release; make no claim that catalog review has already happened.

A successful cloud readback is not confirmation of the physical heating relay. Require verified HTTPS for login, readings and commands, with no HTTP fallback or redirects. Document the fixed-key AES layer as protocol compatibility only.
