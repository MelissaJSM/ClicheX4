"""전체 새원화 보존, 기존16×16 head창 바깥 뒤베일만 leg8 소유로 되돌린다."""
from pack_candidate import *
from prepare_common import X,Y,box
from scipy.ndimage import label
def main():
 a=Archive(PARENT.read_bytes());src=D/'preparation_effect_probe_v1';out=D/'preparation_effect_probe_v2';out.mkdir(exist_ok=False);fx=np.array(Image.open(src/'effect214_indices.png'));Image.fromarray(fx).save(out/'effect214_indices.png');rows=[];partials=[];frames=[]
 for key in(213,215):
  old={pb:np.array(Image.open(src/f'layer{pb}_{key}.png'))for pb in PBS};new={pb:z.copy()for pb,z in old.items()};bounds=[-12,-24,4,-8]if key==213 else[-8,-24,8,-8];m=(old[5]>0)&~box(*bounds)
  need(not np.any(new[8][m]),'소유중복');new[8][m]=new[5][m];new[5][m]=0
  need(comp(a,new,15).tobytes()==comp(a,old,15).tobytes(),'전체포스 그림불변');need(np.array_equal(new[0],old[0]),'기본 그림불변')
  checks=[]
  for n in(key,key+1):
   ls={pb:z.copy()for pb,z in new.items()}
   if n==214:
    ls[0][fx>0]=fx[fx>0]
    for pb in PBS[1:]:ls[pb][fx>0]=0
   for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n}.png')
   for mask in range(16):
    for arm in(1,2):im=comp(a,ls,mask,arm);checks.append({'ref':n,'mask':mask,'arm':arm,'components8':int(label(np.array(im)[:,:,3]>0,np.ones((3,3)))[1]),'rgba_sha256':sha(im.tobytes())})
   for mask in(0,15):need(comp(a,ls,mask).tobytes()==comp(a,{pb:np.array(Image.open(src/f'layer{pb}_{n}.png'))for pb in PBS},mask).tobytes(),'기본/포스 전체 불변')
  moved=[[int(x-160),int(y-160),int(old[5][y,x])]for y,x in np.argwhere(m)]
  frames.append({'key':key,'head_world_bounds':bounds,'moved_head5_to_veil_leg8':moved,'full_base_fourth_unchanged':True,'partial_checks':checks})
  rows.append((str(key),[('idle',a.composite(0,15)[0]),('old ownership full',comp(a,old,15)),('new ownership full exact',comp(a,new,15)),('head only old',comp(a,old,1)),('head only new',comp(a,new,1))]));partials.append((str(key),[(str(mask),comp(a,new,mask))for mask in(1,2,4,8,10)]))
 helper.grid(rows,out/'comparison.png',6);helper.grid(partials,out/'partial.png',6);write(out/'manifest.json',{'parent_sha256':BEFORE,'source':src.relative_to(ROOT).as_posix(),'frames':frames,'policy':'큰 뒤베일/머리끝의 기존 leg8 의미소유.앞16px모자/얼굴 head5 원범위를 유지한다.전체 기본/포스 그림과 source표본 불변이며부분소유만변경.214는같은원124효과 아래 모든아머를지운다.','runtime_verified':False});print(json.dumps([{'key':r['key'],'moved':len(r['moved_head5_to_veil_leg8']),'components':sorted({c['components8']for c in r['partial_checks']})}for r in frames]))
if __name__=='__main__':main()
