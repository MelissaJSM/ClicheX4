"""Original executable frame order with the newly packed standing-pose pictures."""
from pathlib import Path
import sys,json,hashlib,struct,base64,io,re
import numpy as np
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
def main():
 out=D/'native_sequence01';assert not out.exists()
 data=(D/'packed_standing03/PL00_U.ARC').read_bytes();assert sha(data)=='87cc15efefedd475e0de972587995ad351d3ded1bd38a5c5096d5a3ab441748e';a=Archive(data)
 plan=read(W/'staging_rn_v25.json');src=ROOT/plan['source_bin'];assert sha(src.read_bytes())==plan['source_sha256']
 exe=read_disc(src,('SLUS_005.61',))[0]['SLUS_005.61'];load=struct.unpack_from('<I',exe,0x18)[0];at=lambda adr:int(adr,16)-load+0x800
 mp=ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/x_animations.json';meta=read(mp);seqs=[s for s in meta['animations'] if s['id'] in (91,104,105)]
 checks=[]
 for s in seqs:
  assert struct.unpack_from('<I',exe,at(meta['table_address'])+4*s['id'])[0]==int(s['address'],16)
  for q in s['steps']:
   b=exe[at(q['address']):at(q['address'])+4];assert b.hex()==q['bytes']
   duration,event,relative,frame=struct.unpack('<bbbB',b);assert (duration,event,relative,frame)==(q['duration_signed'],q['event_signed'],q['relative_step'],q['frame'])
   assert (duration&255 or 256)==q['duration_calls_uninterrupted']
  checks.append({'id':s['id'],'steps':len(s['steps']),'all_bytes_exact':True})
 out.mkdir();images={};files={};refs=sorted({q['frame'] for s in seqs for q in s['steps']})
 for form,mask in (('base',0),('fourth',15)):
  for n in refs:
   im=a.composite(n,mask)[0];cut=im.crop((112,112,208,208));assert np.count_nonzero(np.array(cut)[:,:,3])==np.count_nonzero(np.array(im)[:,:,3])
   buf=io.BytesIO();cut.save(buf,format='PNG');blob=buf.getvalue();images[f'{form}_{n}']='data:image/png;base64,'+base64.b64encode(blob).decode();p=out/f'{form}_{n:03}_native.png';p.write_bytes(blob);files[p.name]=sha(blob)
  for s in seqs:
   if s['id'] not in (91,104,105):continue
   page([(f'ID{s["id"]} p{q["position"]}: ref{q["frame"]} {q["duration_calls_uninterrupted"]}call jump{q["relative_step"]:+}',a.composite(q['frame'],mask)[0]) for q in s['steps']],a.composite(0,mask)[0],out/f'{form}_id{s["id"]}_ordered.png',cols=4,scale=4)
 template=W/'shibuki_audit/hurt_base_sequence01/REVIEW.html';html=template.read_text('utf8')
 html=re.sub(r'const DATA=.*?;const ctx=',lambda m:'const DATA='+json.dumps({'sequences':seqs,'images':images},ensure_ascii=False)+';const ctx=',html,count=1)
 html=html.replace('id:33','id:91')
 html=re.sub(r'<title>.*?</title>','<title>나나 사격 준비 원순서 검토</title>',html,count=1)
 html=re.sub(r'<h1>.*?</h1>','<h1>나나 기본·포스 사격 준비3 원표 검토</h1>',html,count=1)
 options=''.join(f'<option value="{s["id"]}">원표 {s["id"]}</option>' for s in seqs)
 html=re.sub(r'<select id="anim">.*?</select>','<select id="anim">'+options+'</select>',html,count=1)
 paragraphs=iter(['왼쪽 기본·오른쪽 포스. 실제 EXE 표91/104/105의 순서·분기·유지 호출수로 새 그림을 연결한 표시 시뮬레이션입니다.60호출/초는 검토 가정입니다. 호버/특수 기술 물리 이동·입력·외부 상태·발사체는 재현하지 않습니다.','89/97의 새 그림과88의 원래X-1 및83개 광선 픽셀을 보존합니다.85 및90..92는 부모 그림이며 다른 연결 자세는 이전 검증본입니다. 표의 자기분기는 화면 유지로 표시합니다.'])
 html=re.sub(r'<p>(.*?)</p>',lambda m:'<p>'+next(paragraphs)+'</p>',html)
 (out/'REVIEW.html').write_text(html,'utf8')
 report={'candidate_sha256':sha(data),'source_bin':plan['source_bin'],'source_bin_sha256':plan['source_sha256'],'exe_sha256':sha(exe),'metadata':{'path':mp.relative_to(ROOT).as_posix(),'sha256':sha(mp.read_bytes())},'template_sha256':sha(template.read_bytes()),'native_step_checks':checks,'sequences':seqs,'native_pngs':files,'display_crop':{'size':[96,96],'origin':[48,48],'all_pixels_inside':True},'native_table_bytes_verified':True,'preview_call_rate_assumption':60,'dynamic_timer_93_reproduced':False,'external_state_or_physics_reproduced':False,'continuous_animation_actually_watched_by_model':False,'runtime_verified':False}
 (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sequences':len(seqs),'steps':sum(len(s['steps']) for s in seqs),'native_images':len(images)}))
if __name__=='__main__':main()
