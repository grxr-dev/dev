"""Exactly seq133, reusing the reviewed atomic receipt kernel; never a Send."""
import importlib.util
from pathlib import Path

KERNEL = Path(__file__).resolve().parent.parent / 'inbox_receipt_132/receipt.py'
spec = importlib.util.spec_from_file_location('pinned_receipt133_kernel', KERNEL)
receipt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(receipt)
PINS = {
    'TARGET': 'brainage-phase0-init-census-20261101-04:3abc18cfc75d78fbab4c78db195b84d13338556c29715c931ce6f513e641d4dc',
    'TEXT_SHA': '0fa4ef79e68fd1a069eacc7741a9b3f4697a0ec6a662988ec0f830b506ebc9e0',
    'UUID': '41bfef82-0c00-4014-9f22-11adbf4345f5',
    'FINGERPRINT': '79e3a6d80687c5c6a7a911189d5885d606660c9f2eae0c2b026a7ef4cc40edf7',
    'INCIDENT_SHA': 'b6e89d74d0c3ab2f1cfd110629e899e85d6cf2cb4bc21d1f0b86a058b9ae1906',
    'COMMENT': 6561830626,
    'AUTHORITY_SHA': 'a420e5a9fb9de375299fa8387e5812b477714d80d55590b21c0365552f56ddc4',
    'SEQUENCE': 133, 'EXPECTED_LENGTH': 1287, 'OBSERVED_LENGTH': 1285,
    'MISMATCH_INDEX': 89, 'OBSERVATIONS': 349,
}
for name, value in PINS.items():
    setattr(receipt, name, value)
