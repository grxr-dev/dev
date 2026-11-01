"""Prepared exact seq134 owner receipt. Importing/validating NEVER writes a queue.

Reuses the reviewed atomic receipt kernel, with independent immutable pins.
No CLI applying this receipt is provided: release is held pending verifier proof
and a managed idle boundary. Never run reconcile against an online disk copy.
"""
import importlib.util
from pathlib import Path

KERNEL = Path(__file__).resolve().parent.parent / 'inbox_receipt_132/receipt.py'
spec = importlib.util.spec_from_file_location('pinned_receipt134_kernel', KERNEL)
receipt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(receipt)
PINS = {
    'TARGET': 'brainage-phase0-metadata-init-20261101-05:3cdc0713b5b3f614a012c9676a7ba947d4d9375d35a9780ec58a94d906107a16',
    'TEXT_SHA': '74b79d3c88d0b31883ebf253eb58c26c3bbe7fc0a9925963f210163e1f89ac6f',
    'UUID': 'acab8cd4-6871-49cd-b92a-93961f10a574',
    'FINGERPRINT': 'c2862161d3bf68dc2f226e9cf33f55b4b35900c1c5b49aef0a9cff72c7492dea',
    'INCIDENT_SHA': '5afae75146153c079e04e1236f0ab891c14747cc38dce6be23fb44a9130cd367',
    'COMMENT': 6565241702,
    # Decode GitHub's JSON as UTF-8 before checking this body hash.
    'AUTHORITY_SHA': '2fbecc9913cd3caa3e2878e9477d70ad92cd2dc06c76f7796d8afcfc89abfd16',
    'IDENTITY': 'eb789679d470bea0061e4c2fdbbbeb11aea329bb8d2262b49fa768e22b784a3e',
    'SEAL': '975fe745ad5aa2366cc391b0f728ec4bda2c29753773f69d45a69c8711d59d2c',
    'SEQUENCE': 134, 'EXPECTED_LENGTH': 1243, 'OBSERVED_LENGTH': 1255,
    'MISMATCH_INDEX': 1243, 'OBSERVATIONS': 341,
}
for name, value in PINS.items():
    setattr(receipt, name, value)
