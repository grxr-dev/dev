$ErrorActionPreference = 'Stop'
python tools/task_ai/install.py
if ($LASTEXITCODE -ne 0) { throw 'Task AI installation failed' }
$env:PATH = "$PWD/local/toolchain/w64devkit/bin;$env:PATH"
cmake --build build/task-o-sdl-runner --target nds_runner --parallel 4
if ($LASTEXITCODE -ne 0) { throw 'Task AI build failed' }
