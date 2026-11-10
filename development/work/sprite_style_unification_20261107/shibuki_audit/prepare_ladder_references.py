"""사다리 다음 묶음의 실제 참조·반전·공유·원총구 및 새 원화 입력을 준비한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.export_x_consistency import Archive,page
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write
from scripts.c01_audio_build import read_disc
from src.psx_disc import file_hash

REFS=[*range(143,156),183]
KEYS=[143,144,146,149,151,153,154,183]
MIRRORS={144:(145,-1),146:(147,0),149:(148,0),151:(152,0)}

def mirrored(v,delta):
 out=np.zeros_like(v);y,x=np.nonzero(v);out[y,320+delta-x]=v[y,x];return out

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source changed');baseline=read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC'];data=(H/'prepared_wall_front01/PL00_U.ARC').read_bytes();need(sha(data)=='db508292c2746b5c4a12e60e9cf28f5ebe558e7998788c3d1d5440a4f8fd481a','Checkpoint changed')
 a=Archive(data);src=Archive(baseline);out=H/'ladder_detail_inputs01';need(not out.exists(),'Output exists');out.mkdir();rows=[];history=ROOT/'work/ver_buki_riko/shibuki_art/ladder_v1/production15'
 for n in REFS:
  v=a.layer(n)[0];old=np.zeros_like(v);old[120:200,112:208]=np.array(Image.open(history/f'frame_{n:03}.png'));need(np.array_equal(v,old),'Historical body mismatch')
  f=a.banks[0]['frames'][n];y,x=np.nonzero(v)
  for mask in(0,15):need(a.composite(n,mask)[0].tobytes()==src.composite(n,mask)[0].tobytes(),'Cumulative changes touched next group')
  rows.append({'ref':n,'bbox_world_exclusive':[int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)],'shared_gfx_refs':[q['index']for q in a.banks[0]['frames']if q['offset']==f['offset']],'historical_source':(history/f'frame_{n:03}.png').relative_to(ROOT).as_posix(),'historical_exact':True,'native_body_sha256':sha(v.tobytes())})
  for mask,label in((0,'base'),(15,'fourth')):a.composite(n,mask)[0].save(out/f'{label}_{n:03}.png')
 mirror_checks=[]
 for main,(alias,delta)in MIRRORS.items():
  matches=[]
  for b in(0,5,6,7,8):matches.append({'bank':b,'exact':bool(np.array_equal(mirrored(a.layer(main,b)[0],delta),a.layer(alias,b)[0]))})
  need(matches[0]['exact'],'Actual base mirror differs')
  mirror_checks.append({'main':main,'alias':alias,'world_formula':f'x2={delta}-x1; y2=y1','layers':matches})
 for mask,label in((0,'base'),(15,'fourth')):
  for start in(0,7):page([(f'{n} actual current',a.composite(n,mask)[0])for n in REFS[start:start+7]],a.composite(0,mask)[0],out/f'{label}_current{start//7:02}.png',cols=3,scale=4)
 for pn,keys in enumerate((KEYS[:3],KEYS[3:6],KEYS[6:]),1):
  board=Image.new('RGBA',(len(keys)*512,1024),(0,0,0,0))
  for row,mask in enumerate((0,15)):
   for col,n in enumerate(keys):
    im=a.composite(n,mask)[0];bb=im.getbbox();need(bb[0]>=128 and bb[1]>=128 and bb[2]<=192 and bb[3]<=192,'64 native input crop clips pose');board.alpha_composite(im.crop((128,128,192,192)).resize((512,512),Image.Resampling.NEAREST),(col*512,row*512))
  board.save(out/f'page{pn:02}_poses.png')
 # Only our existing mod sprites are included. Original X is never an imagegen input.
 reference=Image.new('RGBA',(1536,1024),(0,0,0,0))
 for row,mask in enumerate((0,15)):
  for col,n in enumerate((0,55,61)):reference.alpha_composite(a.composite(n,mask)[0].crop((128,128,192,192)).resize((512,512),Image.Resampling.NEAREST),(col*512,row*512))
 reference.save(out/'accepted_idle_new_wall_reference.png')
 shot=json.loads((history/'registration.json').read_text('utf8'))
 inventory=json.loads((ROOT/'work/sprite_consistency_20261105/coverage/ver_buki_riko/x_animations.json').read_text('utf8'));animations=[{'id':r['id'],'graphics_bank':r['graphics_bank'],'composition_bank':r['composition_bank'],'steps':r['steps'],'loop_to_position':r['loop_to_position']}for r in inventory['animations']if any(s['frame']in REFS for s in r['steps'])]
 write(out/'manifest.json',{'source_bin_sha256':SOURCE_SHA,'baseline_arc_sha256':sha(baseline),'parent_arc_sha256':sha(data),'refs':rows,'new_body_key_refs':KEYS,'firing_refs':[150,155],'firing_common_body':149,'firing_original_muzzles':[{'ref':q['frame'],'world':q['original_muzzle_world']}for q in shot],'mirror_relations':mirror_checks,'animations':animations,'page_layout':{'native_crop_world':[-32,-32,32,32],'source_scale':8,'each_cell':[512,512],'top':'base','bottom':'Fourth','page01':KEYS[:3],'page02':KEYS[3:6],'page03':KEYS[6:]},'reference_only_no_generation':True,'initial_art_problem':'후면의 큰 단색 머리면과 단순한 옷깃·허리 디테일이 대기보다 빈약하다. 3/4사격 얼굴도 구형 벽 머리와 같은 단순화가 남는다.','keep':['원래 손·발의 사다리 접점','8개의 서로 다른 관절 자세와 반전 중심','150/155 원 배럴 크기와 총구','부분 아머16종 및 양팔','대기 크기의 머리/귀와 짧은 몸 비율'],'do_not':['후면 전체에 같은 정면 대기 머리 붙이기','과거 소매를 늘여 총구 연결','본문 bbox에 맞춰 전신 강제 리사이즈','큰 단색 머리의 선 몇 개만 더하고 완료 선언']})
 print(json.dumps({'keys':KEYS,'mirror_layers':mirror_checks,'shots':shot,'animations':[r['id']for r in animations]}))

if __name__=='__main__':main()
