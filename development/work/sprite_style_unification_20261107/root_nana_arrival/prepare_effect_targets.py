"""Reconnect new body art to proven native light effects without repainting effects."""
from prepare_body_targets import *
import collections
sys.path.insert(0,str(W/'nana_audit/ultimate_ceremony_repaint'))
from prepare_effect_probe import render,overlay
from scripts.c01_audio_build import read_disc
from src.psx_player import composition_frame
def main():
 td=D/'body_targets02';m=json.loads((td/'manifest.json').read_text('utf8'));parent=ROOT/m['parent_arc'];a=Archive(parent.read_bytes());assert sha(a.data)==m['parent_sha256'];out=D/'joint_targets01';out.mkdir(exist_ok=False)
 targets={(n,pb):np.array(Image.open(td/f'layer{pb}_{n:03}.png'))for n in(133,135,136,137)for pb in(0,5,6,7,8)};rules=[]
 for n in(136,137):
  ps=[p for p in composition_frame(a.c,0,n)['parts']if p['tile']==7];fx=render(a,n,ps);assert int((fx>0).sum())==46
  targets[n,0]=overlay(targets[n,0],fx)
  for pb in(5,6,7,8):targets[n,pb][fx>0]=0
  assert a.words[13]==a.words[29]==a.words[45]
  Image.fromarray(fx).save(out/f'effect_{n}.png');rules.append({'ref':n,'source_parts':ps,'rule':'원래46픽셀 빛선을원위치/색으로 최상단복원','effect_sha256':sha(fx.tobytes())})
 fx=a.layer(129)[0];assert np.array_equal(overlay(fx,a.layer(133)[0]),a.layer(134)[0])
 for pb in(0,5,6,7,8):targets[134,pb]=overlay(fx,targets[133,pb])if pb==0 else targets[133,pb].copy()
 rules.append({'ref':134,'rule':'기존129구체 뒤에 새133 각 파츠 조립','effect_sha256':sha(fx.tobytes())})
 fx131=render(a,131,composition_frame(a.c,0,131)['parts'][:16]);assert np.array_equal(fx131,a.layer(132)[0]);assert np.array_equal(np.where(a.layer(133)[0]>0,13,fx131).astype(np.uint8),a.layer(131)[0]);targets[131,0]=np.where(targets[133,0]>0,13,fx131).astype(np.uint8)
 for pb in(5,6,7,8):targets[131,pb]=np.zeros((384,384),np.uint8)
 rules.append({'ref':131,'rule':'새기본133 알파13 + 기존131 앞16개 효과,132 원raw/조립보존','effect_sha256':sha(fx131.tobytes())})
 original=ROOT/'MegaMan X4.bin';assert sha(original.read_bytes())=='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b';data,_=read_disc(original,('PL00_U.ARC',));u=Archive(data['PL00_U.ARC']);fxmap=np.array([0,5,1,10,12,9,7,5,13,9,6,1,8,7,6,5],np.uint8);orb=fxmap[u.layer(129)[0]%16];shell=fxmap[u.layer(130)[0]%16];body=np.zeros((384,384),np.uint8);body[80:240,80:240]=np.array(Image.open(ROOT/'work/ver_rin_nana/nana_art/arrival_v1/production02/frame_133.png'));old=overlay(orb,np.where(body>0,13,0).astype(np.uint8));new=overlay(orb,np.where(targets[133,0]>0,13,0).astype(np.uint8));parts=composition_frame(u.c,0,130)['parts'];cnt=collections.Counter(p['tile']for p in parts);rects=[]
 for p in parts:
  if cnt[p['tile']]>1:
   x,y=p['x']+160,p['y']+160;old[y:y+16,x:x+16]=shell[y:y+16,x:x+16];new[y:y+16,x:x+16]=shell[y:y+16,x:x+16];rects.append([x-160,y-160,x-144,y-144])
 assert np.array_equal(old,a.layer(130)[0]),'130 historical reconstruction';targets[130,0]=new
 for pb in(5,6,7,8):targets[130,pb]=np.zeros((384,384),np.uint8)
 rules.append({'ref':130,'rule':'원US129효과색상맵+새133흰실루엣;원130반복외곽창가림 보존','original_arc_sha256':sha(u.data),'color_map':fxmap.tolist(),'shell_rectangles':rects,'historical_reconstruction_exact':True})
 refs=sorted({n for n,pb in targets});frames=[];rows=[]
 for n in refs:
  ls={pb:targets[n,pb]for pb in(0,5,6,7,8)}
  for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
  frames.append({'ref':n,'layer_hashes':{str(pb):sha(z.tobytes())for pb,z in ls.items()}});rows.append((f'arrival+fx{n}',[('old base',a.composite(n)[0]),('new base',composite(a,ls,0)),('old Fourth',a.composite(n,15)[0]),('new Fourth',composite(a,ls,15))]))
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',4)
 (out/'manifest.json').write_text(json.dumps({'parent_arc':m['parent_arc'],'parent_sha256':m['parent_sha256'],'refs':refs,'unchanged_stream_partners':[132],'frames':frames,'source_body_manifest_sha256':sha((td/'manifest.json').read_bytes()),'rules':rules,'native_packed':False,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'refs':refs,'layers':len(targets),'passthrough':[132]}))
if __name__=='__main__':main()
