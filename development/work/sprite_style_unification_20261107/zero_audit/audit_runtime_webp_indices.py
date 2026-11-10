"""Runtime WebP 기록/인덱스 리뷰 영향만 읽고 보고. 원증거 수정 없음."""
from pathlib import Path
import bisect,collections,hashlib,html,json,struct
from PIL import Image
D=Path(__file__).parent;B=D.parent;ROOT=D.parents[2];R=B/'runtime';O=D/'runtime_webp_index_audit01';O.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
tracked={}
def load(p):
 b=p.read_bytes();tracked[rel(p)]=sha(b);return b
def norm(s):
 s=str(s).replace('\\','/').lower()
 while '//'in s:s=s.replace('//','/')
 return s
def chunks(data):
 assert data[:4]==b'RIFF'and data[8:12]==b'WEBP'and struct.unpack_from('<I',data,4)[0]+8==len(data)
 pos=12;out=[];start=0
 while pos<len(data):
  tag=data[pos:pos+4];size=struct.unpack_from('<I',data,pos+4)[0];raw=data[pos+8:pos+8+size]
  assert len(raw)==size
  if tag==b'ANMF':
   dur=int.from_bytes(raw[12:15],'little');out.append({'index':len(out),'timestamp_ms':start,'duration_ms':dur});start+=dur
  pos+=8+size+(size&1)
 assert pos==len(data);return out
clips=[];byname={}
for p in sorted(R.rglob('play.webp')):
 ep=p.parent/'evidence.json'
 if not ep.exists():continue
 ev=json.loads(load(ep));data=load(p);encoded=chunks(data)
 with Image.open(p)as im:nn=im.n_frames
 assert nn==len(encoded)or nn==1 and not encoded
 times=ev.get('capture_times',[]);reported=ev.get('frames');recorded=len(times)
 row={'play':rel(p),'evidence':rel(ep),'source_webp_sha256':sha(data),'recorded_frames_field':reported,'capture_times_count':recorded,'webp_frames':nn,'difference':recorded-nn,'mapping_valid':False,'reviews':[]}
 if times and encoded:
  ds=[max(1,round((b-a)*1000))for a,b in zip(times,times[1:])]+[100];starts=[];total=0
  for v in ds:starts.append(total);total+=v
  es=[x['timestamp_ms']for x in encoded];mapping=[bisect.bisect_right(es,x)-1 for x in starts]
  valid=total==sum(x['duration_ms']for x in encoded)and all(k>=0 and es[k]<=t and t+dur<=es[k]+encoded[k]['duration_ms']for k,t,dur in zip(mapping,starts,ds))and set(mapping)==set(range(nn))
  row.update(mapping_valid=valid,total_recorded_duration_ms=total,total_webp_duration_ms=sum(x['duration_ms']for x in encoded),encoded_intervals=encoded,capture_to_encoded_frame=mapping)
  row['mapping_divergent_capture_indices']=[i for i,k in enumerate(mapping)if i!=k]
  row['first_merged_capture_index']=next((i for i,k in enumerate(mapping)if i!=k),None)
 else:row['mapping_limitation']='capture_times 또는ANMF누락'
 assert reported==recorded,(p,'frame metadata mismatch')
 clips.append(row);byname[norm(p.parent.name)]=row
def sourceclip(src):
 s=norm(src)
 for key,row in byname.items():
  if s.endswith('/'+key+'/play.webp'):return row
 return None
scripts=[]
for p in sorted(list(R.glob('*.py'))+list(B.glob('review*.py'))):
 text=load(p).decode('utf8')
 if 'play.webp'in text and '.seek('in text:
  scripts.append({'path':rel(p),'sha256':sha(p.read_bytes()),'method':'timestamp_mapping'if 'capture_to_encoded_frame'in text else 'decoded_webp_timestamps'if 'timestamp'in text and ('webp_indices'in text or 'webp_timestamp_ms'in text)else 'direct_index','seek_lines':[{'line':i,'text':s.strip()}for i,s in enumerate(text.splitlines(),1)if '.seek('in s]})
