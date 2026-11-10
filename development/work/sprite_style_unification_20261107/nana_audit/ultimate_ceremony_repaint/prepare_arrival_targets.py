"""등장5 새몸과130/131/134/139/141의 입증된 파생 연결을 준비한다."""
from pathlib import Path
import sys,json,collections,argparse
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint'),str(D)]
from preview_restore import Archive,digest,sha,write,need,helper
from prepare_effect_probe import render,overlay,full
from scripts.c01_audio_build import read_disc
from src.psx_player import composition_frame
PBS=(0,5,6,7,8);REFS=(130,131,133,134,135,136,137,138,139,141)
def shift(z,dy):
 v=np.zeros_like(z);yy,xx=np.nonzero(z);v[yy+dy,xx]=z[yy,xx];return v
def split(b,v):
 need(not ((v>0)&(b==0)).any(),'후폼 알파 포함');return {0:v,5:np.where((b!=v)|(b==15),b,0).astype(np.uint8),6:np.zeros_like(v),7:np.zeros_like(v),8:np.zeros_like(v)}
def composite(a,ls,mask=0,arm=2):
 im=a.rgba(ls[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
 return im
def main():
 cli=argparse.ArgumentParser();cli.add_argument('--out',default='arrival_targets_probe_v1');cli.add_argument('--settle',default=None);args=cli.parse_args()
 p=N/'ultimate_hurt_repaint/packed_hurt_candidate_v1/PL02_U.ARC';a=Archive(p.read_bytes());need(digest(p)=='c9e68442829a7f149ae86317c88172e27dbce545e454687b98310fad28ef83a5','부모');out=(D/args.out).resolve();need(out.is_relative_to(D.resolve()),'출력');out.mkdir(exist_ok=False);bd=D/'common_hands_probe_v1';body={(f,n):np.array(Image.open(bd/f'{f}_{n:03}.png'))for f in('before','after')for n in(133,135,136,137,138)};histp=ROOT/'work/overhaul_20261105/sprites/ver_rin_nana/baseline/PL02_U.ARC';h=Archive(histp.read_bytes());rules=[];effects={}
 if args.settle:
  sd=(D/args.settle).resolve();need(sd.is_relative_to(D.resolve()),'국소입력')
  for f in('before','after'):body[f,138]=np.array(Image.open(sd/f'{f}_138.png'))
  rules.append({'ref':138,'rule':'새 종아리/옆구리 국소 원화 등록.원몸체 크기/신발/권총 보호.','source_manifest':(sd/'manifest.json').relative_to(ROOT).as_posix(),'source_manifest_sha256':digest(sd/'manifest.json')})
 for n in(136,137):
  ps=[q for q in composition_frame(h.c,0,n)['parts']if q['tile']==7];fx=render(h,n,ps);need(int((fx>0).sum())==46,'흰선46');effects[n]=fx;Image.fromarray(fx).save(out/f'effect_{n:03}.png')
  for form in('before','after'):body[form,n]=overlay(body[form,n],fx)
  rules.append({'ref':n,'rule':'역사tile7의46px를원위치에최상단재합성','source_parts':ps,'effect_pixels':46,'effect_sha256':sha(fx.tobytes()),'translation':[0,0]})
 fx134=h.layer(129)[0];need(np.array_equal(overlay(fx134,a.layer(133)[0]),a.layer(134)[0]),'134부모규칙');effects[134]=fx134;Image.fromarray(fx134).save(out/'effect_134.png')
 for form in('before','after'):body[form,134]=overlay(fx134,body[form,133]);body[form,139]=shift(body[form,138],-1)
 rules.extend([{'ref':134,'rule':'새133각폼을역사129구체위에합성','effect_sha256':sha(fx134.tobytes()),'source_ref':129},{'ref':139,'rule':'역사수용Nana138→139 y−1을양폼에적용;원US 동일자세라는뜻아님','translation':[0,-1]}])
 ps=composition_frame(h.c,0,131)['parts'][:16];fx131=render(h,131,ps);need(np.array_equal(fx131,a.layer(132)[0]),'132순수효과');need(np.array_equal(np.where(a.layer(133)[0]>0,13,fx131).astype(np.uint8),a.layer(131)[0]),'131부모규칙');new131=np.where(body['after',133]>0,13,fx131).astype(np.uint8);effects[131]=fx131;Image.fromarray(fx131).save(out/'effect_131.png')
 for form in('before','after'):body[form,131]=new131.copy()
 rules.append({'ref':131,'rule':'새후폼133알파13을역사첫16energy기록위에합성.132 순수FX는raw/표시보존','effect_sha256':sha(fx131.tobytes()),'source_parts':ps,'visible_body_contribution':int((new131!=fx131).sum())})
 original,_=read_disc(ROOT/'MegaMan X4.bin',('PL02_U.ARC',));u=Archive(original['PL02_U.ARC']);relation=json.loads((ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_ultimate_ceremony_sources01/report.json').read_text('utf8'));need(sha(u.data)==relation['original_PL02_sha256'],'원USARC');fxmap=np.array([0,5,1,10,12,9,7,5,13,9,6,1,8,7,6,5],np.uint8);fx130=fxmap[u.layer(129)[0]%16];shell=fxmap[u.layer(130)[0]%16];oldbody=np.zeros((384,384),np.uint8);oldbody[80:240,80:240]=np.array(Image.open(ROOT/'work/ver_rin_nana/nana_art/arrival_v1/production02/frame_133.png'));old130=overlay(fx130,np.where(oldbody>0,13,0).astype(np.uint8));new130=overlay(fx130,np.where(body['after',133]>0,13,0).astype(np.uint8));ps=composition_frame(u.c,0,130)['parts'];counts=collections.Counter(q['tile']for q in ps);rects=[];shellmask=np.zeros_like(new130,bool)
 for q in ps:
  if counts[q['tile']]>1:
   x,y=q['x']+160,q['y']+160;old130[y:y+16,x:x+16]=shell[y:y+16,x:x+16];new130[y:y+16,x:x+16]=shell[y:y+16,x:x+16];shellmask[y:y+16,x:x+16]=True;rects.append([q['x'],q['y'],q['x']+16,q['y']+16])
 need(np.array_equal(old130,a.layer(130)[0]),'130과거규칙재현');need(np.array_equal(new130[shellmask],shell[shellmask]),'반복껍질전체창');Image.fromarray(fx130).save(out/'effect_130_background.png');Image.fromarray(shell).save(out/'effect_130_shell.png');Image.fromarray(shellmask.astype(np.uint8)*255).save(out/'effect_130_shell_mask.png')
 for form in('before','after'):body[form,130]=new130.copy()
 rules.append({'ref':130,'rule':'새후폼133알파13+원US129색상맵,원130반복shell창가림보존','source_us_arc_sha256':sha(u.data),'palette_index_map':fxmap.tolist(),'shell_windows':rects,'shell_window_sha256':sha(shell[shellmask].tobytes()),'historical_parent_reconstruction_exact':True})
 idlefull=full(a,0);old141=full(a,141);need(np.array_equal(idlefull[idlefull>0],old141[idlefull>0]),'141앞폼idle몸');dust=np.where(idlefull==0,old141,0).astype(np.uint8);need(int((dust>0).sum())==12,'입증된141먼지12');Image.fromarray(dust).save(out/'effect_141_visible_dust.png');body['before',141]=overlay(dust,idlefull);body['after',141]=overlay(dust,a.layer(0)[0]);need(np.array_equal(body['before',141],old141),'141앞폼 전체보존');dp=ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_arrival141_dust01';need(np.array_equal(dust,np.load(dp/'dust141_indices.npy')),'독립 역사 먼지12 exact');rules.append({'ref':141,'rule':'현재idle0각폼+역사tile7의6px를반전포함두기록으로그린먼지12.후폼외부추가5는구형몸체이며효과아님.','dust_pixels':12,'dust_sha256':sha(dust.tobytes()),'before_display_indices_exact':True,'independent_report':(dp/'report.json').relative_to(ROOT).as_posix(),'independent_report_sha256':digest(dp/'report.json')})
 targets={};targethash={};rows=[]
 for n in REFS:
  ls=split(body['before',n],body['after',n]);targethash[str(n)]={}
  for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png');targethash[str(n)][str(pb)]=sha(z.tobytes());targets[n,pb]=z
  for form,z in(('before',body['before',n]),('after',body['after',n])):Image.fromarray(z).save(out/f'{form}_{n:03}_indices.png')
  need(composite(a,ls,15).tobytes()==a.rgba(body['before',n],16).tobytes(),f'앞폼{n}');need(composite(a,ls,0).tobytes()==a.rgba(body['after',n]).tobytes(),f'후폼{n}');rows.append((f'arrival {n}',[('old before',a.composite(n,15)[0]),('new before',composite(a,ls,15)),('old after',a.composite(n)[0]),('new after',composite(a,ls))]))
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',5)
 write(out/'manifest.json',{'parent_arc_sha256':digest(p),'body_source_manifest':(bd/'manifest.json').relative_to(ROOT).as_posix(),'body_source_manifest_sha256':digest(bd/'manifest.json'),'historical_arc':histp.relative_to(ROOT).as_posix(),'historical_arc_sha256':digest(histp),'refs':list(REFS),'new_art_body_refs':[133,135,136,137,138],'linked_refs':[130,131,134,139,141],'rules':rules,'targets':targethash,'preserved_refs':[132,140,142,156,157,158],'scope':'5새몸체와5연동참조50층준비안.원효과원점/파생규칙을원화에연결했다.미술최종/패킹/독립/실기전.','native_packed':False,'runtime_verified':False});print(json.dumps({'refs':list(REFS),'layers':len(targets),'manifest_sha256':digest(out/'manifest.json')}))
if __name__=='__main__':main()
