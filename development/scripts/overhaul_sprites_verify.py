"""최종 자원의 재패킹 동일성과 입력/출력 보호 조건을 검사한다."""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import overhaul_sprites_audit as audit
from scripts.overhaul_sprites_proposal import main as freeze


def reject(name, operation):
    try:
        operation()
    except ValueError as error:
        return {"case": name, "rejected": True, "reason": str(error)}
    raise AssertionError(f"잘못된 입력을 허용함: {name}")


def verify():
    results = []
    for project, prefix in (("ver_buki_riko", "shibuki"), ("ver_rin_nana", "nana")):
        frozen = audit.D / "c03_final_v1" / project
        packed = audit.D / f"{prefix}_preultimate" / "packed_progress"
        manifest = json.loads((frozen / "proposal.json").read_text("utf8"))
        expected = manifest["files"]["PL02_U.ARC"]["after"]
        fresh = audit.sha((packed / "PL02_U.ARC").read_bytes())
        saved = audit.sha((frozen / "PL02_U.ARC").read_bytes())
        if fresh != expected or saved != expected:
            raise AssertionError(f"재패킹 결과 불일치: {project}")
        proof = json.loads((packed / "actual_readback" / "verification.json").read_text("utf8"))
        if proof["after_sha256"] != expected:
            raise AssertionError("최종 검증 증거의 해시 불일치")
        rejections = [
            reject("input_output_collision", lambda: freeze(project, packed, packed)),
            reject("immutable_output_exists", lambda: freeze(project, packed, frozen)),
            reject("outside_sprite_workspace", lambda: freeze(project, packed, ROOT / "forbidden_sprite_output")),
        ]
        with tempfile.TemporaryDirectory(prefix="input_hash_test_", dir=audit.D) as temp:
            bad = Path(temp) / "wrong.bin"
            bad.write_bytes(b"not the supported PS1 image")
            previous = audit.BASES[project]
            try:
                audit.BASES[project] = (str(bad), previous[1])
                rejections.append(reject("unsupported_bin_hash", lambda: audit.load(project)))
            finally:
                audit.BASES[project] = previous
        # Repacking intentionally marks drafts incomplete. Restore the already
        # verified report only after matching both immutable and readback hashes.
        (packed / "packing.json").write_bytes((frozen / "packing.json").read_bytes())
        results.append({"project": project, "sha256": expected,
                        "repack_identical": True, "input_output_guards": rejections,
                        "readback_verification": str((packed / "actual_readback" / "verification.json").relative_to(ROOT))})
    audit.write(audit.D / "c03_final_v1" / "reproducibility.json", results)
    print(json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    verify()
