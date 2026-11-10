"""독립 reader의 기존 읽기 검사 블록만 재사용한다. 제작 모듈은 호출하지 않는다."""
from pathlib import Path
D=Path(__file__).parent
s=(D/'verify_nana_base_standing3_independent.py').read_text('utf8')
prefix=s[:s.index('oldbody88=')]
prefix=prefix.replace("S=B/'root_nana_standing';T=S/'joint_layers06';P=S/'packed_standing03';O=D/'nana_base_standing3_independent01'", "S=B/'root_nana_recoil';T=S/'joint_layers02';P=S/'packed_recoil03';O=D/'nana_base_recoil2_independent01'")
prefix=prefix.replace('REFS={88,89,97}', 'REFS={90,91}')
prefix=prefix.replace("B/'root_nana_special/packed_special02/PL00_U.ARC'", "B/'nana_audit/base_settle_repaint/packed_settle_candidate_v1/PL00_U.ARC'")
prefix=prefix.replace('f2a968791b3411642a64bec9eb384a7f4b6a6d4e45be928a17b39262676f3648','15d01f06aee14e3264d7ce41d1358a530147e4a3464d3ac949b64cde5085a775')
prefix=prefix.replace('87cc15efefedd475e0de972587995ad351d3ded1bd38a5c5096d5a3ab441748e','ef69d0a13ad11ede874f2642bd9df719cbb2d864798801867b6738f728df6df4')
prefix=prefix.replace("assert meta['parent_sha256']==reg['parent_sha256']==sha(old)", "assert meta['parent_sha256']==sha(old)\nassert reg['parent_sha256']==meta['source_parent_sha256']\nsource_parent=Archive(blob(ROOT/js(S/'inputs01/manifest.json')['parent_arc']))\nassert sha(source_parent.data)==reg['parent_sha256'] and source_parent.p==a.p\nfor n in REFS:\n for pb in PBS:assert np.array_equal(a.layer(n,pb)[0],source_parent.layer(n,pb)[0])")
prefix=prefix.replace('26765dc823179faae9a24b9102fbccb9aa8d511434e784931b0245a77d3a4711','2d7bc4ab502eeb79f498f87d89cb1e5c840cc4381e7af7d531699b52dccbf9e6')
registration=r'''
donorpath=B/'nana_audit/ultimate_ceremony_repaint/packed_arrival_candidate_v1/PL02_U.ARC'
donor=Archive(blob(donorpath));assert sha(donor.data)=='c721ddee3292a88f6d1dbffb49bc79d1a82e08b3d6913cb501dc406800aa23c9'
z=donor.layer(85)[0];gm=(X>=-22)&(X<=-15)&(Y>=-11)&(Y<=-6)&np.isin(z,range(1,10))
gun=np.where(gm,z,0).astype(np.uint8);assert np.count_nonzero(gun)==20
case=np.zeros_like(gun);case[:,:-2]=gun[:,2:]
target={};proof=[];bodies={};eyes=[]
for n in sorted(REFS):
 base,fourth=registered['base',n].copy(),registered['fourth',n].copy()
 q=next(q for q in meta['source_registration']if q['ref']==n)
 if n==90:
  shared=poly([[-22,-20],[-14,-20],[-11,-13],[-14,-9],[-18,-11]])
  fourth[shared]=base[shared];weapons={'method':'새 base 사선 권총·손을 양폼 공유','polygon':q['weapon']['polygon']}
 else:
  registrations=[]
  for form,body in(('base',base),('fourth',fourth)):
   original=body.copy();skin=(X>=-22)&(X<=-17)&(Y>=-9)&(Y<=-6)&np.isin(body,(10,11,12,13))
   remove=(X>=-25)&(X<=-17)&(Y>=-13)&(Y<=-7)&((Y<=-10)|(X<=-20))&np.isin(body,range(1,10))
   body[remove]=0;visible=(case>0)&~skin;body[visible]=case[visible];body[skin]=original[skin]
   rec={'form':form,'removed':[[int(x-160),int(y-160),int(original[y,x])]for y,x in np.argwhere(remove)],'skin_preserved':int(skin.sum()),'gun_hand_contact8':int(((case>0)&binary_dilation(skin,np.ones((3,3)))).sum())}
   assert rec==next(x for x in q['weapon']['registrations']if x['form']==form)
   registrations.append(rec)
  shared=(X>=-25)&(X<=-16)&(Y>=-13)&(Y<=-5);fourth[shared]=base[shared]
  weapons={'method':'정본85 20색인 texel x−2 평행이동, 새 피부/손가림 보존','source':rel(donorpath),'translation':[-2,0],'registrations':registrations}
 source=fourth.copy();region=(Y>=8)&(Y<=22)&(X>=-18)&(X<=16);links=[]
 for y in range(168,183):
  runs=spans((source[y]>0)&region[y]);groups={}
  for gap in spans((base[y]>0)&(fourth[y]==0)&region[y]):
   assert runs
   near=min(runs,key=lambda r:np.abs(r[:,None]-gap).min());groups.setdefault((int(near[0]),int(near[-1])),[]).append(gap)
  for(l,r),gaps in groups.items():
   lo=min(l,*(int(g[0])for g in gaps));hi=max(r,*(int(g[-1])for g in gaps));dest=np.arange(lo,hi+1)
   assert max(l-lo,hi-r)<=2 and len(dest)<=max(3,2*(r-l+1))
   sx=np.arange(l,r+1)[np.rint(np.linspace(0,r-l,len(dest))).astype(int)]
   fourth[y,dest]=source[y,sx]
   links.extend({'destination':[int(x-160),y-160],'source':[int(xx-160),y-160],'index':int(source[y,xx])}for x,xx in zip(dest,sx))
 assert links==q['leg_registration']
 owner=np.full(base.shape,6,np.uint8);owner[(Y>=5)|((X>=7)&(Y>=-15))]=8
 left=[[-24,-21],[-13,-21],[-9,-12],[-3,-7],[-4,-2],[-17,-7]]if n==90 else[[-26,-14],[-15,-14],[-11,-9],[-3,-8],[-3,-2],[-16,-4],[-22,-6]]
 owner[poly(left)]=7;owner[poly([[3,-8],[12,-7],[14,6],[7,8],[3,2]])]=7
 owner[(X>=-9)&(X<=6)&(Y>=-21)&(Y<=-6)]=5
 owner[(X>=7)&(Y<=-16)]=5;owner[(X>=7)&(X<=13)&(Y>=-15)&(Y<=-9)]=5;owner[shared]=7
 full=np.where(fourth,fourth,base).astype(np.uint8)
 pd=np.array([a.words[i]!=a.words[16+i]for i in range(16)])[full]
 diff=((full!=base)|((fourth>0)&pd))&(full>0)
 ls={0:base,**{pb:np.where(diff&(owner==pb),full,0).astype(np.uint8)for pb in PBS[1:]}}
 frame=next(q for q in meta['frames']if q['ref']==n)
 for pb,v in ls.items():
  assert np.array_equal(v,png(T/f'layer{pb}_{n:03}.png'))and sha(v.tobytes())==frame['layer_hashes'][str(pb)]
  target[n,pb]=v
 assert np.array_equal(owner,png(T/f'owner_{n:03}.png'))
 for form,body in(('base',base),('fourth',fourth)):
  original=registered[form,n];mask=(original==14)&(Y<0)
  assert np.array_equal(body[mask],original[mask]);eyes.append({'ref':n,'form':form,'authored_eye_pixels_exact':int(mask.sum())})
 bodies[n]=(base.copy(),fourth.copy());proof.append({'ref':n,'weapon':weapons,'same_row_leg_links':len(links),'row_wise_max_extension':2,'owner_exact':True})
'''
technical=s[s.index('counts=collections.Counter();'):s.index('\ngroups=[]')]
technical=technical.replace('for mask in (() if n==88 else (0,15)):', 'for mask in (0,15):')
ending=r'''
headrecords=[sig(q)for q in parts(a,5,9)];assert len(headrecords)==2
head_proof=[]
for n in sorted(REFS):
 assert [sig(q)for q in parts(b,5,n)]==headrecords
 assert len({q['tile']for q in parts(b,5,n)})==2
 assert np.array_equal(render(b,n,5,parts(b,5,n)),target[n,5])
 assert not np.array_equal(target[n,5],a.layer(9,5)[0])
 assert [f['index']for f in a.banks[0]['frames']if f['offset']==a.banks[0]['frames'][n]['offset']]==[n]
 assert [f['index']for f in b.banks[0]['frames']if f['offset']==b.banks[0]['frames'][n]['offset']]==[n]
 head_proof.append({'ref':n,'same_two_records_as_parent9':headrecords,'new_head_equals_authored_target':True,'old9_bitmap_not_reused':True,'independent_stream':True,'tiles':[q['tile']for q in parts(b,5,n)]})
assert raw(a,0,9)==raw(b,0,9)
for pb in PBS:assert [sig(q)for q in parts(a,pb,9)]==[sig(q)for q in parts(b,pb,9)]and np.array_equal(a.layer(9,pb)[0],b.layer(9,pb)[0])
nativep=S/'recoil_components_native_checks.json';native=js(nativep);assert native['passed']
nr=native['resources']['PL00_U.ARC'];assert nr['candidate_sha256']==sha(new)
checks=next(q for q in nr['banks']if q['bank']==0)['native_decoder_checks']
for n in REFS:
 q=next(q for q in checks if q['frame']==n);assert q['decoded_sha256']==sha(raw(b,0,n))and q['buffer_outside_and_unused_tail_preserved']
'''
boards=s[s.index('O.mkdir(exist_ok=True);sheets=[]'):s.index("assert counts['raw_checked']==508")]
boards=boards.replace('for n in(89,97):','for n in sorted(REFS):')
tail=r'''
assert counts['raw_checked']==508 and counts['non_target_raw_exact']==506 and counts['partial_RGBA_exact']==64 and counts['target_layers_exact']==10
for path,h in tracked.items():assert sha((ROOT/path).read_bytes())==h,path
report={'passed':True,'scope':'나나 기본/포스90·91 생성 원화 재양자화→무기/같은행 다리/부분소유→실제자원 독립 읽기',
 'candidate':rel(newp),'candidate_sha256':sha(new),'parent':rel(oldp),'parent_sha256':sha(old),'target_manifest_sha256':sha((T/'manifest.json').read_bytes()),
 'counts':dict(counts),'source_quantization':quant,'source_registration':proof,'authored_eyes':eyes,'reused_head_records_only':head_proof,'parent9_raw_all_layers_all_records_exact':True,
 'nonselected_shared_compositions':shared,'other_entries_palette_audio_bank_boundaries_exact':True,
 'native_MIPS_existing_evidence':{'path':rel(nativep),'sha256':sha(nativep.read_bytes()),'two_new_decoded_hashes_match':True,'executed_here':False},
 'readback_sheets':sheets,'readback_actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'runtime_verified':False,'user_accepted':False,
 'limitations':['대상64 RGBA와 비대상1130층/1777조립/506raw를 대조했다. 제작자7296 전조합 재실행은 아니다.','원MIPS 기존결과를 현재후보 및 두 decoded hash에 결속했으며 새실행·브라우저·실기는 하지 않았다.','완료율이나 전체캐릭터 완료를 뜻하지 않는다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts)}))
'''
(D/'verify_nana_base_recoil2_independent.py').write_text(prefix+registration+technical+ending+boards+tail,'utf8')
