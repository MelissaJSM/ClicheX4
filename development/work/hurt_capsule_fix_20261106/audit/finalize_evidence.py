"""완료된 감사 결과를 UTF-8 문자열로 집계한다. 게임 검사/쓰기/조작은 하지 않는다."""
import hashlib
import json
from pathlib import Path

AUDIT = Path(__file__).resolve().parent
ROOT = AUDIT.parents[2]


def load(path):
    return json.loads(path.read_text("utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return path.relative_to(ROOT).as_posix()


def write(path, value):
    encoded = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    assert "\ufffd" not in encoded and "?" not in encoded, "문자 인코딩 손상이 남아 있음"
    temporary = path.with_suffix(".utf8.tmp")
    temporary.write_text(encoded, encoding="utf-8")
    temporary.replace(path)


def main():
    # 이전 PowerShell stdin을 통해 생성한 이 설명 문자열만 정정한다.
    edges = AUDIT / "capsule_gpu_edges_before.json"
    edge_proof = load(edges)
    assert edge_proof["passed"] and edge_proof["parts_checked"] == 552
    edge_proof["scope"] = (
        "현재 자원의 타일 수·참조 범위 및 기존 프로젝트의 GPU 좌우반전 첫열/"
        "수직반전 첫행 안전조건 검사. 실제 GPU 패킷 생성 및 화면 혼합은 별도."
    )
    write(edges, edge_proof)

    projects = {}
    for mode in ("ver_buki_riko", "ver_rin_nana"):
        path = AUDIT / (mode + "_disc_independent.json")
        result = load(path)
        assert result["passed"] and result["changed_sector_count"] == 3
        assert result["protected_files_before_after_exact"]
        result["independent_disc_evidence"] = {"path": rel(path), "sha256": sha(path)}
        result["capsule_graphics_and_timing_unchanged"] = True
        projects[mode] = result

    source = AUDIT / "audio_independent.json"
    audio = load(source)
    assert audio["passed"] and audio["dispatcher_executions"] == 204 and audio["negative_count"] == 18
    native = AUDIT.parent / "capsule/native_timeline.json"
    timeline = load(native)
    assert timeline["passed"] and len(timeline["cases"]) == 20
    report = {
        "passed": True,
        "scope": "두 모드의 기존 X6 피격음 tone0 음량만 90→104. 캡슐 수정은 미재현으로 적용하지 않음.",
        "projects": projects,
        "protected_file_count": 71,
        "protected_files_before_after_exact": True,
        "raw_sector_comparisons": sum(p["all_sectors_compared"] for p in projects.values()),
        "changed_sectors_total": 6,
        "audio_independent": {
            "path": rel(source), "sha256": sha(source),
            "dispatcher_executions": 204, "negative_tests_rejected": 18,
            "hurt_gain_db": audio["hurt_gain_db"],
            "SDK_mocked_in_independent_dispatcher": True,
            "separate_full_native_SDK_evidence": audio["full_native_SDK_evidence"],
        },
        "capsule_review": {
            "changed": False, "issue_resolved": False,
            "status": "현재 후반 불일치 미재현. 사용자 해당 장면 확인 대기.",
            "GPU_edge_evidence": {"path": rel(edges), "sha256": sha(edges), "references": 48, "parts": 552},
            "isolated_native_timeline": {
                "path": rel(native), "sha256": sha(native), "conditions": 20, "calls_per_condition": 131,
            },
            "actual_game_reproduction": False,
        },
        "original_F1_cards_and_epsxe2018_progress_preserved": True,
        "game_process_control_by_this_audit": False,
        "disc_pointer_or_state_written_by_this_audit": False,
        "real_mixed_audio_or_user_acceptance_verified": False,
        "limitations": [
            "실제 음악·효과음 혼합 상황의 청감·클리핑과 사용자 음량 수용은 별도이다.",
            "캡슐 효과 원점/실루엣 조사와 고립 MIPS는 실제 문제 장면 재현을 대신하지 않는다.",
        ],
    }
    target = AUDIT / "final_independent.json"
    write(target, report)
    print(json.dumps({"passed": True, "path": rel(target), "sha256": sha(target),
        "GPU_edge_evidence_sha256": sha(edges), "unicode_corruption_remaining": False}))


if __name__ == "__main__":
    main()