manifests=[];unknown=[]
implicit_specs={
 'nana_base_rising16_review':('review_nana_rising16.py',{'normal_right':(1,1.9),'jump_right':(3.15,4.1),'normal_left':(6,6.9),'jump_left':(8.15,9.1)},1,9),
 'nana_fourth_rising16_review':('review_nana_rising16.py',{'normal_right':(1,1.9),'jump_right':(3.15,4.1),'charged_right':(7.75,8.8),'normal_left':(11,11.9),'charged_left':(14.75,15.8),'jump_left':(18.15,19.1)},1,9),
 'nana_ultimate_rising17_review':('review_nana_ultimate_rising17.py',{'normal_right':(1,1.9),'jump_right':(3.15,4.1),'charged_right':(7.75,8.8),'normal_left':(11,11.9),'charged_left':(14.75,15.8),'jump_left':(18.15,19.1)},1,9),
 'red_rin15_review':('review_red_rin15.py',{'ground_combo':(1.45,2.75),'run':(3.25,4.9),'jump_saber':(5.25,6.25),'left_combo':(6.95,8.15),'right_jump_saber':(10,11.4),'dash_jump':(12.95,14.95)},2,6),
 'shibuki_selection14_review':('review_selection14.py',{'selection':(0,2)},1,8),
}
for p in sorted(R.rglob('*.json')):
 if 'manifest'not in p.name.lower():continue
 try:j=json.loads(load(p))
 except (UnicodeError,json.JSONDecodeError):continue
 if not isinstance(j,dict):continue
 pages=j.get('pages',[])
 if not isinstance(pages,list):continue
 source=j.get('source','');linked=[]
 for page in pages:
  if not isinstance(page,dict):continue
  row=sourceclip(page.get('source',source))
  implicit=implicit_specs.get(p.parent.name)
  if row is None and implicit is not None:row=byname[p.parent.name.replace('_review','_play')]
  if row is None:continue
  claimed=page.get('source_sha256',j.get('source_sha256'))
  if claimed:assert claimed==row['source_webp_sha256'],(p,'source hash')
  pagepath=Path(str(page['path']).replace('\\','/'))
  if not pagepath.is_absolute():pagepath=ROOT/pagepath
  pagebytes=load(pagepath)
  if page.get('sha256'):assert page['sha256']==sha(pagebytes),(p,'page hash')
  ids=page.get('capture_indices',page.get('window_indices',page.get('indices',page.get('actual_frames'))))
  encoded_only=page.get('webp_indices');samples=page.get('samples')
  if implicit is not None:
   script,groups,stride,pagesize=implicit;load(B/script)
   stem=pagepath.stem;label,n=stem.rsplit('_',1);lo,hi=groups[label]
   chosen=[k for k,q in enumerate(row['encoded_intervals'])if lo<=q['timestamp_ms']/1000<=hi][::stride]
   encoded_only=chosen[int(n)*pagesize:(int(n)+1)*pagesize]
   assert encoded_only,(p,'empty implicit selection')
  if encoded_only is None and isinstance(samples,list):encoded_only=[s['webp_index']for s in samples]
  if isinstance(encoded_only,list):
   assert all(isinstance(k,int)and 0<=k<row['webp_frames']for k in encoded_only)
   expected_ms=[row['encoded_intervals'][k]['timestamp_ms']for k in encoded_only]
   recorded_ms=expected_ms if implicit is not None else [s['webp_timestamp_ms']for s in samples]if samples is not None else [round(t*1000)for t in page['actual_times']]
   assert expected_ms==recorded_ms,(p,'encoded timestamp mismatch')
   if samples is not None:assert all(s['duration_ms']==row['encoded_intervals'][s['webp_index']]['duration_ms']for s in samples)
   review={'manifest':rel(p),'page':page.get('path'),'index_method':'decoded_webp_timestamps','capture_indices':None,'used_webp_indices':encoded_only,'correct_webp_indices':encoded_only,'affected_capture_indices':[],'invalid_capture_indices':[],'out_of_range_webp_indices':[],'timestamp_ms':recorded_ms,'timestamp_values_exact':None if implicit else True,'reconstructed_from_original_review_source':rel(B/implicit[0])if implicit else None,'page_sha256_claim':page.get('sha256')}
   row['reviews'].append(review);linked.append(review);continue
  if not isinstance(ids,list)or not all(isinstance(k,int)for k in ids):
   unknown.append({'manifest':rel(p),'page':page.get('path'),'reason':'capture index field unavailable'});continue
  correct=page.get('encoded_frame_indices')
  actual=correct if isinstance(correct,list)else ids
  assert len(actual)==len(ids)
  mapping=row.get('capture_to_encoded_frame',[])
  affected=[i for i,k in zip(ids,actual)if i<len(mapping)and k!=mapping[i]]if row['mapping_valid']else None
  invalid=[i for i in ids if i<0 or i>=len(mapping)]
  out_of_range=[k for k in actual if k<0 or k>=row['webp_frames']]
  review={'manifest':rel(p),'page':page.get('path'),'index_method':'explicit_mapped_indices'if correct is not None else 'direct_capture_index_assumed_from_legacy_field','capture_indices':ids,'used_webp_indices':actual,'correct_webp_indices':[mapping[i]for i in ids]if not invalid else None,'affected_capture_indices':affected,'invalid_capture_indices':invalid,'out_of_range_webp_indices':out_of_range,'page_sha256_claim':page.get('sha256')}
  row['reviews'].append(review);linked.append(review)
 if linked:manifests.append({'path':rel(p),'sha256':sha(p.read_bytes()),'linked_pages':len(linked)})
