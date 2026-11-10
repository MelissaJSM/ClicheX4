# PS1 설치

## 필요한 원본

- 미국판 Mega Man X4, 디스크 식별자 `SLUS_005.61`
- 원시 BIN, 592,217,136바이트, 2352바이트 섹터
- SHA-256: `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b`

파일명만 같은 다른 리비전·일본판·ISO·이미 패치한 BIN은 지원하지 않습니다. 패처는 해시가 다르면 중단합니다. 원본 게임과 BIOS는 제공하지 않습니다.

## 사용 순서

1. Releases의 `ClicheX4_PS1_20261110.zip`을 새 폴더에 모두 풉니다.
2. `ClicheX4_PS1.exe`를 실행합니다. Windows용이며 Python 설치는 필요 없습니다.
3. 모드와 **원본 BIN**을 선택하고, 출력 상위 폴더를 지정합니다.
4. 검사 후 새 BIN/CUE 만들기를 누릅니다. 상위 폴더 아래 `shibuki_riko` 또는 `rin_nana`라는 새 폴더가 만들어집니다. 같은 이름의 폴더가 있으면 덮어쓰지 않고 중단합니다.
5. **DuckStation** 또는 **ePSXe**에서 새 폴더의 **CUE**를 엽니다. 에뮬레이터와 BIOS는 직접 준비합니다. 업데이트 직후에는 새로 부팅한 뒤 게임 내 메모리카드로 불러오세요. 오래된 세이브스테이트는 이전 RAM/VRAM 그림을 포함할 수 있습니다.

두 모드는 원본에서 각각 만들며 서로의 수정 BIN에 겹쳐 패치하지 않습니다. 원본과 기존 출력은 유지됩니다. 패처는 메모리카드나 세이브스테이트에 접근하지 않습니다. ePSXe에서 진행한 사용자 검증을 다른 모든 에뮬레이터·실기 호환성 검증으로 확대하지 않습니다.

## 확인할 출력 해시

| 파일 | SHA-256 |
|---|---|
| `shibuki_riko.bin` | `5bd81ec1cc7cff4b79a828e7931f14f1c7d5ac01a122da81b170751c960b5db7` |
| `rin_nana.bin` | `03bb660be698dd7dd1b1b3fbf6612bcd1ed111cff47b5eda7c186ded3f343f3a` |

## 명령줄

```powershell
ClicheX4_PS1.exe --source "원본.bin" --patch ver_buki_riko.cxp --output "새폴더" --report result.json
ClicheX4_PS1.exe --source "원본.bin" --patch ver_rin_nana.cxp --verify --report verify.json
```

`--verify`는 결과 해시만 검사하며 BIN을 쓰지 않습니다. `.cxp`는 이 패처의 XOR 차이 형식이며 IPS/BPS가 아닙니다. 검증한 원본의 단일 트랙 구성에만 맞는 CUE를 생성합니다.

스텔라이브 관련 콘텐츠의 권리는 스텔라이브 및 각 권리자에게 있으며 요청 시 삭제될 수 있습니다. 원작 게임의 저작권과 소유권은 CAPCOM에 있습니다. [전체 고지](../NOTICE.md)
