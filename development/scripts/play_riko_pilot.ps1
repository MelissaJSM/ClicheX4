# 현재 검증된 Riko 대기 시험판을 보여 주거나 새로 실행한다. 원본 게임 쓰기 없음.
$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$buildRecord = Get-Content -LiteralPath (Join-Path $projectRoot 'projects/ver_buki_riko/current_build.json') -Encoding UTF8 | ConvertFrom-Json
Push-Location -LiteralPath $projectRoot
try {
    $sessionFile = Join-Path $projectRoot (Join-Path $buildRecord.session 'session.local.json')
    $existing = $null
    if (Test-Path -LiteralPath $sessionFile) {
        $sessionRecord = Get-Content -LiteralPath $sessionFile -Encoding UTF8 | ConvertFrom-Json
        $existing = Get-Process -Id $sessionRecord.pid -ErrorAction SilentlyContinue
        if ($existing -and ($existing.Path -ne $sessionRecord.executable -or $sessionRecord.bin_sha256 -ne $buildRecord.bin_sha256)) {
            $existing = $null
        }
    }
    if ($existing) {
        & python scripts/emulator_session.py capture --session $buildRecord.session
    } else {
        & python scripts/emulator_session.py launch --cue $buildRecord.cue
    }
    if ($LASTEXITCODE -ne 0) { throw 'Riko 시험판 실행/포커스 확인 실패. 위 오류를 확인하세요.' }
} finally {
    Pop-Location
}
