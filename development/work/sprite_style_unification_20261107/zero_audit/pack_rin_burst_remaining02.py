"""v1 비수용 회색 신발만 새 원화 색으로 교정한 낙봉파9 별도 준비본."""
from pathlib import Path
import sys,json,hashlib,struct,shutil
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(D))
import pack_rin_burst_remaining01 as base
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
R=D/'rin_extension';P=base.P;O=R/'prepared_burst_remaining02';sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text('utf8'))
EXPECTED={178:'91f9715e0cbb37ccdf2ae7067ac73816631b2fe9ea62a83f4569a1e852ff8512',179:'4436d7a1f2ca4aadb2d4a024d7d3c04f5265bee84bb2ca20726fcf4008fbf806',180:'48ce82b8184d629500338ebd5f54c6fee1aae11e7e42e30288f5d7011b628d08',181:'a13c11d138b3c4b8e42bab59d4a1c3f76bb1d7cec522ed0967e4a7f6848bffbf'}
def targets():
 t=base.load_targets()
 for n,h in EXPECTED.items():
  p=R/'burst_charge_registered_v2'/f'b1_{n:03}_combined_indices.png';assert sha(p.read_bytes())==h,('Changed registered art',n);t[n]=np.array(Image.open(p))
 return t
def build(arc,overrides=None):return base.build(arc,targets()if overrides is None else overrides)
def main():
 assert not O.exists();arc=P.read_bytes();out,v,tt=build(arc);again,_,_=build(arc);assert out==again;O.mkdir();(O/'PL01_U.ARC').write_bytes(out)
 oldcandidate=(R/'prepared_burst_remaining01/PL01_U.ARC').read_bytes();assert sha(oldcandidate)=='626a059f3a290d5d15f647aa6bbb8b9be51e88060638d6a14d62a34508835f6a'
 changed=[]
 for b,pb,total in((0,0,254),(1,5,190)):
  for n in range(total):
   if b==1 and 42<=n<=49:continue
   a,z=render(oldcandidate,b,pb,n)[0],render(out,b,pb,n)[0];k=a!=z
   if k.any():assert b==1 and n in EXPECTED and np.array_equal(a>0,z>0);changed.append({'ref':n,'pixels':int(k.sum())})
 assert sum(x['pixels']for x in changed)==154 and len(changed)==4
 for n,z in tt.items():Image.fromarray(z).save(O/f'b1_{n:03}_indices.png')
 for name in('palette.bin','effect_23.png','effect_24.png'):shutil.copyfile(P.parent/name,O/name)
 recipe=read(P.parent/'static_effects.json');recipe['parts_sha256']=sha(entry(out,3));(O/'static_effects.json').write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n','utf8')
 for form,row in(('normal',0),('black',13)):
  pal=struct.unpack_from('<16H',entry(out,9),row*32)
  for page,ids in enumerate(([177,178,179],[180,181,186],[187,188,189])):
   sh=Image.new('RGB',(1440,len(ids)*400),'#263142');dr=ImageDraw.Draw(sh)
   for i,n in enumerate(ids):
    for col,(tag,z)in enumerate([('idle147',render(out,0,0,147)[0]),(f'{n} old',render(arc,1,5,n)[0]),(f'{n} packed v2',render(out,1,5,n)[0])]):
     pic=rgba(z,pal).crop((112,112,208,188)).resize((480,380),Image.Resampling.NEAREST);sh.paste(pic,(col*480,i*400+20),pic);dr.text((col*480+4,i*400+4),tag,fill='white')
   sh.save(O/f'{form}_readback_{page:02}.png')
 q={'source_arc':rel(P),'source_arc_sha256':base.SOURCE,'resource':rel(O/'PL01_U.ARC'),'after_sha256':sha(out),'new_art_refs':[f'b1_{n:03}'for n in sorted(tt)],'cumulative_main_refs':303,'previous_frozen_art_refs':294,'new_original_masters':7,'reuse177':'원래 몸체가 정확히 같은 현재 새101 + 원효과70px','alias187':186,'target_sha256':{str(n):sha((O/f'b1_{n:03}_indices.png').read_bytes())for n in tt},'verification':v,'reproducible':True,'static_body_patch':{'recipe':rel(O/'static_effects.json'),'sha256':sha((O/'static_effects.json').read_bytes())},'superseded_candidate':{'path':rel(R/'prepared_burst_remaining01/PL01_U.ARC'),'sha256':sha(oldcandidate),'adopted':False,'reason':'178..181 신발색이 대기와 다르게 회색으로 읽힘'},'shoe_color_edit':{'source':rel(R/'burst_shoe_edit01/generated.png'),'source_sha256':sha((R/'burst_shoe_edit01/generated.png').read_bytes()),'registration':rel(R/'burst_charge_registered_v2/registration.json'),'registration_sha256':sha((R/'burst_charge_registered_v2/registration.json').read_bytes()),'changed_from_first_candidate':changed,'all_other_display_pixels_exact':True,'all_alpha_exact':True},'root_art_review_pending':True,'runtime_verified':False,'user_accepted':False,'ready_for_checkpoint_integration':False,'scope':'낙봉파 잔여9. 7개 새몸체와177/101·186/187 공유. 원구체1064 world texel, 원4공유/타일수/이전294/부분8/외부정적효과 보존. 신발은 국소 생성 원화의 파란색154셀만 동일위치 등록.'}
 (O/'proposal.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':sha(out),'slack':v['repack']['remaining_slack'],'xy_bytes':v['only_tile_window_xy_bytes'],'shoe_changes':changed}))
if __name__=='__main__':main()
