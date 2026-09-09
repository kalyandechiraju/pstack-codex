# Contributing

1. Read [`docs/PORTING_PLAN.md`](docs/PORTING_PLAN.md) and
   [`docs/COMPATIBILITY.md`](docs/COMPATIBILITY.md).
2. Keep `vendor/cursor-plugins/pstack` immutable unless you are deliberately
   refreshing the recorded upstream pin.
3. Put compatibility changes in
   [`config/compatibility-allowlist.json`](config/compatibility-allowlist.json)
   or the generator, not in generated files.
4. Regenerate and run the complete test suite.
5. Include the upstream diff, generated diff, and verification commands in the
   pull request description.

Small, focused pull requests are easier to compare against upstream and safer
to update when pstack changes.
