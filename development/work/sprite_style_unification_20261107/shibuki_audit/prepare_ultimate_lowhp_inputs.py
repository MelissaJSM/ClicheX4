"""독립 PL02 저체력 양폼 입력·공유·원시간표 읽기. 새 그림/게임 쓰기 없음."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page,metrics,animation_map
from scripts.c01_audio_build import read_disc
from scripts.prepare_shibuki_ultimate_production import repack_parts
from native_pose_pack import SOURCE,SOURCE_SHA,need,sha,write
from src.psx_disc import file_hash
P=H/'prepared_run_complete03/PL02_U.ARC'
SHA='c7eb1c7998a6780d04f4397a64af653265e3d83985c3c05768dd3de46eae5265'
O=H/'ultimate_lowhp_inputs01'

def plate(a,refs):
 out=Image.new('RGBA',(len(refs)*512,1024))
 for row,mask in enumerate((15,0)):
  for col,n in enumerate(refs):
   q=a.composite(n,mask)[0].crop((128,128,192,192)).resize((512,512),Image.Resampling.NEAREST)
   out.alpha_composite(q,(512*col,512*row))
 return out
def main():
 need(not O.exists(),'Fresh input folder required');need(sha(P.read_bytes())==SHA,'Frozen run parent changed');a=Archive(P.read_bytes())
 need(file_hash(SOURCE)==SOURCE_SHA,'Source changed')
 exe=read_disc(SOURCE,('SLUS_005.61',))[0]['SLUS_005.61'];need(sha(exe)=='93a8f0cab28034bd7d5b93fe4362c7c56c8c2bfba5ccb764e7bf547a02ae1616','EXE changed')
 anims,refs=animation_map(exe);anim=anims[6];need(set(q['frame']for q in anim['steps'])==set(range(120,126)),'Unexpected native low HP refs')
 O.mkdir();plate(a,[0,116,13]).save(O/'accepted_style.png')
 # One row, two identical coordinate windows; jacket left, sleeveless suit right.
 poses=Image.new('RGBA',(1024,512))
 for col,mask in enumerate((15,0)):
  q=a.composite(120,mask)[0];q.save(O/('before_120.png'if mask else'after_120.png'))
  q=q.crop((128,128,192,192)).resize((512,512),Image.Resampling.NEAREST);poses.alpha_composite(q,(col*512,0))
 poses.save(O/'pose_reference.png')
 rows=[]
 for form,mask in(('before',15),('after',0)):
  page([(str(n),a.composite(n,mask)[0])for n in range(120,126)],a.composite(0,mask)[0],O/f'{form}_current.png',cols=3,scale=4)
  for n in [0,116]+list(range(120,126)):
   q,_=a.composite(n,mask);pixels=np.array(q);rows.append({'form':form,'ref':n,**metrics(q),'bottom4_rows_world':[[int(x)-160,int(y)-160]for y,x in zip(*np.nonzero((pixels[:,:,3]>0)&(np.indices(pixels.shape[:2])[0]>=180)))]})
 layer_refs={};groups={}
 for n in range(120,126):
  f=a.banks[0]['frames'][n];same=[q['index']for q in a.banks[0]['frames']if q['offset']==f['offset']]
  groups[str(f['offset'])]={'refs':same,'tile_count':f['tile_count'],'selected':n}
  layer_refs[n]={}
  for b in (0,5,6,7,8):
   v,m=a.layer(n,b);Image.fromarray(v).save(O/f'{n:03}_layer{b}.png');layer_refs[n][b]={'opaque_pixels':int(np.count_nonzero(v)),'parts':len(m['parts']),'indexed_sha256':sha(v.tobytes())}
 pairs=[]
 for n in(120,122,124):
  ls=[]
  for b in(0,5,6,7,8):
   x=a.layer(n,b)[0];y=a.layer(n+1,b)[0];yy,xx=np.nonzero(x!=y)
   ls.append({'bank':b,'changed_pixels':len(xx),'coordinates':[[int(px)-160,int(py)-160,int(x[py,px]),int(y[py,px])]for py,px in zip(yy,xx)]})
  pairs.append({'refs':[n,n+1],'layers':ls})
 slack={str(b):repack_parts(a.c,b,{})[1]for b in(0,5,6,7,8)}
 old_register=ROOT/'scripts/register_shibuki_ultimate_production.py'
 sourceart=ROOT/'work/ver_buki_riko/shibuki_art/ultimate_v1/production_art/action_generated.png'
 history={'source_art':str(sourceart.relative_to(ROOT)),'source_sha256':sha(sourceart.read_bytes()),'master_ref':120,'sheet_cell':10,'old_registration_script':str(old_register.relative_to(ROOT)),'script_sha256':sha(old_register.read_bytes())}
 history['confirmed_old_method']='原화셀을 옛 몸bbox로 비등방 크기변환한 뒤 옛 머리/피부를 보존하고 의상색을 가까운 원화픽셀로 전파. 원래head/detail 소실의 구조적 원인.'
 prompt='''Edit pose_reference.png into exactly TWO refined low-health pixel-art sprites of Tenko Shibuki, on a transparent 1024x512 canvas with two512x512 cells. LEFT: Ultimate before acquisition, wearing the oversized white/navy jacket. RIGHT: Ultimate after acquisition, the same character without that jacket, in the white/light-lavender sleeveless sailor swim dress. These are NOT a bikini, armor plates, or a red shrine outfit.
Use accepted_style.png as the exact accepted compact proportions and pixel detail reference. Its top row is jacket; bottom row is sleeveless swim dress; columns show idle, eye closure and newly approved movement. The character concept is clothing/accessory reference only, NEVER its tall realistic proportions. Preserve the compact accepted game body, broad short sleeves, short torso/limbs, rounded thighs and head including ears about38 percent of full sprite height. Do not make the body skinny, long-legged or taller to fill the cell.
Pose is exactly the original tired low-health pose from pose_reference.png: slightly slumped shoulders, head tilted down toward screen-left, eyes shut in fatigue, one hand close to chest and the other lowered; both feet planted at their existing positions. Both costumes must share EXACT same head, face, hair, ears, tail, neck, shoulders, elbow joints, hands, thighs, legs and sandals. The only difference is the jacket worn over the exact same swim dress/arms. Do not change direction, posture, foot positions or the relative anchors. Jacket can cover the underlying upper arms and dress. There must be no disconnect at the neck, waist, wrists or knees.
Restore the accepted idle's crisp layered lavender hair strands, restrained one-pixel dark outline, ear inner planes, gold-rimmed heart sunglasses resting on top of the head, side flower accessories, clear human anime face and tired eyelids. Keep the exact lavender/navy/white/pink palette feeling. Clothing: white short sailor swim dress with dark navy collar, little pink tie, defined lower pleats and white/pink sandals; jacket adds dark navy lapel, gold piping, white cuff/hem folds, never a giant blank white blob. Preserve the fine distinctions between collar, sleeves, torso and skirt. Do not use the current simplified head or stretch the forearms. Whole newly drawn upper body must match the idle density.
Each cell is a64x64 game-pixel viewport enlarged8x. Keep the sprite positioned where the pose reference is with transparent margin all around, no bounding-box normalization or filling the cell. Draw readable pixel clusters at that native scale, not smooth illustration, blur, gradients or repetitive black hair scratches. No labels, text, extra poses, shadow or backdrop. Two complete unclipped sprites only.'''
 (O/'prompt.txt').write_text(prompt+'\n','utf8')
 info={'source_arc':str(P.relative_to(ROOT)),'source_sha256':SHA,'source_bin_sha256':SOURCE_SHA,'executable_sha256':sha(exe),'canvas':[1024,512],'cell_native':[64,64],'world_viewport':[-32,-32,32,32],'display_scale':8,'forms_left_to_right':['ultimate_before_jacket','ultimate_after_swimdress'],'refs':list(range(120,126)),'native_animation':anim,'duration_policy':'원래 animate_object 호출단위,0=256/-1=255. 사건/상태전환은 이 표만으로 실행하지 않는다.','metrics':rows,'layers':layer_refs,'raw_shared_groups':groups,'blink_pair_differences':pairs,'part_bank_slack_bytes':slack,'historical_method':history,'source_inputs':{f:sha((O/f).read_bytes())for f in('accepted_style.png','pose_reference.png')},'concept':'character/ver_buki_riko/buki(ultimate armor).webp','concept_sha256':sha((ROOT/'character/ver_buki_riko/buki(ultimate armor).webp').read_bytes()),'old_master_overwrite_allowed':False,'new_after_body_must_fit_new_before_alpha':True,'generation_started':False,'game_modified':False}
 write(O/'analysis.json',info);print(json.dumps({'folder':str(O),'groups':groups,'slack':slack,'native_steps':len(anim['steps'])},ensure_ascii=False))
if __name__=='__main__':main()
