"""사용자 재개 후 정식 도구가 반환한135를 고정 셀 좌표에 등록한다."""
from pathlib import Path
import hashlib,json,shutil,sys
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;W=H.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(H))
from scripts.export_x_consistency import Archive,page,metrics
from inspect_ultimate_hurt_common import grid
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=H/'ultimate_arrival135_resume51';assert not out.exists();out.mkdir()
generated=Path('<LOCAL_PATH>');shutil.copyfile(generated,out/'generated.png')
src=json.loads((W/'staging_br_v31.json').read_text('utf8'))['resources']['PL02_U.ARC'];parent=ROOT/src['path'];assert sha(parent)==src['after'];a=Archive(parent.read_bytes())
im=Image.open(out/'generated.png').convert('RGBA');assert im.size==(1536,1024);sample=np.array(im.resize((192,128),Image.Resampling.NEAREST));cell=sample[64:128,96:192]
rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.int32)
q=(1+((cell[:,:,:3].astype(np.int32)[:,:,None]-rgb[None,None,1:])**2).sum(3).argmin(2)).astype(np.uint8);q[cell[:,:,3]<128]=0
after=np.zeros((384,384),np.uint8);after[128:192,112:208]=q
bp=H/'ultimate_arrival_native01/before_135_indices.png';before=np.array(Image.open(bp));rows=[]
for form,v,pal,mask in [('before',before,16,15),('after',after,0,0)]:
    Image.fromarray(v).save(out/f'{form}_135_indices.png');native=a.rgba(v,pal);native.save(out/f'{form}_135.png');page([(f'135 current {form}',a.composite(135,mask)[0]),(f'135 registered {form}',native)],a.composite(0,mask)[0],out/f'{form}_comparison.png',cols=2,scale=5);rows.append({'form':form,'metrics':metrics(native)})
grid([a.rgba(before,16),a.rgba(after)],out/'135_grid.png',['approved new jacket135','user-resumed edited135'])
report={'generated_file':str(generated),'generated_sha256':sha(out/'generated.png'),'same_original_prompt_sha256':sha(H/'ultimate_arrival135_arms01/prompt.txt'),'parent_arc':src,'before_source':{'path':bp.relative_to(ROOT).as_posix(),'sha256':sha(bp)},'user_authorized_resume':True,'tool':'builtin image_gen','tool_success':True,'fallback_used':False,'filter_bypassed':False,'original_failure_preserved':True,'native_registration_scale':.125,'alpha_threshold':128,'palette_changed':False,'new_game_arc_written':False,'visual_review_pending':True,'rows':rows,'after_outside_before':int(((after>0)&(before==0)).sum())}
(out/'registration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'output':str(out),'rows':rows,'outside':report['after_outside_before']}))
