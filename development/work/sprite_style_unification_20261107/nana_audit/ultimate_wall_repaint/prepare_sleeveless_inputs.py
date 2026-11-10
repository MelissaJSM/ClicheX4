"""후폼 새 몸체+새 재킷사격팔의 위치 가이드. 생성 입력이며 완성 그림 아님."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
def main():
 a=Archive((N/'ultimate_air_repaint/packed_air_candidate_v1/PL02_U.ARC').read_bytes())
 for page,refs,sub in [('a',(56,58,60),'firing_a_before_joint_probe_v2'),('b',(62,64,66),'firing_b_before_joint_probe_v4')]:
  out=D/f'firing_{page}_after_inputs_v1';out.mkdir(exist_ok=False);boards={k:Image.new('RGBA',(1280,1280))for k in('after_body_with_sleeve_guide','accepted_new_before_shots','new_after_bodies')};records=[];source=D/sub;meta=json.loads((source/'registration.json').read_text('utf8'))
  for i,n in enumerate(refs):
   body=np.array(Image.open(D/'costume_pair_probe_v2'/f'after_{n-1:03}.png'));new=np.array(Image.open(source/f'before_{n:03}.png'));use=np.array(Image.open(source/f'used_arm_{n:03}.png'))>0;held=np.array(Image.open(source/f'new_hand_removal_{n:03}.png'))>0;bar=np.array(Image.open(D/'weapon_constraints_v1'/f'case_{n:03}.png'));q=next(x for x in meta['frames']if x['ref']==n)
   guide=body.copy();guide[held]=0;guide[use]=new[use]
   for p in q['new_folded_cuff_alpha_from_firing_source']:
    x,y=p['world'];guide[y+160,x+160]=new[y+160,x+160]
   guide[bar>0]=bar[bar>0]
   rgba=a.rgba(guide,0);before_rgba=a.rgba(new,16);ar=np.array(rgba);br=np.array(before_rgba);ar[use]=br[use];rgba=Image.fromarray(ar)
   ims={'after_body_with_sleeve_guide':rgba,'accepted_new_before_shots':before_rgba,'new_after_bodies':a.rgba(body,0)}
   for k,im in ims.items():boards[k].alpha_composite(im.crop((112,112,208,208)).resize((640,640),Image.Resampling.NEAREST),(i%2*640,i//2*640))
   Image.fromarray(guide).save(out/f'guide_{n:03}.png');records.append({'ref':n,'before_shot_path':str((source/f'before_{n:03}.png').relative_to(ROOT)),'before_shot_sha256':digest(source/f'before_{n:03}.png'),'after_body_sha256':digest(D/'costume_pair_probe_v2'/f'after_{n-1:03}.png'),'guide_index_sha256':sha(guide.tobytes()),'guide_is_unfinished_costume_mix':True})
  for k,im in boards.items():im.alpha_composite(a.composite(85,15 if k=='accepted_new_before_shots'else 0)[0].crop((112,112,208,208)).resize((640,640),Image.Resampling.NEAREST),(640,640));im.save(out/f'{k}.png')
  write(out/'manifest.json',{'frames':records,'only_imagegen_input':True,'fourth_cell_reference_only':True,'input_hashes':{p.name:digest(p)for p in out.glob('*.png')}})
 print('after a/b input prepared')
if __name__=='__main__':main()
