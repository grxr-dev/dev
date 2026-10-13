# AW4 ROM-free reconciliation

This directory contains a diagnostic-only expected-state reconciler and a separate
synthetic runtime test executable. It does not install an AX activation path.
Brain Age must not be launched by these helpers.

Run `python tools/task_aw4/check.py --output local/task-aw4/fresh-certification`.
Use a new evidence directory; existing evidence is never overwritten. The helper
builds a separate executable from actual provider-owning translation units and
ROM-free dependencies. It never links generated banks or invokes the interpreter.
Synthetic fixture setters exist only in that executable. Required local dependencies
are the pinned installed AW3 hooks and existing w64devkit/support/libslirp build.

`reconcile.h` protects immutable cells separately from exact expected evolving
cells. `controller.h` connects actual passive samples to that plan and terminal
disposal. A synthetic identity profile is compile-gated, not a runtime selector.
Normal builds still require the original AU manifest. No live AX path is installed.

See `docs/BrainAge_TaskAW4_FullStateControllerReconciliation.md` for the field model,
test scope and the distinction between ROM-free certification and live eligibility.
