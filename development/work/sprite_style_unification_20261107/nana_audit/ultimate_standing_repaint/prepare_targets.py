"""새89/97 공통몸과 원83텍셀 효과로88을 별도 파생한다."""
from pathlib import Path
import json,sys,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
def shift(z,dx):
 v=np.zeros_like(z);v[:,max(dx,0):min(384,384+dx)]=z[:,max(-dx,0):min(384,384-dx)];return v
def comp(a,l,mask,arm=2):
 z=a.rgba(l[0])
 for pb,bit in((8,8),(5,1),(7,4),(6,2)):
  if mask&bit:z.alpha_composite(a.rgba(l[pb],32 if pb==7 and arm==2 else 16))
 return z
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--common',default='common_probe_v3');ap.add_argument('--out',default='targets_probe_v2');args=ap.parse_args()
 p=N/'ultimate_ladder_repaint/packed_first7_diagnostic_v1/PL02_U.ARC';need(digest(p)=='dcaf1343747fabeab3054c59fc384c3bbd598209eccb6c5a37ac84c1d340d339','고정부모');a=Archive(p.read_bytes());src=D/args.common;meta=json.loads((src/'manifest.json').read_text('utf8'))
 aud=N.parent/'zero_audit/nana_ultimate_special_relations01';report=json.loads((aud/'report.json').read_text('utf8'));need(digest(aud/'report.json')=='6c5ebd4f5b8af48b4185fe9bf27e0881651b39f91afe3c296b88001a96ec0007','효과출처');fx=np.load(aud/'effect_088_original.npy');need(fx.dtype==np.uint8 and fx.shape==(384,384) and int((fx>0).sum())==83 and set(np.unique(fx))=={0,12},'원83효과')
 original=next(q for q in report['relations']if q['archive']=='original_US'and q['source']==89 and q['target']==88);parts=original['layers']['0']['parts_target'];need(parts[6:8]==[[0,7,-19,-26],[0,8,-3,-26]],'원효과파트순서');need(parts[8]==[0,4,-26,7],'효과뒤 마지막몸파트');need(not np.any(fx[167:183,134:150]),'마지막몸파트와효과범위겹침0')
 out=D/args.out;need(out.resolve().is_relative_to(D.resolve()),'소유출력');out.mkdir(exist_ok=False);records=[];rows=[];targets={};fxmask=fx>0
 for n in(88,89,97):
  sn=89 if n==88 else n;shiftx=-1 if n==88 else 0;b=shift(np.array(Image.open(src/f'before_{sn:03}_indices.png')),shiftx);v=shift(np.array(Image.open(src/f'after_{sn:03}_indices.png')),shiftx);without_before=b.copy();without_after=v.copy()
  need(not np.any((v>0)&(b==0)),'재킷밖맨팔없음')
  if n==88:b[fxmask]=fx[fxmask];v[fxmask]=fx[fxmask]
  pc=np.array([a.words[i]!=a.words[i+16]for i in range(16)])[b];ls={0:v,5:np.where((b!=v)|pc,b,0).astype(np.uint8),6:np.zeros_like(v),7:np.zeros_like(v),8:np.zeros_like(v)}
  if n==88:
   need(np.all(v[fxmask]==fx[fxmask])and np.all(b[fxmask]==fx[fxmask]),'원효과색인')
   need(np.array_equal(v[~fxmask],without_after[~fxmask])and np.array_equal(b[~fxmask],without_before[~fxmask]),'효과밖새몸exact')
  for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
  for form,z in(('before',b),('after',v)):Image.fromarray(z).save(out/f'{form}_{n:03}_indices.png')
  for mask in range(32):
   expected=a.rgba(b,16)if mask&1 else a.rgba(v)
   for arm in(1,2):need(comp(a,ls,mask,arm).tobytes()==expected.tobytes(),'32마스크두팔')
  targets[str(n)]={str(pb):sha(z.tobytes())for pb,z in ls.items()}
  records.append({'ref':n,'source_ref':sn,'translation':[shiftx,0],'source_common_manifest_sha256':digest(src/'manifest.json'),'layers':targets[str(n)],'effect_pixels':83 if n==88 else 0,'effect_outside_body_exact':True if n==88 else None,'body_components':{'before':int(label(without_before>0,np.ones((3,3)))[1]),'after':int(label(without_after>0,np.ones((3,3)))[1])},'no_old_body_copied':True})
  rows.append((str(n),[('old before',a.composite(n,15)[0]),('new before',comp(a,ls,15)),('old after',a.composite(n)[0]),('new after',comp(a,ls,0))]))
 for i in range(0,3,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',7)
 write(out/'manifest.json',{'parent_arc':p.relative_to(ROOT).as_posix(),'parent_arc_sha256':digest(p),'refs':[88,89,97],'new_authored_body_refs':[89,97],'derived_effect_refs':[88],'targets':targets,'frames':records,'direct_rgba_combinations':192,'original_effect_source':{'report':(aud/'report.json').relative_to(ROOT).as_posix(),'report_sha256':digest(aud/'report.json'),'npy':(aud/'effect_088_original.npy').relative_to(ROOT).as_posix(),'npy_sha256':digest(aud/'effect_088_original.npy'),'pixels':83,'original_part_order':'몸6→효과2→마지막몸1.마지막몸world[-26,7,-10,23]은효과영역과겹치지않음.'},'policy':'88은새89 X−1+원효과83. 현재after의효과밖105셀등록차이는복사하지않는새공통몸체정책. 기존after정확복원이라고표현하지않음.','native_packed':False,'runtime_verified':False});print(json.dumps({'layers':15,'RGBA':192,'source_effect':83,'manifest_sha256':digest(out/'manifest.json')}))
if __name__=='__main__':main()
