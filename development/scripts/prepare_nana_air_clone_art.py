"""수용한 나나 공중 도트를 재사용하고 새 대시와 분신 소멸을 원작 슬롯에 준비한다."""
import argparse,json,sys,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,find_objects
from scripts.prepare_nana_idle_shot import INV,PILOT,write
from scripts.normalize_nana_run import quantize
from scripts.project import digest
from scripts.extract_zero import save_image
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import canvas_from_parts
from scripts.solve_sprite_cover import cover
from scripts.solve_paired_cover import paired_cover
PARENT=ROOT/'out/ver_rin_nana/nana_special_remaining_20261030T010327624138Z'
FRAMES=[93,94,*range(208,213),*range(221,231)]
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();root=ROOT/'work/ver_rin_nana/nana_art/air_clone_v1';out=args.output.resolve();source=root/'generated.png'
 if not out.is_relative_to(root)or out.exists():raise ValueError('Fresh isolated air/clone output required')
 arc=(PARENT/'modified.arc').read_bytes()
 if sha256(arc)!='c29abbd84c29e5ab2a20b1b4869a167352c3e53cc02d01c9f0bd23dd2c60aa17':raise ValueError('Parent changed')
 inv=json.loads(INV.read_text('utf8'))
 if sha256((INV.parent/'original.arc').read_bytes())!=inv['archive']['sha256']:raise ValueError('Original changed')
 es={int(e['type'],16):arc[e['offset']:e['offset']+e['size']]for e in psx_arc(arc)};bank=graphics_bank(es[2],0,allow_bank_aliases=True)
 def compose(n):
  f=bank['frames'][n];return canvas_from_parts(decode_stream(es[2],f['offset'],f['limit'],f['tile_count']*128).data,f['tile_count'],composition_frame(es[3],0,n))%16
 im=Image.open(source).convert('RGBA');lab,_=label(np.array(im.getchannel('A'))>=192);sizes=np.bincount(lab.flat);objs=[(i,(s[1].start,s[0].start,s[1].stop,s[0].stop))for i,s in enumerate(find_objects(lab),1)if sizes[i]>1000];objs.sort(key=lambda q:q[1][0])
 if len(objs)!=2:raise ValueError('Expected dash and standing calibration')
 scale=45/(objs[1][1][3]-objs[1][1][1]);pal=list(struct.unpack('<16H',(PILOT/'palette.bin').read_bytes()));rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal],np.int32);out.mkdir(parents=True)
 idx,bb=objs[0];crop=np.array(im.crop(bb));crop[lab[bb[1]:bb[3],bb[0]:bb[2]]!=idx,3]=0;crop=Image.fromarray(crop);size=(round(crop.width*scale*.9),round(crop.height*scale));v=quantize(crop,size,rgb)
 rgba=np.array(crop).astype(np.int32);r,g,b=rgba[:,:,:3].transpose(2,0,1);gm=(g>=60)&(g>r+20)&(g>b+20);votes=np.array(Image.fromarray(np.where(gm,rgba[:,:,3],0).astype(np.uint8)).resize(size,Image.Resampling.BOX));votes[size[1]//2:]=0;ey,ex=np.unravel_index(votes.argmax(),votes.shape)
 if votes[ey,ex]<8:raise ValueError('Missing green eye')
 v[ey,ex]=14;left,top=76-int(ex),66-int(ey);canvas=np.zeros((160,160),np.uint8);canvas[top:top+size[1],left:left+size[0]]=v;targets={93:compose(37),94:canvas};reuse={93:37}
 for n,src in((221,39),(223,37),(225,45),(227,47),(229,41)):
  for k in(0,1):targets[n+k]=compose(src+k);reuse[n+k]=src+k
 idle=compose(0);targets[208]=np.where(idle!=0,7,0).astype(np.uint8);targets[209]=np.where(idle!=0,8,0).astype(np.uint8)
 # 원작 소멸 빔의 중심은 캔버스 X74다. 몸 실루엣을 이 중심으로 수축한다.
 targets[210]=np.zeros_like(idle);ys,xs=np.nonzero(idle);cx=np.rint(74+(xs-74)*.45).astype(int);targets[210][ys,cx]=9
 effect_map=list(range(16))
 for old,new in((5,13),(8,9),(12,7),(13,8)):effect_map[old]=new
 for n in(211,212):targets[n]=np.array(effect_map,np.uint8)[compose(n)]
 rows={r['frame']:r for r in json.loads((root/'inventory_plan.json').read_text('utf8'))['groups']};groups=[]
 for n in(93,94,208,209,210,211,212,221,223,225,227,229):
  aliases=[k for b,k in rows[n]['aliases']];w={p['tile']for k in aliases for p in rows[k]['parts']};armor={t for k in aliases for t in rows[k]['armor_tiles']}
  if w&armor or any(k not in FRAMES for k in aliases):raise ValueError('Scope/armor conflict')
  kind='pair'if n>=221 else'effect'if n in(211,212)else'body'
  groups.append({'frame':n,'aliases':aliases,'writable':sorted(w),'kind':kind,'effect_tiles':[],'translations':{str(k):[0,0]for k in aliases},'budget':rows[n]['budget'],'tile_count':rows[n]['tile_count'],'part_slots':{str(k):[p['index']for p in rows[k]['parts']if p['tile']in w]for k in aliases}})
 for n,v in targets.items():save_image(v.tobytes(),(160,160),pal,out/f'frame_{n:03d}.png')
 art={'task':'x_nana','scope':'base_nana_air_clone_17','source':source.as_posix(),'source_sha256':digest(source),'source_inventory':INV.relative_to(ROOT).as_posix(),'parent':PARENT.relative_to(ROOT).as_posix(),'canvas_size':[160,160],'origin':[80,80],'remaining_frames':FRAMES,'groups':groups,'frames':[{'frame':n,'image':f'frame_{n:03d}.png'}for n in FRAMES],'palette_words':pal,'effect_index_mapping':effect_map,'scale':scale,'common_width_factor':.9,'per_frame_scale':False,'reused_accepted_frames':reuse,'new_dash_eye':[76,66],'clone_beam_center_x':74,'master_sha256':digest(PILOT/'nana_000_indexed.png'),'palette_sha256':digest(PILOT/'palette.bin'),'runtime_verified':False};write(out/'art.json',art)
 board=Image.new('RGB',(1080,720),'#222630');dr=ImageDraw.Draw(board)
 for i,n in enumerate([0,*FRAMES]):
  v=compose(0)if n==0 else targets[n];path=out/f'preview_{n:03d}.png';save_image(v.tobytes(),(160,160),pal,path);pic=Image.open(path).convert('RGBA').crop((50,40,110,112)).resize((180,216),Image.Resampling.NEAREST);x,y=i%6*180,i//6*240;board.paste(pic,(x,y+24),pic);dr.text((x+5,y+5),('accepted 'if n==0 else'')+str(n),fill='white')
 board.save(out/'body_review.png');layouts=[]
 for q in groups:
  if q['kind']=='effect':continue
  n=q['frame'];limit=min(len(q['part_slots'][str(n)]),len(q['writable']));result={'fits':False}
  if q['kind']=='pair':
   limitb=len(q['part_slots'][str(n+1)])
   for common in range(min(limit,limitb),1,-1):
    for rc in range(1,limit-common+1):
     sc=min(limitb-common,len(q['writable'])-common-rc)
     if sc<1:continue
     result=paired_cover(targets[n],targets[n+1],[common,rc,sc],6)
     if result['fits']:break
    if result['fits']:break
  else:result=cover(targets[n]!=0,limit,10)
  result.update(frame=n);layouts.append(result);write(out/'layout.json',layouts);print({'frame':n,'fits':result['fits'],'rects':len(result.get('rects',[]))},flush=True)
 print(json.dumps({'scale':scale,'dash_size':size,'reused':reuse}))
if __name__=='__main__':main()
