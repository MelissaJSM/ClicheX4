from pathlib import Path
D=Path(__file__).parent
s=(D/'verify_shibuki_ultimate_victory4_independent.py').read_text('utf8')
head=s[:s.index('body={};sources=[]')]
head=head.replace('from scipy.ndimage import label','from scipy.ndimage import label,binary_dilation')
head=head.replace('raw,parts,sig,tile,color,polygons','raw,parts,sig,tile,color,polygons,render')
head=head.replace("P=H/'prepared_ultimate_victory01';T=H/'ultimate_victory_targets01';O=D/'shibuki_ultimate_victory4_independent01'", "P=H/'prepared_ultimate_return01';T=H/'ultimate_return_targets01';O=D/'shibuki_ultimate_return3_independent01'")
head=head.replace('REFS={204,205,206,207}','REFS={156,157,158}')
begin=head.index('def shift(');end=head.index('a,b=Archive(old)',begin)
head=head[:begin]+'''def shift(z,dy,dx=0):
 out=np.zeros_like(z);y,x=np.nonzero(z);assert np.all((y+dy>=0)&(y+dy<384)&(x+dx>=0)&(x+dx<384));out[y+dy,x+dx]=z[y,x];return out
oldp=H/'prepared_ultimate_victory01/PL02_U.ARC';newp=P/'PL02_U.ARC'
old,new=readb(oldp),readb(newp)
assert sha(old)=='ec7a6847ec8de42a3b25c1d0b87fdc96330bc61488c2296426ab24cbe9cfa9b8'
assert sha(new)=='f40f33969d488af9db8c7d99b6bf4a78ad6e5542883bff63116fa26778de4cdc'
'''+head[end:]
source=r'''
fixed={};source_proof=[]
for srcdir,nativedir in(('ultimate_return_inputs01','ultimate_return_native01'),('ultimate_return_arm_edit02','ultimate_return_arm_native02')):
 source=H/srcdir/'generated.png';rp=H/nativedir/'report.json';rm=readj(rp)
 assert sha(readb(source))==rm['source_sha256'];im=Image.open(source).convert('RGBA');assert im.size==(1536,1024)
 samples=np.array(im.resize((192,128),Image.Resampling.NEAREST));pair={}
 for i,(form,start)in enumerate((('before',16),('after',0))):
  cell=samples[:,i*96:(i+1)*96];pal=rgb[start:start+16];small=(1+((cell[:,:,:3].astype(np.int32)[:,:,None]-pal[None,None,1:])**2).sum(3).argmin(2)).astype(np.uint8);small[cell[:,:,3]<128]=0
  v=np.zeros((384,384),np.uint8);v[96:224,112:208]=small
  assert np.array_equal(v,png(H/nativedir/f'{form}_156_indices.png'))
  row=next(q for q in rm['rows']if q['form']==form);assert sha(v.tobytes())==row['index_array_sha256'];pair[form]=v
 fixed[srcdir]=pair;source_proof.append({'generated':rel(source),'sha256':sha(source.read_bytes()),'fixed_1_over8_nearest_palette_exact':True,'forms':2})
src=fixed['ultimate_return_inputs01'];donor=fixed['ultimate_return_arm_edit02'];cm=readj(H/'ultimate_return_contacts02/report.json')
assert cm['before_to_after_lut']==lut.tolist()
arms=((xx<=-4)|(xx>=5))&(yy>=-3)&(yy<=5);bodies={f:z.copy()for f,z in src.items()}
for f in bodies:bodies[f][arms]=donor[f][arms]
hairtip=(xx==11)&(yy==5);assert src['before'][165,171]==src['after'][165,171]==2;bodies['before'][hairtip]=src['before'][hairtip]
unmoved=bodies['before'].copy();left=(xx>=-5)&(xx<=0)&(yy>=16)&(yy<=21);right=(xx>=1)&(xx<=6)&(yy>=16)&(yy<=21)
bodies['before'][left|right]=0
for mask,dx,dy in((right,0,-1),(left,1,1)):
 y,x=np.nonzero(mask&(unmoved>0));bodies['before'][y+dy,x+dx]=unmoved[y,x]
seam=(xx>=-4)&(xx<=0)&(yy==16);bodies['before'][seam]=unmoved[seam]
headmask=yy<=-4;hair=(yy>=6)&(yy<=12)&((xx<=-6)|(xx>=6));legs=(yy>=9)&(xx>=-5)&(xx<=6);hands=((xx<=-11)|(xx>=12))&(yy>=-2)&(yy<=3);common=headmask|hair|legs|hands
bodies['after'][common]=lut[bodies['before']][common]
for name,m in(('arms_donor',arms),('first_new_hair_tip',hairtip),('left_ankle_module',left),('right_ankle_module',right),('left_join_row',seam),('head',headmask),('hair',hair),('legs',legs),('hands',hands),('common',common)):
 assert np.array_equal(m,png(H/'ultimate_return_contacts02'/f'{name}_mask.png')>0)
for form,z in bodies.items():
 assert np.array_equal(z,png(H/'ultimate_return_contacts02'/f'{form}_156_indices.png'))and label(z>0,np.ones((3,3)))[1]==1
 torso=(xx>=-3)&(xx<=4)&(yy>=-3)&(yy<=8);assert np.array_equal(z[torso],src[form][torso])
assert not ((bodies['after']>0)&(bodies['before']==0)).any()
assert np.array_equal(bodies['before'][headmask],src['before'][headmask])
energy=a.layer(159)[0];assert np.count_nonzero(energy)==1875 and sha(energy.tobytes())=='5940e1569783b6638ec8b6ac868a7537dfc234c7337ab68cfff68e7fcba1d02a'
assert np.array_equal(energy,png(T/'historical159_indices.png'))
body={};effects=[]
for form,z in bodies.items():
 body[form,156]=z;moved=shift(z,-1);m=moved>0;inner=binary_dilation(m,np.ones((3,3)));outer=binary_dilation(m,np.ones((3,3)),iterations=2)
 body[form,157]=np.where(m,moved,np.where(inner,9,np.where(outer,14,0))).astype(np.uint8)
 moved=shift(z,-10);body[form,158]=np.where(moved>0,moved,energy).astype(np.uint8)
 assert np.array_equal(moved,png(T/f'{form}_158_body_indices.png'))
 effects.append({'form':form,'157_new_Chebyshev9_14':int((body[form,157]>0).sum()-(z>0).sum()),'158_source_energy_pixels':1875,'158_visible_energy_pixels':int(((energy>0)&(moved==0)).sum()),'158_body_not_recolored':True})
target={}
for n in sorted(REFS):
 bef,aft=body['before',n],body['after',n]
 equal=np.all(color(a,bef,16)==color(a,aft),axis=2)
 target[n,0]=aft;target[n,5]=np.where(equal,0,bef).astype(np.uint8)
 for pb in(6,7,8):target[n,pb]=np.zeros_like(aft)
 for pb in PBS:assert np.array_equal(target[n,pb],png(T/f'{n:03}_bank{pb}_indices.png'))and sha(target[n,pb].tobytes())==meta['targets'][str(n)][str(pb)]
 for form in('before','after'):assert np.array_equal(body[form,n],png(T/f'{form}_{n:03}_indices.png'))
'''
tech=s[s.index('counts=collections.Counter();'):s.index('O.mkdir(exist_ok=True);sheets=[]')]
end=r'''
energy_records=parts(a,0,159);actual_records=parts(b,0,158)
assert len(energy_records)==18 and len(actual_records)==24
assert [sig(q)for q in actual_records[:18]]==[sig(q)for q in energy_records]
assert np.array_equal(render(b,158,0,actual_records[:18]),energy)
assert np.array_equal(render(b,158,0,actual_records[18:]),shift(bodies['after'],-10))
preserved_tiles=[]
assert a.banks[0]['frames'][159]['tile_count']==19
for t in range(19):
 assert np.array_equal(tile(a,159,t),tile(b,158,t));preserved_tiles.append({'tile':t,'whole_256_nibbles_sha256':sha(tile(a,159,t).tobytes())})
assert not tile(b,158,18).any()
for n in(159,160,161):
 assert raw(a,0,n)==raw(b,0,n)
 for pb in PBS:assert [sig(q)for q in parts(a,pb,n)]==[sig(q)for q in parts(b,pb,n)]and np.array_equal(a.layer(n,pb)[0],b.layer(n,pb)[0])
nativep=H/'ultimate_return_components_native_checks.json';native=readj(nativep);assert native['passed'];nr=native['resources']['PL02_U.ARC'];assert nr['candidate_sha256']==sha(new)
checks=next(q for q in nr['banks']if q['bank']==0)['native_decoder_checks']
for n in REFS:
 q=next(q for q in checks if q['frame']==n);assert q['decoded_sha256']==sha(raw(b,0,n))and q['buffer_outside_and_unused_tail_preserved']
O.mkdir(exist_ok=True);sheets=[]
for n in sorted(REFS):
 pics=[(f'{n} {caption}',ar.composite(n,mask)[0])for ar,mask,caption in((a,15,'old before'),(b,15,'new before'),(a,0,'old after'),(b,0,'new after'))]
 boxes=[im.getbbox()for _,im in pics];box=(min(q[0]for q in boxes)-3,min(q[1]for q in boxes)-3,max(q[2]for q in boxes)+3,max(q[3]for q in boxes)+3)
 w,h=box[2]-box[0],box[3]-box[1];cw,ch=w*4+10,h*4+26;board=Image.new('RGB',(cw*4,ch),'#263345');dr=ImageDraw.Draw(board)
 for k,(caption,im)in enumerate(pics):
  x=k*cw;dr.text((x+4,4),caption,fill='white');v=im.crop(box).resize((w*4,h*4),Image.Resampling.NEAREST);board.paste(v,(x+4,22),v)
 p=O/f'readback_{n}.png';board.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'no_clipping':True})
assert counts['raw_checked']==512 and counts['non_target_raw_exact']==509 and counts['target_layers_exact']==15 and counts['non_target_layers_exact']==1125 and counts['partial_RGBA_exact']==96
for p,h in tracked.items():assert sha((ROOT/p).read_bytes())==h,p
report={'passed':True,'scope':'시부키 Ultimate 귀환3 새원화2+국소팔2 고정등록→접점·공통부→새테두리/역사광선→15층 독립 재구성',
 'candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'target_manifest_sha256':sha((T/'manifest.json').read_bytes()),'source_lock_sha256':sha((P/'SOURCE_LOCK.json').read_bytes()),'locked_inputs':len(lock['files']),
 'counts':dict(counts),'source_reconstruction':source_proof,'source_pose_registration':{'local_arm_region':{'world_x':'x<=-4 or x>=5','world_y_inclusive':[-3,5]},'left_ankle_translation':[1,1],'right_ankle_translation':[0,-1],'left_join_row_preserved':16,'before_head_first_new_source_exact':True,'torso_both_first_new_source_exact':True,'after_common_parts_from_new_before':True,'wholebody_scaling':False},
 'effect_policy':effects,'157_historical_occlusion_exception_reused':False,'158_whole19_storage_tiles':preserved_tiles,'158_original_effect18_records_prefix_exact':True,'158_new_body6_records_follow_effect':True,'pure_effect159_160_161_preserved':True,
 'old_shared_non_target_compositions':shared,'other_entries_audio_palette_bank_boundaries_exact':True,'part_counts':{str(n):{str(pb):len(parts(b,pb,n))for pb in PBS}for n in sorted(REFS)},
 'existing_native_evidence':{'path':rel(nativep),'sha256':sha(nativep.read_bytes()),'three_decoded_hashes_bound':True,'executed_here':False},
 'readback_sheets':sheets,'readback_actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'runtime_verified':False,'user_accepted':False,
 'limitations':['원MIPS·브라우저·실기는 새로 실행하지 않았다.','대상96 RGBA와1125비대상층/509raw/1776조립 보존을 검사했으며 전체폼 완료율이 아니다.','157은 새156에 적용한 신규테두리정책이며 옛가림 예외의 동일복원이 아니다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(counts),'report_sha256':sha((O/'report.json').read_bytes())}))
'''
(D/'verify_shibuki_ultimate_return3_independent.py').write_text(head+source+tech+end,'utf8')
