"""Exactly seq135, original failed automatic evidence retained, never a Send."""
import importlib.util
from pathlib import Path
KERNEL=Path(__file__).resolve().parent.parent/'inbox_receipt_132/receipt.py'
spec=importlib.util.spec_from_file_location('pinned_receipt135_kernel',KERNEL)
receipt=importlib.util.module_from_spec(spec);spec.loader.exec_module(receipt)
PINS={
 'TARGET':'brainage-phase0-compiler-pilot-20261101-06:78c8de26d16dc4b6f39ffcb22d15cf4f7a9dd4160441c6747f5b3ccc300d1886',
 'TEXT_SHA':'edaa26acdceb03efef5793fb4e9893638c19b49aeb8625c3b4682127631f344a',
 'UUID':'92e1f981-d2e4-43f9-92f0-0abb7b72c828',
 'FINGERPRINT':'973550d3ec95d98159f4647882964a30feaddc89d3ed9a30aac66a128de11034',
 'INCIDENT_SHA':'ad417942c62fc354bf1f55944015fee970835aac4730af4ec9a78ee90b4538b7',
 'COMMENT':6565939655,'AUTHORITY_SHA':'60112ec25f47cfe8afd5dcd8fed26b4b23b1df4cb5eb01074f226c1b41c48247',
 'IDENTITY':'eb789679d470bea0061e4c2fdbbbeb11aea329bb8d2262b49fa768e22b784a3e',
 'SEAL':'975fe745ad5aa2366cc391b0f728ec4bda2c29753773f69d45a69c8711d59d2c',
 'SEQUENCE':135,'EXPECTED_LENGTH':863,'OBSERVED_LENGTH':875,'MISMATCH_INDEX':863,'OBSERVATIONS':336,
}
for name,value in PINS.items():setattr(receipt,name,value)
