"""잔여75의 잘리지 않은 보조판과 구체 후속 분류를 저장한다."""
from pathlib import Path
import sys,json,struct,hashlib
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';O=D/'remaining240_review';a=(D/'prepared_bank1_recovery128/PL01_U.ARC').read_bytes();pal=struct.unpack_from('<16H',entry(a,9));idle=rgba(render(a,0,0,0)[0],pal)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();j=json.loads((O/'manifest.json').read_text('utf8'))
for page in j['additional_sheets']:
 sheet=Image.new('RGB',(1536,1080),(28,34,45));draw=ImageDraw.Draw(sheet)
 for i,ref in enumerate(page['refs']):
  b,n=int(ref[1]),int(ref.split('_')[1]);z=render(a,b,b*5,n)[0];outside=z.copy();outside[96:208,104:232]=0;assert not outside.any()
  x=i%2*768;y=i//2*360;draw.text((x+5,y+5),ref+' / idle0 -> current',fill='white')
  for col,pic in enumerate((idle,rgba(z,pal))):
   view=pic.crop((104,96,232,208)).resize((384,336),Image.Resampling.NEAREST);sheet.paste(view,(x+col*384,y+24),view)
 p=ROOT/page['path'];sheet.save(p);page['sha256']=sha(p);page['scale']=3;page['full_pose_in_crop_asserted']=True;page['actually_viewed']=False
for g in j['groups']:
 if g['group']=='rakuhouha':
  g['reason']='177..181은 몸체와 별도 구체 표현이 함께 있어 기존 효과 소유를 분리한 뒤 새5자세가 필요하다.186/187은 같은 낮은 회복,188/189는 서로 다른 후속 자세로 새3원화가 필요하다.'
  for r in g['refs']:r['status']='needs_repaint_body_preserve_original_effect'
j['concrete_backlog']={'ride_armor_head':{'refs':19,'source_masters':5,'generation_saved':True,'packed':False},'ride_chaser':{'refs':28,'body_angle_masters':4,'ribbon_phase_count':4},'arrival':{'body_refs':5,'white_flash_refs_preserve':2},'rakuhouha':{'body_refs':9,'exact_unique_body_and_effect_shapes':8,'effects_must_be_separated':True},'baseline_idle_and_transition_refs_preserve':10,'derived_static_already_synchronized_refs':2,'total_ledger_refs':75,'active_repaint_refs':61,'not_art_completion_percentage':True}
j['correction']='b1_000은 빈 그림이 아니라 b0_147 대기 사본임을 실제 표시 완전일치와 열람으로 정정했다. 빈 탑승80과 혼동하지 않는다.'
j['visual_observations']=['탑승머리4판과 체이서5판을 실제 열람했고 현재240의73 비정적 잔여가222 원본표시와 완전일치함을 확인했다.','체이서는 흰 얼굴/검정 몸통/치마·부츠가 큰 면으로 남아 대기보다 세부가 부족하다.4각도에서 손과 좌석 접점을 고정해 상세화를 진행한다.','등장249..253은 머리와 의상 내부 표현이 단순하다.247/248은 원래 의도한 흰 섬광이므로 이후 새몸에 맞춘 파생만 검토한다.','낙봉파177..181의 손 구체를 몸 일부로 다시 그리지 않는다.186..189는 자세 변화와 원래 낮은 중심을 보존하면서 머리/앞치마/부츠를 보완한다.']
(O/'manifest.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(j['concrete_backlog']))
