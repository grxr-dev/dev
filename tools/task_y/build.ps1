$ErrorActionPreference = 'Stop'
python tools/task_y/install.py --codex-executable 'C:/Users/rustg/AppData/Local/OpenAI/Codex/bin/9691020b546a15b2/codex.exe'
if ($LASTEXITCODE -ne 0) { throw 'Task Y installation failed' }
$env:PATH = "$PWD/local/toolchain/w64devkit/bin;$env:PATH"
cmake --build build/task-o-sdl-runner --target nds_runner --parallel 4
if ($LASTEXITCODE -ne 0) { throw 'Task Y build failed' }
