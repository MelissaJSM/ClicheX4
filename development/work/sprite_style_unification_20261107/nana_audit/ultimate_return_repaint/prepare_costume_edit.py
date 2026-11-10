"""귀환 후폼의 잘못 생긴 흰 반바지만 기존 검정/분홍 의상으로 수정 요청."""
from pathlib import Path
import json,hashlib
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 out=D/'costume_edit_inputs_v1';out.mkdir(exist_ok=False)
 src=D/'body_v1/generated.png';assert sha(src)=='3a404c02d31fd865a38980b12e2f1f5e0536fcc92a2842cd8932a822dd466150'
 (out/'target.png').write_bytes(src.read_bytes())
 Image.open(D/'body_inputs_v1/targets.png').crop((768,0,1536,1024)).save(out/'accepted_pose_costume.png')
 style=Image.open(D/'body_inputs_v1/style.png');style.crop((768,0,1536,1536)).save(out/'accepted_style_costume.png')
 prompt='''Use case: precise-object-edit. Image1 is the EDIT TARGET, two neutral full-body adult game sprites on a1536x1024 transparent canvas. Keep its complete canvas, both sprite positions, scale, and pose exactly unchanged. Correct ONE clothing error on the RIGHT sprite only: the newly invented white/gray shorts below her pink waist belt do not belong to her accepted costume.
Replace only those white/gray shorts with the established black/pink fitted athletic costume shown on the RIGHT character in Images2 and3, retaining the accepted coverage, pink waistband, dark fabric side panels, and the existing natural skin contours. This is costume continuity for the same adult heroine. Image2 is the exact older return pose and accepted costume. Image3 shows accepted idle and victory clothing detail; use only its fabric design, not its poses.
Do not change the left pink-jacket sprite at all. On the right preserve the new detailed head, ears, pink hair strands, face/green eye, empty fists held near chest, forearms, black upper garment, torso proportions, bent knees, calves, and green/gray shoes. Do not raise or lower the waistband or change her body shape. No new accessories, weapons or extra limbs. Preserve both footprints and native pixel clusters. Output the same two full-body sprites on actual transparent background, no halo, glow, labels, grid, or background. The only substantive change is replacing the incorrect white shorts with the accepted black/pink costume.'''
 (out/'prompt.txt').write_text(prompt,'utf8')
 record={'source_sha256':sha(src),'scope':'오른쪽156 후폼의 잘못된 흰 반바지만 수용 검정/분홍 의상으로. 새 머리·몸·팔·다리·발과 왼쪽 재킷형 보존.','native_packed':False,'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in out.iterdir() if p.is_file()]}
 (out/'manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n','utf8')
 print(out)
if __name__=='__main__':main()
