"""시부키 Ultimate 비사격5의 생성7셀부터 최종25목표층까지 독립 읽기 재구성."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;W=N.parent;ROOT=W.parents[1];H=W/'shibuki_audit'
sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
PARENT='01997c949968d5a1a12d89e09c5eb46448bbcf245009feb9953e3d9e9356efd7'
FINAL='3f16886331dd693e841450cbaebc8c2c3ad226681cfb26478463481ce05048ba'
PBS=(0,5,6,7,8);CUT={221:5,223:6,225:5,227:7,229:5};INPUTS={};CHECKS=[]
def digest(v):return hashlib.sha256(v).hexdigest()
def read(p):
 v=p.read_bytes();INPUTS[p.relative_to(ROOT).as_posix()]=digest(v);return v
def js(p):return json.loads(read(p))
def arr(p):read(p);return np.array(Image.open(p))
def same(x,y,label):
 assert x.shape==y.shape and np.array_equal(x,y),label
 CHECKS.append(label)
def image(p):read(p);return Image.open(p).convert('RGBA')
def quant(pix,palette):
 # 실제표본의알파와RGB를독립계산. 동률은원팔레트순서첫불투명색.
 flat=pix[:,:,:3].reshape(-1,3).astype(np.int32);dist=np.sum((flat[:,None,:]-palette[None,1:,:])**2,axis=2);q=(1+np.argmin(dist,axis=1)).astype(np.uint8).reshape(pix.shape[:2]);q[pix[:,:,3]<128]=0;return q
def world(v,offset):
 z=np.zeros((384,384),np.uint8);z[offset:offset+v.shape[0],offset:offset+v.shape[1]]=v;return z
def dilate8(z):
 out=np.zeros_like(z);s=np.pad(z,1)
 for dy in range(3):
  for dx in range(3):out|=s[dy:dy+384,dx:dx+384]
 return out
def box(xmin,ymin,xmax,ymax):
 # inclusive world bounds
 z=np.zeros((384,384),bool);z[160+ymin:161+ymax,160+xmin:161+xmax]=True;return z
def compose(a,ll):
 im=a.rgba(ll[0]);im.alpha_composite(a.rgba(ll[5],16));return im
def main():
 assert not(D/'report.json').exists();out=D/'reconstructed';out.mkdir(exist_ok=False)
 lockp=H/'prepared_hover_ultimate01/INPUT_LOCK.json';lock=js(lockp);assert lock['parent_sha256']==PARENT and lock['candidate_sha256']==FINAL and len(lock['files'])==355
 for name,h in lock['files'].items():assert digest((ROOT/name).read_bytes())==h,name
 parentp=H/'prepared_nova_strike_ultimate01/PL02_U.ARC';parent=read(parentp);assert digest(parent)==PARENT;a=Archive(parent)
 candidate=read(H/'prepared_hover_ultimate01/PL02_U.ARC');assert digest(candidate)==FINAL
 pal={k:np.array([[((int(w)>>shift)&31)*255//31 for shift in(0,5,10)]for w in a.words[k:k+16]],np.int32)for k in(0,16)}
 generated=[];bodies={};samples={};targets={};locals=[]
 meta=js(H/'hover_ultimate_inputs01/input.json');src=H/'hover_ultimate_inputs01/generated_v1.png';im=image(src);assert im.width==im.height;whole=np.array(im.resize((192,192),Image.Resampling.NEAREST));registration=js(H/'hover_ultimate_native01/registration.json');assert digest(src.read_bytes())==registration['source_sha256']
 for f in meta['frames']:
  n=f['ref'];i=f['cell'];sample=whole[(i//2)*96:(i//2+1)*96,(i%2)*96:(i%2+1)*96];samples[n]=sample.copy();same(sample,arr(H/f'hover_ultimate_native01/{n:03}_sample.png'),f'{n} 전체192격자표본');z=world(quant(sample,pal[0]),112);same(z,arr(H/f'hover_ultimate_native01/{n:03}_indices.png'),f'{n} 생성셀직접양자화');bodies[n]=z;generated.append({'ref':n,'source':src.relative_to(ROOT).as_posix(),'source_sha256':digest(src.read_bytes()),'source_size':list(im.size),'whole_grid':[192,192],'cell':i,'native_cell':[96,96],'alpha_cutoff':128,'whole_grid_sample_exact':True,'quantization_exact':True})
 # 221첫국소: 새피부영역1픽셀팽창 + 허리의잘못남은팔범위만교체.
 for stage,ifolder,ofolder in((1,'hover221_arm_inputs01','hover221_arm_native01'),(2,'hover221_reach_inputs01','hover221_reach_native01')):
  m=js(H/ifolder/'input.json');source=H/ifolder/'generated_v1.png';im=image(source);assert im.width==im.height;sample=np.array(im.resize((128,128),Image.Resampling.NEAREST));donor=world(quant(sample,pal[0]),96);same(sample,arr(H/ofolder/'sample_rgba.png'),f'221 국소{stage} 표본');same(donor,arr(H/ofolder/'donor_indices.png'),f'221 국소{stage} 재양자화');same(bodies[221],arr(ROOT/m['source_new_body']['path']),f'221 국소{stage} 선행연결')
  z=bodies[221].copy()
  if stage==1:
   skin=np.isin(donor,[10,11,12,13])&box(1,-30,10,-4);arm=dilate8(skin)&box(0,-31,11,-3);waist=box(-1,-5,9,5);mask=arm|waist;same(arm,arr(H/ofolder/'arm_semantic_mask.png')>0,'221 첫팔 의미마스크');same(waist,arr(H/ofolder/'old_waist_arm_mask.png')>0,'221 허리 잔여팔마스크')
  else:
   roi=box(0,-31,10,-4);skin=np.isin(donor,[10,11,12,13])&roi;oldskin=np.isin(z,[10,11,12,13])&roi;mask=dilate8(skin|oldskin)&box(0,-32,11,-3);same(mask,arr(H/ofolder/'arm_semantic_mask.png')>0,'221 두번째높이 의미마스크')
  q=np.where(mask,donor,z).astype(np.uint8);same(q,arr(H/ofolder/'221_indices.png'),f'221 국소{stage} 등록전체');same(q[~mask],z[~mask],f'221 국소{stage} 보호외부');same(q!=z,arr(H/ofolder/'changed_mask.png')>0,f'221 국소{stage} 변화마스크');r=js(H/ofolder/'registration.json');assert r['changed_cells']==int((q!=z).sum());locals.append({'stage':stage,'source':source.relative_to(ROOT).as_posix(),'source_sha256':digest(source.read_bytes()),'source_size':list(im.size),'whole_grid':[128,128],'semantic_mask_cells':int(mask.sum()),'changed_cells':int((q!=z).sum()),'outside_mask_exact':True,'final_body_lower_row_source':'최종하체5는첫원화의원고정RGBA표본을CLUT16으로독립양자화.국소허리원화전체를하체로전파하지않음.'});bodies[221]=q
 # 상체는팔교정후CLUT0, 하체는최초생성RGBA의CLUT16직접양자화.
 for n in(221,223,225,227):
  upper=bodies[n].copy();upper[160+CUT[n]:]=0;lower=world(quant(samples[n],pal[16]),112);lower[:160+CUT[n]]=0;ll={b:np.zeros((384,384),np.uint8)for b in PBS};ll[0]=upper;ll[5]=lower
  for b in PBS:same(ll[b],arr(H/f'hover_ultimate_body_layers01/{n:03}_bank{b}_indices.png'),f'{n} 분할층{b}')
  targets[n]=ll
 # 229단독128셀,두팔레트독립양자화후worldY5분할.
 src=H/'hover_ultimate_inputs02/generated_v1.png';im=image(src);assert im.width==im.height;sample=np.array(im.resize((128,128),Image.Resampling.NEAREST));same(sample,arr(H/'hover_ultimate_native02/229_sample.png'),'229 단독표본');r=js(H/'hover_ultimate_native02/registration.json');assert digest(src.read_bytes())==r['source_sha256'];ll={b:np.zeros((384,384),np.uint8)for b in PBS};ll[0]=world(quant(sample,pal[0]),96);ll[5]=world(quant(sample,pal[16]),96);ll[0][165:]=0;ll[5][:165]=0
 for b in PBS:same(ll[b],arr(H/f'hover_ultimate_native02/229_bank{b}_indices.png'),f'229 분할층{b}')
 targets[229]=ll;generated.append({'ref':229,'source':src.relative_to(ROOT).as_posix(),'source_sha256':digest(src.read_bytes()),'source_size':list(im.size),'whole_grid':[128,128],'native_cell':[128,128],'world_origin':[160,160],'alpha_cutoff':128,'quantization_exact':True})
 tm=js(H/'hover_ultimate_targets01/manifest.json');assert digest((H/'hover_ultimate_targets01/manifest.json').read_bytes())==lock['target_manifest_sha256'];contact=js(H/'hover_ultimate_body5_contacts01/report.json');finalrows=[]
 for n,ll in targets.items():
  for b,z in ll.items():
   same(z,arr(H/f'hover_ultimate_targets01/{n:03}_bank{b}_indices.png'),f'{n} 최종목표층{b}');assert digest(z.tobytes())==tm['targets'][str(n)][str(b)];Image.fromarray(z).save(out/f'{n:03}_bank{b}_indices.png')
  actual=compose(a,ll);same(np.array(actual),arr(H/f'hover_ultimate_body5_contacts01/actual_{n}.png'),f'{n} body5진단그림 무변형');same(np.array(actual),arr(H/f'hover_ultimate_targets01/actual_{n:03}.png'),f'{n} 최종actual15')
  c=next(x for x in contact['frames']if x['ref']==n)
  for b,p in c['source_layers'].items():assert digest((ROOT/p['path']).read_bytes())==p['sha256']
  actual.save(out/f'actual_{n:03}.png');crop=(112,112,208,208);sheet=Image.new('RGB',(96*4*3,96*4+30),'#b7c2c8');draw=ImageDraw.Draw(sheet)
  for j,(title,pic)in enumerate((('parent actual15',a.composite(n,15)[0]),('rebuilt actual15',actual),('lower5 CLUT16',a.rgba(ll[5],16)))):
   tile=pic.crop(crop).resize((384,384),Image.Resampling.NEAREST);sheet.paste(tile,(j*384,30),tile);draw.text((j*384+5,7),f'{n} {title}',fill='black')
  sheet.save(D/f'readback_{n:03}.png');finalrows.append({'ref':n,'cut_world_y':CUT[n],'upper0_pixels':int((ll[0]>0).sum()),'lower5_pixels':int((ll[5]>0).sum()),'target_layers_exact':5,'body_contacts_output_exact':True,'index_hashes':{str(b):digest(z.tobytes())for b,z in ll.items()}})
 forbidden=('register_hover_ultimate_first','register_hover_ultimate_last','register_hover221_arm','register_hover221_reach','prepare_hover_ultimate_body_layers','prepare_hover_ultimate_targets','native_pose_pack')
 assert not any(any(x==k or x.endswith('.'+k)for k in forbidden)for x in sys.modules)
 for name,h in lock['files'].items():assert digest((ROOT/name).read_bytes())==h,name
 assert digest((H/'prepared_hover_ultimate01/PL02_U.ARC').read_bytes())==FINAL
 r={'passed':True,'scope':'시부키Ultimate 호버비사격5의생성원화7고정셀(신규몸5+221국소2)→고정양자화→의미팔교정→상체0/하체5→25목표층독립재구성.','parent_sha256':PARENT,'candidate_sha256':FINAL,'candidate_read_scope':'완성ARC해시결속만. ARC50층/사격5/GPU/원FX 검사는HUD별도reader범위.','input_lock':{'path':lockp.relative_to(ROOT).as_posix(),'sha256':digest(lockp.read_bytes()),'all_input_files_checked_unchanged':len(lock['files'])},'generated_bodies':generated,'local221':locals,'final_layers':finalrows,'assertions':CHECKS,'contact_followup':'body5_contacts의actual5와최종target actual5는독립재구성과RGBAexact. 해당후속은읽기진단이며새몸체추가변환이없음을파일/명세양쪽으로확인.','source_files':INPUTS,'quantization_method':'생성파일전체를192또는128로NEAREST.192의96셀4개와128의단독셀3개를명시된고정위치로읽고alpha128로절단.실제ARC의불투명15색RGB거리제곱최소를직접계산. sprite별bbox스케일이나옛몸덮기없음.','actually_viewed':False,'producer_functions_imported_or_called':False,'art_or_ARC_modified':False,'runtime_verified':False,'limits':['그림7셀의고정표본과양자화는직접재현했지만생성모델의생성과정자체를재현한것은아니다.','원15jet/총구/사격팔/공유stream/부분GPU/MIPS/실기검사는이보조reader범위밖.','221오른손높이1px차이등새원화의미술판단은수치exact와구분.원US손외곽exact복원주장없음.']};(D/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'source_fixed_cells':7,'layers':25,'assertions':len(CHECKS),'report_sha256':digest((D/'report.json').read_bytes())}))
if __name__=='__main__':main()
