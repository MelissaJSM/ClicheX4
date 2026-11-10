"""기존 16 비교판을 보존하여 녹화 시간 대응만 교정한다. 게임/원판 수정 없음."""
from pathlib import Path
import hashlib,json,math,sys,html
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;R=D.parent/'runtime'
sys.path.insert(0,str(R))
from review_recording_timeline import decode_mapping
O=D/'nana_legacy_timeline_review01';O.mkdir(exist_ok=False)
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def read(p):
 b=p.read_bytes();tracked[rel(p)]=sha(b);return json.loads(b)
impact=read(D/'runtime_webp_index_audit01/impact_list.json');helper=R/'review_recording_timeline.py';tracked[rel(helper)]=sha(helper.read_bytes())
records=[];pages=[]
for item in impact['impact_list']:
 name=Path(item['play'].replace('\\','/')).parent.name.removesuffix('_play')
 if name not in ('nana_dash12','nana_ultimate01'):continue
 play=R/(name+'_play');capture=read(play/'evidence.json');watch=read(R/(name+'_watch/evidence.json'))
 tracked[rel(play/'play.webp')]=sha((play/'play.webp').read_bytes())
 rec,im,mapping=decode_mapping(play);assert capture==rec and capture['bin_sha256']==watch['disc_sha256']
 records.append({'name':name,'source':rel(play/'play.webp'),'source_sha256':tracked[rel(play/'play.webp')],'bin_sha256':capture['bin_sha256'],'disc':watch['disc'],'old_watch':rel(R/(name+'_watch/evidence.json')),'mapping':mapping,'new_gameplay_performed':False,'new_RAM_GPU_checks_performed':False})
 sub=O/name;sub.mkdir()
 for q in item['affected_pages']:
  oldp=ROOT/q['page'].replace('\\','/');manifestp=ROOT/q['manifest'].replace('\\','/');m=read(manifestp)
  old=next(v for v in m['pages']if v['path'].replace('\\','/')==rel(oldp));ids=old['indices'];assert ids==q['capture_indices']
  tracked[rel(oldp)]=sha(oldp.read_bytes());box=old['crop'];cw,ch=box[2]-box[0],box[3]-box[1];cols=3 if name=='nana_dash12' else 4
  board=Image.new('RGB',(cw*cols,(ch+30)*math.ceil(len(ids)/cols)),'#202630');dr=ImageDraw.Draw(board);cells=[]
  for j,ci in enumerate(ids):
   ei=mapping['capture_to_encoded_frame'][ci];assert ei==q['correct_webp_indices'][j]
   im.seek(ei);right=im.convert('RGB').crop(tuple(box));im.seek(ci);wrong=im.convert('RGB').crop(tuple(box))
   # Pillow difference count avoids altering either original crop.
   import numpy as np
   d=np.any(np.array(right)!=np.array(wrong),axis=2)
   x,y=j%cols*cw,j//cols*(ch+30);board.paste(right,(x,y+30));dr.text((x+3,y+4),f'capture {ci} / webp {ei} / {capture["capture_times"][ci]:.3f}s',fill='white')
   cells.append({'capture_index':ci,'encoded_frame_index':ei,'capture_seconds':capture['capture_times'][ci],'crop_rgb_sha256':sha(right.tobytes()),'legacy_seek_rgb_sha256':sha(wrong.tobytes()),'changed_crop_pixels':int(d.sum())})
  target=sub/oldp.name;board.save(target)
  pages.append({'path':rel(target),'sha256':sha(target.read_bytes()),'original_path':rel(oldp),'original_sha256':tracked[rel(oldp)],'original_manifest':rel(manifestp),'crop':box,'capture_indices':ids,'encoded_indices':[v['encoded_frame_index']for v in cells],'cells':cells,'actual_viewed':False})
assert len(pages)==16
for p,h in tracked.items():assert sha((ROOT/p).read_bytes())==h,p
result={'scope':'과거 RN12 나나 대시6판·RN9 Ultimate10판의 시간 대응 교정. 현재 최신 원화/자원 또는 전체실기 완료로 확대하지 않는다.','method':'runtime/review_recording_timeline.py::decode_mapping 호출. 원 capture 간격의 round ms 누적과 WebP duration 구간의 exact 포함 관계를 검증한 뒤 같은 원 캡처 번호/같은 crop을 읽는다.','old_files_preserved':True,'resampled':False,'sprite_pixels_edited':False,'new_runtime_performed':False,'RAM_GPU_evidence_changed':False,'clips':records,'pages':pages,'source_files':tracked,'changed_crops':sum(c['changed_crop_pixels']>0 for p in pages for c in p['cells']),'all_selected_crops':sum(len(p['cells'])for p in pages),'visual_review_pending':True}
(O/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
body=['<!doctype html><meta charset="utf-8"><title>나나 과거 녹화 시간 교정</title><style>body{background:#17212e;color:#e9edf1;font:16px sans-serif;margin:24px}img{max-width:100%}a{color:#9dd9ff}</style><h1>나나 과거 녹화 시간 교정 16판</h1><p>당시 RN12/RN9 영상의 같은 캡처 선택을 실제 WebP 시간에 연결한 별도 보충판입니다. 기존 파일과 RAM/GPU 증거는 보존했습니다. 새 그림의 실제 게임 완료나 사용자 수용을 의미하지 않습니다.</p><a href="manifest.json">해시·시간 대응·원본 경로</a>']
for p in pages:body.append(f'<h2>{html.escape(Path(p["path"]).parent.name+" / "+Path(p["path"]).name)}</h2><img src="{html.escape(str((ROOT/p["path"]).relative_to(O)).replace(chr(92),"/"))}">')
(O/'INDEX.html').write_text('\n'.join(body),'utf8')
print(json.dumps({'pages':len(pages),'changed_crops':result['changed_crops'],'all_selected_crops':result['all_selected_crops'],'manifest_sha256':sha((O/'manifest.json').read_bytes())}))
