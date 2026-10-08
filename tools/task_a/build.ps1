param(
    [string]$Rom,
    [string]$Framework,
    [string]$Ui,
    [string]$Toolchain
)

$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
if (!$Rom) { $Rom = Join-Path $taskRoot '../Brain Age - Train Your Brain in Minutes a Day! (USA) (Rev 1).nds' }
if (!$Framework) { $Framework = Join-Path $taskRoot 'local/ndsrecomp' }
if (!$Ui) { $Ui = Join-Path $taskRoot 'local/recomp-ui' }
if (!$Toolchain) { $Toolchain = Join-Path $taskRoot 'local/toolchain/w64devkit/bin' }
$Framework = (Resolve-Path $Framework).Path
$Ui = (Resolve-Path $Ui).Path
$Toolchain = (Resolve-Path $Toolchain).Path
$taskPin = '3a57236bb23d25dcb4caad7d58d733311062ff5e'
if ((git -C $Framework rev-parse HEAD) -ne $taskPin) { throw 'Unexpected ndsrecomp baseline' }
if ((git -C $Ui rev-parse HEAD) -ne '7e884a227accea91ddb378671bd49aaeeea13371') { throw 'Unexpected recomp-ui baseline' }
if ((Get-FileHash -LiteralPath $Rom -Algorithm SHA1).Hash.ToLowerInvariant() -ne 'b8a105bacc3234dede8d4465df0869f2b922a0e2') { throw 'Unexpected ROM SHA-1' }
$env:PATH = "$Toolchain;$env:PATH"
$taskPatchPath = Join-Path $PSScriptRoot 'ndsrecomp-flash-trace.patch'
$taskSavedErrorAction = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
git -C $Framework apply --reverse --check $taskPatchPath 2>$null
$taskReverseExit = $LASTEXITCODE
$ErrorActionPreference = $taskSavedErrorAction
if ($taskReverseExit -ne 0) {
    git -C $Framework apply --check $taskPatchPath
    if ($LASTEXITCODE -ne 0) { throw 'Instrumentation patch conflicts with framework changes' }
    git -C $Framework apply $taskPatchPath
    if ($LASTEXITCODE -ne 0) { throw 'Instrumentation patch failed' }
}
Copy-Item (Join-Path $PSScriptRoot 'brainage_flash_trace.h') (Join-Path $Framework 'runner/src/brainage_flash_trace.h')
Push-Location $taskRoot
try {
    New-Item -ItemType Directory -Force local/task-a,generated/public,generated/brainage | Out-Null
    cmake -S "$Framework/recompiler" -B build/recompiler-gcc -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
    if ($LASTEXITCODE -ne 0) { throw 'Recompiler configure failed' }
    cmake --build build/recompiler-gcc --target nds_recompile --parallel 2
    if ($LASTEXITCODE -ne 0) { throw 'Recompiler build failed' }
    python tools/prepare_brainage.py --rom $Rom --out local/inputs
    if ($LASTEXITCODE -ne 0) { throw 'ROM preparation failed' }
    $taskRecompiler = Join-Path $taskRoot 'build/recompiler-gcc/nds_recompile.exe'
    foreach ($taskCpu in @('9','7')) {
        $taskShards = if ($taskCpu -eq '9') { 4 } else { 2 }
        & $taskRecompiler --config "config/brainage_arm$taskCpu.toml" --bin "local/inputs/arm$taskCpu.bin" --out generated/brainage --bank "brainage_arm${taskCpu}_main" --shards $taskShards *> "local/task-a/emit-arm$taskCpu.log"
        if ($LASTEXITCODE -ne 0) { throw 'Title bank emission failed' }
    }
    foreach ($taskBank in @('freebios_arm9','arm9_bios','freebios_arm7','arm7_bios')) {
        $taskCpu = if ($taskBank -match 'arm9') { '9' } else { '7' }
        & $taskRecompiler --config "$Framework/bios/freebios$taskCpu.toml" --bin "$Framework/third_party/freebios/drastic_bios_arm$taskCpu.bin" --out generated/public --bank $taskBank *> "local/task-a/emit-$taskBank.log"
        if ($LASTEXITCODE -ne 0) { throw 'Public BIOS bank emission failed' }
    }
    cmake -S "$Framework/runner" -B build/task-a-runner -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DNDS_SDL_BACKEND=NONE -DNDS_ENABLE_COMPUTE_RENDERER=OFF -DNDS_BOOTSTRAP_FIRMWARE=ON "-DNDS_RECOMP_UI_ROOT=$Ui" "-DNDS_GENERATED_DIR=$taskRoot/generated/public" "-DNDS_TITLE_BANK_DIR=$taskRoot/generated/brainage" -DNDS_TITLE_ROM_SHA1=b8a105bacc3234dede8d4465df0869f2b922a0e2
    if ($LASTEXITCODE -ne 0) { throw 'Runner configure failed' }
    cmake --build build/task-a-runner --target nds_runner cart_backup_test --parallel 2
    if ($LASTEXITCODE -ne 0) { throw 'Runner build failed' }
    & ./build/task-a-runner/cart_backup_test.exe
    if ($LASTEXITCODE -ne 0) { throw 'Existing Flash semantics test failed' }
    g++ -std=c++20 -O2 -Itools/task_a "-I$Framework/runner/src" "-I$Framework/recompiler/armv4t" "-I$Framework/external/arm-recomp-core/common" tools/task_a/origin_test.cpp "$Framework/runner/src/cart_backup.cpp" -o build/task-a-origin-test.exe
    if ($LASTEXITCODE -ne 0) { throw 'Origin test build failed' }
    & ./build/task-a-origin-test.exe
    if ($LASTEXITCODE -ne 0) { throw 'Origin test failed' }
} finally {
    Pop-Location
}