alltexts=[]
for p in sorted(list(B.glob('root_review_checkpoint*.json'))+list(R.glob('*summary.json'))):
 alltexts.append((p,norm(load(p).decode('utf8'))))
for row in clips:
 for review in row['reviews']:
  target=norm(review['page']);projectpart=target[target.index('work/'):]if 'work/'in target else target
  review['linked_existing_reviews_or_summaries']=[rel(p)for p,t in alltexts if projectpart in t]
 row['review_page_count']=len(row['reviews']);row['affected_legacy_page_count']=sum(bool(q['affected_capture_indices'])for q in row['reviews'])
 row['corrected_mapping_page_count']=sum(q['index_method']in('explicit_mapped_indices','decoded_webp_timestamps')and not q['affected_capture_indices']for q in row['reviews'])
 row['reviewed_capture_uses']=sum(len(q['capture_indices']or[])for q in row['reviews'])
 row['affected_capture_uses']=sum(len(q['affected_capture_indices']or[])for q in row['reviews'])
 row['recording_contact_first_last_affected_by_this_bug']=False
 row['direct_review_method_status']='old source index selection not identical to capture timeline'if row['affected_legacy_page_count']else 'selected reviewed indices agree or no linked legacy review'
counts={'clips':len(clips),'different_counts':sum(q['difference']!=0 for q in clips),'valid_timeline_mappings':sum(q['mapping_valid']for q in clips),'affected_legacy_clips':sum(q['affected_legacy_page_count']>0 for q in clips),'affected_legacy_pages':sum(q['affected_legacy_page_count']for q in clips),'affected_capture_uses':sum(q['affected_capture_uses']for q in clips),'linked_review_manifests':len(manifests),'unknown_page_formats':len(unknown)}
report={'scope':'현재runtime전체play.webp+evidence/연결리뷰manifest읽기. 과거동결/리뷰/원녹화수정없음.','counts':counts,'clips':clips,'review_manifests':manifests,'review_scripts':scripts,'unknown_formats':unknown,'source_files':tracked,'findings':['ANMF chunk의정수밀리초duration을직접읽고기록capture_times의max(1,round(delta*1000))+마지막100ms합산과대조했다. 수정review_recording_timeline 함수를호출하지않은독립파서다.','프레임수차이와실제사용한리뷰인덱스영향은다르므로각page의잘못된매핑수를별도로기록했다. n_frames동일만으로원시캡처이미지동일성을추가주장하지않고전체시간구간포함도검사했다.','record contact.png/first.png/last.png는인코딩전frames배열에서직접작성되는현재recorder코드이므로이번seek버그영향대상이아니다.','RAM/GPU observer는WebP seek에의존하지않는다. 해당검증성공을취소하거나재검증하지않았다.','잘못된seek가다른시각이미지를선택해도정지장면/되풀이동작은픽셀이같을수있다.이감사는시간/인덱스매핑오류이며선택된모든사진에서미술차이를보았다는주장이아니다.'],'limits':['리뷰manifest에실제capture선택목록을기록하지않은임의수동화면열람은추적하지못한다.','기존root직접열람기록이나summary를수정/무효화하지않고연결경로만기록했다. 새시간매핑판의실제열람은별도다.'],'old_evidence_modified':False,'game_or_save_accessed':False}
report['scope']='현재 runtime의 play.webp 43개와 대응 evidence, 실제 리뷰 경로를 읽기 조사한 스냅샷. 기존 증거와 동결 파일을 수정하지 않았다.'
report['findings']=[
 'WebP ANMF의 정수 ms duration을 직접 읽어 recorder의 max(1, round(delta * 1000)) 및 마지막 100 ms와 독립 대조했다. 모든 43개에서 전체 캡처 구간의 포함 관계와 합계가 성립했다.',
 '프레임 수 차이와 실제 리뷰 영향은 다르다. 15개 녹화에 병합이 있으나, 기존 선택 번호가 어긋난 것은 4개 녹화의 21판, 선택 153회다. 중복 선택을 포함한 수이며 미술 결함 개수가 아니다.',
 'RN26 charge의 첫 매핑 차이는 capture 186이다. 기존 4판의 capture 47..65와 139..157은 그 전이므로 해당 선택에는 영향이 없다.',
 'BR13 선택은 이미 시간 기준 v2가 있고 RN30 등장도 root126의 보정 v2가 있다. Nana dash12 및 Ultimate01의 과거 두 리뷰는 당시 시간/모션 연결 근거에 한정해 재검토 필요로 남긴다. 이후 새 자원의 미술이나 현재 게임 동작을 자동으로 무효화하지 않는다.',
 '현재 recorder의 contact.png, first.png, last.png는 인코딩 전 frames 배열에서 생성한다. 이 seek 오류의 대상이 아니다.',
 'RAM/GPU 검증은 WebP seek와 독립이다. 이번 감사는 기존 검사 성공을 취소하거나 다시 실행하지 않았다.',
 '잘못된 시간 선택에서도 정지 장면이나 반복 동작의 픽셀이 같을 수 있다. 실제 모든 사진의 미술이 달랐다고 주장하지 않는다.'
]
report['limits']=[
 'manifest의 capture 번호 또는 원 리뷰 스크립트에 근거한 시간 매핑 감사다. 기존 PNG의 미술 재열람이나 각 셀의 픽셀 재합성을 수행하지 않았다.',
 '직접 capture 번호라는 설명이 없는 actual_frames 필드는 과거 선택 리뷰의 명칭상 위험으로 분리했다. 해당 BR13 판은 이미 시간 기준 v2로 대체되어 있다.',
 '사람의 수동 화면 열람 등 선택 목록이 남지 않은 경우까지 추적했다고 주장하지 않는다. nana_dash12_left_retry와 nana_ultimate_hurt19_approach는 별도 리뷰 manifest가 발견되지 않았다.',
 '이전 동결/summary의 문구를 바꾸지 않는다. 연결된 과거 근거와 새 보정판을 별도 기록한다.'
]
report['counts']['linked_pages']=sum(q['review_page_count']for q in clips)
report['impact_list']=[{'play':q['play'],'recorded_frames':q['capture_times_count'],'encoded_frames':q['webp_frames'],'first_divergent_capture_index':q['first_merged_capture_index'],'affected_pages':[r for r in q['reviews']if r['affected_capture_indices']],'available_timeline_correct_review_manifests':sorted({r['manifest']for r in q['reviews']if r['index_method']in('explicit_mapped_indices','decoded_webp_timestamps')})}for q in clips if q['affected_legacy_page_count']]
out=O/'report.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
(O/'impact_list.json').write_text(json.dumps({'report_sha256':sha(out.read_bytes()),'counts':counts,'findings':report['findings'],'impact_list':report['impact_list'],'limits':report['limits']},ensure_ascii=False,indent=2)+'\n','utf8')
rows=[]
for q in clips:
 rows.append('<tr>'+''.join('<td>'+html.escape(str(v))+'</td>'for v in (Path(q['play']).parent.name,q['capture_times_count'],q['webp_frames'],q['difference'],q.get('first_merged_capture_index'),q['review_page_count'],q['affected_legacy_page_count'],q['affected_capture_uses'],q['corrected_mapping_page_count']))+'</tr>')
