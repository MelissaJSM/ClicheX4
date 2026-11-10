"""이미 실제 열람한 최종 시트의 관찰·한계를 독립 검사에 결합한다."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
DASH = ROOT / "work/sprite_style_unification_20261107/nana_audit/ultimate_dash_repaint"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


report = json.loads((OUT / "report.json").read_text("utf-8"))
assert report["passed"]
assert report["candidate_sha256"] == "d1d25c1677f4b108e6cca373ca8cdc7957f1c4e51a4d8480b37a8f06479607d0"
assert sha(ROOT / report["candidate"]) == report["candidate_sha256"]
paths = [
    DASH / "nova_head_registered_v1/comparison.png",
    DASH / "nova_head_registered_v1/mask_review.png",
    *[DASH / f"packed_dash_candidate_v1/readback_{i}.png" for i in range(1, 5)],
    DASH / "packed_dash_candidate_v1/nova_readback.png",
]
report["visual_review_pending"] = False
report["visual_review"] = {
    "reviewer": "/root/hud_checkpoint",
    "method": "view_image로 최종 재추출 및 의미 마스크 비교 시트 7장을 직접 열람",
    "images": [{"path": str(p.relative_to(ROOT)), "sha256": sha(p)} for p in paths],
    "observations": [
        "71/75의 두 신발이 두 의상과 사격 표시에서 구분되며, 새 팔·하체의 뚜렷한 단절은 발견하지 못했다.",
        "맨팔 어깨·팔꿈치·손목 연결이 유지된다. 71 목뒤와 94 어깨에서 이전 재킷의 밝은 소매띠가 남는 새 결함은 이 시트에서 발견하지 못했다.",
        "93/94는 사격 짝으로 오인하지 않고 연결 자세로 검토했다.",
        "노바 머리의 명암·머릿결이 새 대시와 이어지고, 보호된 원손·하체 및 219 효과는 그대로다. 218/220의 효과색은 정적 팔레트 미리보기다.",
    ],
    "limits": [
        "7,296 조합은 수치 대조이며 그 모든 조합을 눈으로 본 것은 아니다.",
        "이 기록은 7개 정적 시트의 미술 검토다. 연속 애니메이션·실제 게임의 동작이나 동적 효과색을 확인한 기록이 아니다.",
        "원 MIPS 디코더/GPU 검사는 별도로 연결한 제작자 실행 증거다. 독립 감사자가 재실행했다고 주장하지 않는다.",
        "루트 최종 미술 수용 및 사용자 실기 수용은 이 보고서로 대신하지 않는다.",
    ],
}
(OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", "utf-8")
print(json.dumps({"passed": True, "report_sha256": sha(OUT / "report.json"), "viewed_images": len(paths)}))
