# Task AT static certificate

Run python -B tools/task_at/check.py from the repository root. This reads the
exact local ROM, retained AS evidence and framework source. It never loads or
calls the guest interpreter, runtime, bus, replay runner or MMIO model.

python -B tools/task_at/analyze.py --export writes only the ROM-free Task AT
JSON report. Markdown explains the reviewed instruction annotations. The helper
is a fixed static certificate, not an instruction interpreter. No guest image
is modified. The certificate recommends AU; it does not implement or run AU.
