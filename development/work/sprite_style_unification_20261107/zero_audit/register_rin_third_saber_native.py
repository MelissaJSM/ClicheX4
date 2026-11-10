"""Keep authored details and recover the source cyan-eye sample lost by voting."""
from pathlib import Path
import sys,json,hashlib,struct,collections
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';O=D/'third_saber_registered_v2';assert not O.exists();O.mkdir()
P=D/'prepared_burst_pair_final_v1/PL01_U.ARC';arc=P.read_bytes();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(P)=='10f1cc28662a8ceae3b3e00c305fdbeeb0e7e16bc21c13d65a05fadc19e19ca3'
pal=struct.unpack_from('<16H',entry(arc,9));black=struct.unpack_from('<16H',entry(arc,9),13*32)
items={v:[]for v in('normal','black')};records=[]
for n in[109,111,113,115,121]:
 d=D/('third_saber121_01'if n==121 else'third_saber01');p=d/f'native/b0_{n:03}_indices.png'
 before=render(arc,0,0,n)[0];a=np.array(Image.open(p));assert a.shape==(384,384)and a.max()<=15
 correction=[]
 if n==109:
  im=np.array(Image.open(d/'generated.png').convert('RGBA')).astype(float)[:512,:768]
  r,g,b,alpha=[im[:,:,j]for j in range(4)];ratio=np.divide(g,b,out=np.zeros_like(g),where=b>0)
  mask=(alpha>=128)&(r<g*.6)&(g>90)&(ratio>.6)&(ratio<1.15)
  yy,xx=np.nonzero(mask);keep=(yy<270)&(xx>150)&(xx<370);yy,xx=yy[keep],xx[keep]
  votes=collections.Counter(zip((112+xx//8).astype(int).tolist(),(124+yy//8).astype(int).tolist()))
  (x,y),count=votes.most_common(1)[0];assert(x,y,count)==(153,148,33)
  assert a[y,x]!=0 and a[y,x]!=15
  correction.append({'x':x,'y':y,'before':int(a[y,x]),'after':15,'cyan_source_pixels_in_native_cell':count,
                     'reason':'생성 원화의 청록 눈 색이 RGB 최단거리 다수결에서 사라진 한 셀만 원래 청록 팔레트로 등록한다. 옛 머리 픽셀을 복사하지 않는다.'})
  a[y,x]=15
 name=f'b0_{n:03}_indices.png';Image.fromarray(a).save(O/name)
 anchors={}
 for label,arr in[('before',before),('new',a)]:
  y,x=np.nonzero(arr);ey,ex=np.nonzero((arr==15)&(np.indices(arr.shape)[0]<160))
  anchors[label]={'bbox':[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)],
                  'lowest_y':int(y.max()),'bottom_row_x':np.where(arr[y.max()]>0)[0].tolist(),
                  'eye_cyan_xy':[[int(x),int(y)]for y,x in zip(ey,ex)]}
 assert anchors['new']['lowest_y']==anchors['before']['lowest_y']==183
 for v,words in[('normal',pal),('black',black)]:
  im=rgba(a,words);im.save(O/f'{v}_b0_{n:03}.png')
  items[v]+=[(f'b0_{n:03} before',rgba(before,words)),(f'b0_{n:03} detailed',im)]
 records.append({'key':f'b0_{n:03}','input_native':str(p.relative_to(ROOT)),'input_native_sha256':sha(p),
                 'generated':str((d/'generated.png').relative_to(ROOT)),'generated_sha256':sha(d/'generated.png'),
                 'after_sha256':sha(O/name),'source_eye_registration':correction,'anchors':anchors,
                 'old_head_or_body_overwrite':False,'world_translation':[0,0]})
for v,words in[('normal',pal),('black',black)]:page(items[v],rgba(render(arc,0,0,147)[0],words),O/f'{v}_comparison.png',cols=2,scale=4)
report={'source_arc':str(P.relative_to(ROOT)),'source_sha256':sha(P),'records':records,
        'exact_display_aliases':[[109],[111],[113],[115,117,119],[121,123,125,127]],
        'palette_unchanged':True,'native_scale':{'page01':.125,'single121':.0625},
        'all_foot_contact_y183':True,'all_hand_or_toe_pixels_identical':False,
        'anchor_scope':'발바닥 높이와 전신 원점은 보존. 새 원화의 발끝 윤곽/눈 위치는 일부1px 차이가 있어 실제 전후 시트를 별도로 판단한다.',
        'generated_art_not_applied_to_game':True,'root_review_pending':True,'user_accepted':False}
(O/'registration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'output':str(O),'native_hashes':{r['key']:r['after_sha256']for r in records}}))
