"""Keep new victory art; recover only its own cyan iris lost by color voting."""
from pathlib import Path
import sys,json,hashlib,struct,collections
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';O=D/'victory_registered_v1';assert not O.exists();O.mkdir()
P=D/'prepared_rising_rear_v1/PL01_U.ARC';arc=P.read_bytes();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(P)=='223e553f97ecc85d52b085f3e0e6cd46ecc914063f1adcef43fd1d34c25d298e'
pal=struct.unpack_from('<16H',entry(arc,9));black=struct.unpack_from('<16H',entry(arc,9),13*32);records=[];items={f:[]for f in('normal','black')}
expected_sources={'victory_detail01':'1db69b93d93ee61e121a156557df87a77c0218f5d772d4f320c0b28b86421719','victory_detail02':'0fc788eb53bc774697af9b5b7167d07457eebce27d01973fb941a5203ec6d956'}
# Explicit semantic iris cells preserve the neighboring white catchlight and skin.
iris={1:(159,138),2:(163,138),3:(164,138),4:(164,137),6:(162,137)}
for n,(ix,iy)in iris.items():
 folder='victory_detail02'if n==6 else'victory_detail01';d=D/folder;assert sha(d/'generated.png')==expected_sources[folder]
 info=json.loads((d/'inputs.json').read_text('utf8'));f=next(v for v in info['frames']if v['ref']==n);im=Image.open(d/'generated.png').convert('RGBA');cw,ch=im.width/info['columns'],im.height/info['rows'];cx,cy=f['cell']
 crop=im.crop((round(cx*cw),round(cy*ch),round((cx+1)*cw),round((cy+1)*ch)));v=np.array(crop).astype(float);r,g,b,alpha=[v[:,:,k]for k in range(4)];ratio=np.divide(g,b,out=np.zeros_like(g),where=b>0);mask=(alpha>=128)&(r<g*.6)&(g>90)&(ratio>.6)&(ratio<1.15)
 yy,xx=np.nonzero(mask);votes=collections.Counter(zip((112+xx*96/cw).astype(int).tolist(),(112+yy*80/ch).astype(int).tolist()));count=votes[ix,iy];assert count>=10
 ip=d/f'native/b1_{n:03}_indices.png';a=np.array(Image.open(ip));original_index=int(a[iy,ix]);assert original_index in(3,4,5,6);a[iy,ix]=15
 before=render(arc,1,5,n)[0];yy,xx=np.nonzero(a);assert int(yy.max())==int(np.nonzero(before)[0].max())==183
 op=O/f'b1_{n:03}_indices.png';Image.fromarray(a).save(op)
 for form,words in[('normal',pal),('black',black)]:
  image=rgba(a,words);image.save(O/f'b1_{n:03}_{form}.png');items[form]+=[(f'b1:{n} before',rgba(before,words)),(f'b1:{n} refined',image)]
 records.append({'key':f'b1_{n:03}','bank':1,'ref':n,'input_native':str(ip.relative_to(ROOT)),'input_native_sha256':sha(ip),'generated':str((d/'generated.png').relative_to(ROOT)),'generated_sha256':sha(d/'generated.png'),'after_sha256':sha(op),'source_iris_registration':{'xy':[ix,iy],'before':original_index,'after':15,'cyan_source_pixels_in_cell':count,'method':'새 원화의 청록 표본이 있는 어두운 홍채 셀만 팔레트15로 등록. 흰 눈 하이라이트와 피부 셀은 그대로.'},'whole_body_translation':[0,0],'old_head_or_body_pixels_copied':0,'floor_y':183,'floor_x':np.where(a[183]>0)[0].tolist(),'bbox':[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]})
for form,words in[('normal',pal),('black',black)]:
 for i in range(0,len(items[form]),6):page(items[form][i:i+6],rgba(render(arc,0,0,147)[0],words),O/f'{form}_comparison_{i//6:02}.png',cols=2,scale=5)
 page([('refined5 preserved',rgba(render(arc,1,5,5)[0],words)),('refined6',rgba(np.array(Image.open(O/'b1_006_indices.png')),words))],rgba(render(arc,0,0,147)[0],words),O/f'{form}_victory5_6.png',cols=2,scale=6)
report={'source_arc':str(P.relative_to(ROOT)),'source_arc_sha256':sha(P),'records':records,'new_body_refs':[1,2,3,4,6],'planned_departure_sync_refs':[7,8],'protected_body_refs':[0,5],'protected_effect_refs':list(range(9,14)),'palette_unchanged':True,'root_review_pending':True,'user_accepted':False,'runtime_verified':False,'scope':'새 원화5자세를 고정셀 등록. 전신이동0, 발바닥183유지. 새 원화의 청록 홍채가 소실된1셀씩만 복구하며 옛머리/몸을 덮지 않음.'}
(O/'registration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'out':str(O),'hashes':{r['key']:r['after_sha256']for r in records}}))
