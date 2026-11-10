$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectRoot
try {
    if (@(Get-Process RXC1 -ErrorAction SilentlyContinue).Count -eq 0) {
        Start-Process -FilePath 'C:/Program Files (x86)/Steam/steam.exe' -ArgumentList '-applaunch 743890' -WindowStyle Hidden
    }
    & python scripts/steam_title_position.py --wait 30
    if ($LASTEXITCODE -ne 0) { throw '게임 기동 또는 타이틀 표시 좌표 확인에 실패했습니다.' }
    & python scripts/steam_portrait_routes.py
    if ($LASTEXITCODE -ne 0) { throw '일러스트의 언어별 자원 연결을 확인하지 못했습니다.' }
    & python scripts/steam_dialogue_outfits.py
    if ($LASTEXITCODE -ne 0) { throw '대화 일러스트의 장비별 선택을 확인하지 못했습니다.' }
    & python scripts/steam_ultimate_player.py
    if ($LASTEXITCODE -ne 0) { throw '얼티밋 스프라이트의 획득 전후 표시를 확인하지 못했습니다.' }
    & python scripts/steam_menu_outfits.py
    if ($LASTEXITCODE -ne 0) { throw '일시정지 및 저장 화면의 의상 선택을 확인하지 못했습니다.' }
    & python scripts/steam_audio_runtime.py
    if ($LASTEXITCODE -ne 0) { throw '음향 자원 및 보스 개전 음성 연결을 확인하지 못했습니다.' }
    & python scripts/steam_effect_colors.py
    if ($LASTEXITCODE -ne 0) { throw '사망 구체의 캐릭터 색상 연결을 확인하지 못했습니다.' }
} finally {
    Pop-Location
}
