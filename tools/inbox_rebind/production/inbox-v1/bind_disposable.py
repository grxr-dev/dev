"""Local test-only binding edit, never accepted by inbox/native protocol."""
raise SystemExit('Test-only recipient editing retired. Use production binding.py status/rebind; all deliveries remain HOLD.')
import argparse
from pathlib import Path
import re
PERMANENT='6ac7d7f2-b474-83e9-83c8-1a1cd9ad2b4f'
p=argparse.ArgumentParser();p.add_argument('conversation_id',nargs='?');p.add_argument('--restore',action='store_true');a=p.parse_args()
id=PERMANENT if a.restore else a.conversation_id
if not id or not re.fullmatch(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',id):p.error('provide a disposable conversation UUID or --restore')
for name in ('background.js','chatgpt_content.js'):
    file=Path(__file__).parent/'extension'/name;s=file.read_text(encoding='utf-8-sig')
    s,n=re.subn(r"const BOUND_CONVERSATION_ID='[0-9a-f-]+';",f"const BOUND_CONVERSATION_ID='{id}';",s)
    if n!=1:raise ValueError('binding constant missing; abort')
    file.write_text(s,encoding='utf-8')
print('Local binding set to',id,'; reload temporary extension. No tab is opened or navigated.')
