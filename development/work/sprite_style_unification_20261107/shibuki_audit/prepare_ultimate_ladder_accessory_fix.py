"""뒤통수에 잘못 반복된 정면 선글라스 네 곳만 새 원화 국소편집 입력."""
from pathlib import Path
import sys,json,shutil
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write

def main():
    d=H/'ultimate_ladder_back_accessory01';need(not d.exists(),'Fresh output');d.mkdir();src=H/'ultimate_ladder_inputs01/page01/generated.png'
    need(sha(src.read_bytes())=='f42c13e7325e8d6c87fd9260032ee9372903fa3a4b26f3f04515df04d9ef0965','Changed generation');shutil.copyfile(src,d/'edit_target.png')
    prompt='''Edit the provided transparent six-sprite page with ONE small correction: the FOUR BACK-VIEW sprites, columns2 and3 in both rows, incorrectly have a pair of golden heart-shaped sunglasses drawn on the BACK OF THEIR HEADS. Remove those four gold heart outlines from the rear hair and restore the same coherent lavender hair locks underneath. Their face and sunglasses are on the unseen FRONT of the head. Do not draw any eyes, face, glasses lenses, necklace or large gold ornament on the back hair. The dark navy flower on the side of the hair stays exactly as it is. The TWO SIDE-VIEW sprites in column1 correctly show sunglasses above the eyes and MUST stay unchanged.
Everything else is locked: all six poses, silhouettes, hair/ear size, existing fine hair strands, jacket folds, sailor collars, bare arms, sandals, all hand and foot endpoints, forearm length, original 1536x1024 canvas and the 512x512 cell placement. Do not redraw clothes or move the figures. Top row remains white/navy jacket, bottom row sleeveless sailor swimsuit. This is not a new character design or a new pose. Keep the detailed pixel art and compact proportions.
Use a genuinely transparent background and remove only the low-opacity surrounding glow outside the figures; do not erase light-colored hair or white clothes. Solid sprite pixels should remain opaque. No floor, text, labels, borders or extra effects. Return the same full six-figure sheet, at the same exact size and coordinates.'''
    (d/'prompt.txt').write_text(prompt+'\n',encoding='utf8')
    write(d/'input.json',{'source':src.relative_to(ROOT).as_posix(),'source_sha256':sha(src.read_bytes()),'edit_target_sha256':sha((d/'edit_target.png').read_bytes()),'scope':'후면144/146 양의상의 뒤통수에 잘못 추가한 선글라스4곳 제거.143 측면 안경은 유지.','body_pose_scale_change':False,'registration_policy':'결과 전체교체 아님. 새 국소 머리영역을 원화 좌표 대조 후 제한 채택하며 다른 몸체 보존.','generated':False})
    print(json.dumps({'path':str(d)}))
if __name__=='__main__':main()
