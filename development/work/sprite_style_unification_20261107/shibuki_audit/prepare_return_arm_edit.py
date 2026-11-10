"""귀환156 첫 새몸을 보호하며 손 위치만 국소 교정할 입력을 만든다."""
from pathlib import Path
import sys,json,shutil
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def main():
 s=H/'ultimate_return_inputs01';d=H/'ultimate_return_arm_edit02';need(not d.exists(),'Fresh local input');p=s/'generated.png';need(sha(p.read_bytes())=='de885d26b9a11c8838d4ea7a3a6770840a2188a7bec8c2eac4efcd959f038201','Source changed');d.mkdir();shutil.copyfile(p,d/'edit_target.png')
 # 가이드 그림은 새 도트가 아니라 입력 원화 위의 편집 목적지 표시다.
 guide=Image.new('RGBA',(1536,1024),(28,32,40,255));guide.alpha_composite(Image.open(p).convert('RGBA'));dr=ImageDraw.Draw(guide)
 for col in range(2):
  ox=col*768+384;oy=512
  for x in (-16,17):
   px=ox+x*8;py=oy+2*8
   dr.line((px,py-24,px,py+24),fill=(70,255,120),width=2)
   dr.line((px-12,py,px+12,py),fill=(70,255,120),width=2)
  dr.text((col*768+235,714),'Hands only: green marks = outer palm ends',fill='white')
 guide.convert('RGB').save(d/'hand_destination_guide.png')
 prompt='''Edit Image1 with one very small local change: slightly spread both forearms and hands outward, and lift the hands a little. Keep the image dimensions1536x1024, the two side-by-side figures, their size and exact head/body positions unchanged. Image2 is ONLY a placement guide: the green marks indicate the desired outer palm ends. Do not draw the marks, text or background into the output.
The hands in each figure need to move roughly24 image pixels outward and8 image pixels up. Re-articulate only the elbows, cuffs/wrists and small fists to reach the guide positions naturally. Keep shoulders fixed. Left figure keeps the detailed jacket sleeves and navy cuffs. Right figure keeps the bare arms and existing wrist accessories. Exactly two arms and two hands per figure, same pose in both outfits. Do not add another hand. Do not lengthen a straight strip of sleeve: preserve a small natural elbow bend and a connected wrist.
Preserve EVERYTHING else from Image1: identical head, ears, glasses, face, hair, torso, neckline, waist, outfit design, hips, legs, sandals and all existing detail. In particular do not edit the legs or feet during this pass. Do not make the figures larger, taller or wider through the body. Do not recompose, zoom, crop, move, rotate or mirror the figures. Keep the generous transparent margins exactly. This is a tiny forearm pose correction, not a new full-body drawing. Clean game pixel clusters; preserve true transparent background without any glow, haze, grid, text or labels.'''
 (d/'prompt.txt').write_text(prompt,'utf8');m=json.loads((s/'input.json').read_text('utf8'));write(d/'input.json',{'refs':[156],'forms_by_column':['before','after'],'source_layout':m['source_layout'],'ultimate_parent':m['ultimate_parent'],'source_new_art':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())},'edit_scope':'새156 머리/몸통/하체 고정. 팔꿈치부터 손끝까지 양쪽3px 바깥·1px 위의 원관절로 교정. 가이드는 아트가 아니다.','original_game_art_sent':False,'files':{q.name:sha(q.read_bytes())for q in d.iterdir()if q.is_file()}})
 reject=H/'ultimate_return_limb_edit01/rejection.json';need(not reject.exists(),'Fresh rejection record');write(reject,{'generated_sha256':'367f746cd48edaa7038dcfc084fd2a7af0cb1dd9c68a8cb44f16a89742b5c1a8','native_report':(H/'ultimate_return_limb_native01/report.json').relative_to(ROOT).as_posix(),'actual_viewed':['ultimate_return_limb_native01/before_comparison.png'],'status':'rejected','reasons':['첫 원화46px 및 기존47px에 비해 고정1/8등록 키가59px로 늘었다.','머리·몸통·팔다리까지 커졌으므로 국소 편집 보호 조건을 위반했다.','이 후보를 축소하거나 옛 몸체로 덮어 채택하지 않는다. 첫 새 원화를 보존하고 팔·발을 별도로 검토한다.'],'arc_written':False,'generation_slot_returned_to':'/root/overhaul_audio'})
 print(d)
if __name__=='__main__':main()
