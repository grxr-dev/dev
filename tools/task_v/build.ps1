# The pinned runner must already have the Task P/Q/U facilities installed.
$ErrorActionPreference = 'Stop'
python tools/task_v/install.py
if ($LASTEXITCODE -ne 0) { throw 'Task V installation failed' }
$env:PATH = "$PWD/local/toolchain/w64devkit/bin;$env:PATH"
cmake --build build/task-o-sdl-runner --target nds_runner --parallel 4
if ($LASTEXITCODE -ne 0) { throw 'Task V build failed' }
