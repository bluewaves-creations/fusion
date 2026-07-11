# Fusion installer (Windows) — https://github.com/bluewaves-creations/fusion
# Usage: powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/bluewaves-creations/fusion/main/install.ps1 | iex"
# Env:   FUSION_VERSION, FUSION_PACKAGE_SPEC, FUSION_SKILLS_DIR,
#        FUSION_NO_AGENTS, FUSION_NO_MODIFY_PATH
$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

function Say([string]$m) { Write-Host $m }
function Fail([string]$m) { Write-Error "fusion install: $m"; exit 1 }

# 1 — uv (registry-based PATH handling is uv's own; we never call setx)
$uv = Get-Command uv -ErrorAction SilentlyContinue
if ($uv) { $uvExe = $uv.Source }
else {
    Say "installing uv (Astral's official installer)..."
    if ($env:FUSION_NO_MODIFY_PATH -eq "1") { $env:UV_NO_MODIFY_PATH = "1" }
    try { Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression }
    catch { Fail "could not download or run uv's installer - install uv yourself (https://docs.astral.sh/uv/), then: uv tool install fusion-cli; fusion setup" }
    $uvExe = Join-Path $HOME ".local\bin\uv.exe"
    if (-not (Test-Path $uvExe)) { Fail "uv installed but not found at $uvExe - restart the terminal and re-run, or run by hand: uv tool install fusion-cli; fusion setup" }
}

# 2 — the CLI
$spec = if ($env:FUSION_PACKAGE_SPEC) { $env:FUSION_PACKAGE_SPEC }
        elseif ($env:FUSION_VERSION)  { "fusion-cli==$($env:FUSION_VERSION)" }
        else                          { "fusion-cli" }
Say "installing $spec..."
# --refresh: skip uv's cached PyPI index, so an install minutes after a
# release still lands the release, not the cache's idea of "latest"
& $uvExe tool install --force --refresh $spec
if ($LASTEXITCODE -ne 0) { Fail "uv tool install failed. manual step: uv tool install --force --refresh $spec" }

# 3 — hand off to the brain
$binRaw = & $uvExe tool dir --bin
if ($LASTEXITCODE -ne 0 -or -not $binRaw) { Fail "could not resolve uv's tool bin dir - run by hand: uv tool dir --bin, then <that dir>\fusion.exe setup" }
$bin = "$binRaw".Trim()
$fusion = Join-Path $bin "fusion.exe"
if (-not (Test-Path $fusion)) { Fail "fusion not found in $bin after install - run by hand: uv tool dir --bin, then <that dir>\fusion.exe setup" }
& $fusion setup
exit $LASTEXITCODE
