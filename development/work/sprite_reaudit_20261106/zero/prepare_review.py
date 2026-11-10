"""최신 Zero 도트를 읽기 전용 복원하여 비교시트만 새 감사 폴더에 만든다."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from scripts.export_zero_consistency import sheets
from scripts.overhaul_sprites_audit import render, rgba
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition
from scripts.ultimate_costume_swap_ui import ui_canvas
from scripts.verify_shibuki_save_icon import rgba as word_rgba
from scripts.export_sprite_consistency_ui import canvas, sheet

SOURCES = {
    "riko": ("ver_buki_riko", "shibuki_riko", "8c1a2fa5b3f985be9945717d3d88776f2f4534030c42818843ec8093a3ce1a81"),
    "rin": ("ver_rin_nana", "rin_nana", "dcdf175eb93014da90d1bfb429774b48533e1c156e289a3ac49f969ea7a0f9c7"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path):
    return json.loads(path.read_text("utf-8"))


def main():
    results = {}
    for char, (mode, stem, expected) in SOURCES.items():
        source = ROOT / "out" / mode / "hurt_capsule_fix_20261106_v1" / (stem + ".bin")
        with source.open("rb") as f:
            digest = hashlib.sha256()
            for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
                digest.update(block)
            assert digest.hexdigest() == expected
        assets, _ = read_disc(source, ("PL01_U.ARC", "ST0E_U1.ARC", "COL0E_U1.ARC", "MOJIPAT.ARC", "LOAD_U.ARC"))
        arc = assets["PL01_U.ARC"]
        baseline = ROOT / "out/sprite_consistency_20261105" / char
        manifest = load(baseline / "manifest.json")
        revised_path = ROOT / "out/sprite_consistency_20261105/revised" / char / "mapping.json"
        revised = load(revised_path)["frames"] if revised_path.exists() else {}
        bound = (ROOT / "work/sprite_consistency_20261105/zero/riko/wall_fix/prepared_v1/PL01_U.ARC"
                 if char == "riko" else ROOT / "work/sprite_consistency_20261105/zero/rin/PL01_U.ARC").read_bytes()
        for kind in (2, 3, 9, 0x10206):
            assert entry(arc, kind) == entry(bound, kind), (char, kind)
        folder = OUT / char
        folder.mkdir(parents=True, exist_ok=True)
        imgs = {v: {} for v in ("normal", "black")}
        for variant in imgs:
            (folder / variant / "sheets").mkdir(parents=True, exist_ok=True)
        palettes = {v: list(struct.unpack("<64H", (baseline / v / "preview_palettes.bin").read_bytes())) for v in imgs}
        pal = entry(arc, 9)
        assert palettes["normal"][:16] == list(struct.unpack_from("<16H", pal))
        assert palettes["black"][:16] == list(struct.unpack_from("<16H", pal, 13 * 32))
        checked = []
        for rec in manifest["frames"]:
            if rec["render_status"] != "decoded":
                continue
            if rec["graphics_bank"] is not None:
                indices, _ = render(arc, rec["graphics_bank"], rec["parts_bank"], rec["frame"])
                images = {v: rgba(indices, words) for v, words in palettes.items()}
            else:
                cp = composition_frame(entry(arc, 3), rec["parts_bank"], rec["frame"])
                pix, size, bb, _ = compose_static(entry(arc, 0x10206), cp)
                indices = np.zeros((384, 384), np.uint8)
                indices[160+bb[1]:160+bb[3], 160+bb[0]:160+bb[2]] = np.frombuffer(pix, np.uint8).reshape(size[1], size[0])
                recipe = ROOT / rec["palette_source"]
                meta = load(recipe)
                colors = (recipe.parent / meta["palette_file"]).read_bytes()
                assert sha(colors) == rec["palette_sha256"]
                images = {v: rgba(indices, struct.unpack("<16H", colors)) for v in palettes}
            for variant, im in images.items():
                path = ROOT / revised[f"{variant}:{rec['id']}"] if f"{variant}:{rec['id']}" in revised else baseline / rec["images"][variant]
                assert np.array_equal(np.array(im), np.array(Image.open(path).convert("RGBA"))), (char, rec["id"], variant)
                imgs[variant][rec["id"]] = im
                checked.append({"id": f"{variant}:{rec['id']}", "PNG": path.relative_to(ROOT).as_posix(), "current_RGBA_exact": True})
        boards = []
        for variant in imgs:
            boards.extend(sheets(folder, variant, manifest["frames"], imgs[variant], imgs[variant]["b0_147"]))
        texture = entry(assets["ST0E_U1.ARC"], 0x10102)[:40960]
        parts = entry(assets["ST0E_U1.ARC"], 10)
        colors = entry(assets["COL0E_U1.ARC"], 5)
        ui = folder / "ui"
        ui.mkdir(exist_ok=True)
        items = []
        count = composition_frame(parts, 0, 0)["bank_frame_count"]
        for n in range(count):
            cp = composition_frame(parts, 0, n)
            im = Image.new("RGBA", (384, 384))
            for p in cp["parts"]:
                raw, size, bb, _ = compose_static(texture, local_composition({**cp, "parts": [p]}))
                words = struct.unpack_from("<16H", colors, p["clut"] * 32)
                patch = rgba(np.frombuffer(raw, np.uint8).reshape(size[1], size[0]), words)
                im.alpha_composite(patch, (160+bb[0], 160+bb[1]))
            old = Image.open(baseline / "supplementary" / f"selection_{n:03}.png").convert("RGBA")
            assert np.array_equal(np.array(im), np.array(old))
            items.append((f"select 0:{n}", im))
        for start in range(0, len(items), 24):
            name = f"selection_{start//24:02}.png"
            sheet(items[start:start+24], ui / name)
            boards.append({"path": "ui/"+name, "group": "selection", "variant": "normal", "frames": list(range(start, min(len(items), start+24)))})
        menu, texture = assets["MOJIPAT.ARC"], entry(assets["LOAD_U.ARC"], 0x10008)
        items = []
        for label, row in (("save_normal", 8), ("save_black", 27)):
            im = canvas(word_rgba(ui_canvas(menu, texture, 43, row)))
            assert np.array_equal(np.array(im), np.array(Image.open(baseline / "supplementary" / (label+".png")).convert("RGBA")))
            items.append((label, im))
        sheet(items, ui / "save.png")
        boards.append({"path": "ui/save.png", "group": "save", "variant": "both", "frames": ["normal", "black"]})
        results[char] = {"source_bin": source.relative_to(ROOT).as_posix(), "source_sha256": expected,
            "current_PL01_graphics_parts_palette_static_exact": True, "current_RGBA_checks": len(checked),
            "revised_PNG_references": len(revised), "UI_selection_references_checked": count, "UI_save_references_checked": 2,
            "source_reference_checks": checked, "sheets": boards,
            "unreconstructed": [r["id"] for r in manifest["frames"] if r["render_status"] != "decoded"],
            "limitations": ["현재 본체 팔레트는 실제 BIN에서 확인. CLUT2/정적 특수효과는 기존 해시 고정 미리보기 팔레트이다.",
                            "이 결과는 자료 신선성 확인과 시트 생성이며 미술 열람 완료 표시가 아니다."]}
        print(char, "prepared", len(boards), "sheets", len(checked), "RGBA checks", flush=True)
    (OUT / "freshness.json").write_text(json.dumps(results, ensure_ascii=False, indent=2)+"\n", "utf-8")


if __name__ == "__main__":
    main()