(O/'INDEX.html').write_text('<!doctype html><meta charset="utf-8"><title>WebP 인덱스 리뷰 영향</title><style>body{font:15px sans-serif}td,th{padding:7px;border:1px solid #bbb}table{border-collapse:collapse}</style><h1>녹화 WebP 병합과 기존 리뷰 인덱스 영향</h1><p>과거 증거는 수정하지 않았습니다. RAM/GPU 결과와 인코딩 전 contact/first/last는 별도입니다. 새시간판의 미술 열람은 별도입니다.</p><pre>'+html.escape(json.dumps(counts,ensure_ascii=False,indent=2))+'</pre><table><tr><th>녹화</th><th>기록</th><th>WebP</th><th>차이</th><th>첫 매핑차이</th><th>리뷰판</th><th>영향판</th><th>영향 선택수</th><th>교정판</th></tr>'+''.join(rows)+'</table>','utf8')
print(json.dumps({'report_sha256':sha(out.read_bytes()),'counts':counts,'affected':[{'play':Path(q['play']).parent.name,'record':q['capture_times_count'],'webp':q['webp_frames'],'pages':q['affected_legacy_page_count'],'capture_uses':q['affected_capture_uses']}for q in clips if q['affected_legacy_page_count']],'mismatch_no_manifest':[Path(q['play']).parent.name for q in clips if q['difference']and not q['reviews']],'unknown':unknown},ensure_ascii=False))
