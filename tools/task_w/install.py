"""Install Task W owned headers via the proven V ROM-view installation."""
from pathlib import Path
import subprocess
r=Path(__file__).resolve().parents[2]
subprocess.run(['python',str(r/'tools/task_v/install.py')],cwd=r,check=True)
