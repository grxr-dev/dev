# Run from repository root after the Task R diagnostic installation.
$ErrorActionPreference = 'Stop'
python tools/task_s/install.py
if ($LASTEXITCODE -ne 0) { throw 'Task S installation failed' }
$env:PATH = "$PWD/local/toolchain/w64devkit/bin;$env:PATH"
cmake -S local/ndsrecomp/runner -B build/task-s-runner -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DNDS_SDL_BACKEND=NONE -DNDS_ENABLE_COMPUTE_RENDERER=OFF -DNDS_BOOTSTRAP_FIRMWARE=ON "-DNDS_RECOMP_UI_ROOT=$PWD/local/recomp-ui" "-DNDS_GENERATED_DIR=$PWD/generated/public" "-DNDS_TITLE_BANK_DIR=$PWD/generated/brainage" -DNDS_TITLE_ROM_SHA1=b8a105bacc3234dede8d4465df0869f2b922a0e2
if ($LASTEXITCODE -ne 0) { throw 'Task S configuration failed' }
cmake --build build/task-s-runner --target nds_runner --parallel 4
if ($LASTEXITCODE -ne 0) { throw 'Task S build failed' }
