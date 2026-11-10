"""공통 독립 감사 구조에서 회전 전용 검사기를 생성한다. 자원 쓰기 없음."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'verify_riko_ceremony_independent.py').read_text('utf8')
s=s.replace('리코 등장·승리11: 원화9와 native 섬광2를 독립 재구성한다.','리코 회전8: 원화와 원래 회전 머리·검기를 독립 확인한다.')
s=s.replace('prepared_ceremony_clothes_v2','prepared_spin_clothes_v1')
s=s.replace('dd61d2f1b77cab1c43256dd6e2553f631067100338352c86aaea1d5d41eddec7','SOURCE_PLACEHOLDER')
s=s.replace('0de65ee0ee43f9c2713af4ce372023325cc2389bd42664f460ff93d2efd2a7d0','c68ef84d524a16062937359c52f9d640213b250ea2b679a673046f977d997e42')
s=s.replace('SOURCE_PLACEHOLDER','0de65ee0ee43f9c2713af4ce372023325cc2389bd42664f460ff93d2efd2a7d0').replace('ceremony_clothes16','spin_clothes17')
h0=s.index('HEAD=');h1=s.index('targets={};',h0)
s=s[:h0]+'''HEAD={};rotated={};original=render(old,1,5,161)[0];headbase=np.zeros_like(original);headbase[141:160,146:169]=original[141:160,146:169]
for j,n in enumerate(range(161,176,2)):
    q=np.array(Image.fromarray(headbase).rotate(j*45,Image.Resampling.NEAREST,center=(160.5,160)))
    assert np.array_equal(q,np.array(Image.open(D/f'head_{n:03}.png')))
    actual=render(old,1,5,n)[0];assert np.array_equal(q[q>0],actual[q>0])
    yy,xx=np.nonzero(q);HEAD[1,n]=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));rotated[n]=q
'''+s[h1:]
s=s.replace('for pn in range(1,6):','for pn in range(1,3):')
s=s.replace('head=previous[y0:y1,x0:x1];green=','head=rotated[n][y0:y1,x0:x1];green=')
b0=s.index('def flash(');b1=s.index("for r in p['registration']['frames']:",b0);s=s[:b0]+s[b1:]
s=s.replace('support={(1,n)for n in(0,1,5,9)}','support={(1,n)for n in range(162,177,2)}')
s=s.replace("if int(e['type'],16)!=2:","if int(e['type'],16)not in(2,3):")
s=s.replace('assert c==nc and bank_offsets(g)==bank_offsets(ng)','assert bank_offsets(c)==bank_offsets(nc) and bank_offsets(g)==bank_offsets(ng)')
s=s.replace("cp=composition_frame(c,b*5,n)","cp=composition_frame(nc if selected else c,b*5,n)")
s=s.replace("counts['non_target_raw']==429","counts['non_target_raw']==428")
s=s.replace("counts['non_target_display']==425","counts['non_target_display']==428")
s=s.replace("counts['target_display']==11","counts['target_display']==8")
s=s[:s.index("sp=P/")]+'''changes_parts=[];semantic=lambda cp:[(r['flags'],r['tile'],r['x'],r['y'])for r in cp['parts']]
for b in range(len(bank_offsets(c))):
    count=composition_frame(c,b,0)['bank_frame_count'];assert count==composition_frame(nc,b,0)['bank_frame_count']
    for n in range(count):
        if semantic(composition_frame(c,b,n))!=semantic(composition_frame(nc,b,n)):
            assert b==5 and n==171;changes_parts.append([b,n])
assert changes_parts==[[5,171]]
assert g[bank_offsets(g)[0]:bank_offsets(g)[1]]==ng[bank_offsets(ng)[0]:bank_offsets(ng)[1]]
sp=P/'static_effects.json';prior=(ROOT/p['source_arc']).with_name('static_effects.json');rec=json.loads(sp.read_text('utf8'));before=json.loads(prior.read_text('utf8'))
assert rec['parts_sha256']==sha(nc) and {k:v for k,v in rec.items()if k!='parts_sha256'}=={k:v for k,v in before.items()if k!='parts_sha256'}
report={'passed':True,'parent_sha256':sha(old),'candidate_sha256':sha(new),'proposal_sha256':sha((P/'proposal.json').read_bytes()),'sources':sources,'counts':counts,'changes':changes,'support_tile_windows':support_rows,'original_eight_rotated_heads_exact':True,'rotation_center':[160.5,160],'rotation_degrees':[j*45 for j in range(8)],'source_alpha_cut':128,'no_extra_halo_pixels_in_registered_output':True,'changed_composition_refs':changes_parts,'bank0_graphics_bytes_exact':True,'other_entries_exact':True,'static_recipe_only_parts_hash_rebound':True,'producer_packer_or_generation_called':False,'runtime_verified':False,'visual_review_pending':True,'frozen':False}
O=H/'riko_spin_independent';O.mkdir(exist_ok=True);(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\\n','utf8')
print(json.dumps({'passed':True,'counts':counts,'report':str(O/'verification.json')}))
'''
(H/'verify_riko_spin_independent.py').write_text(s,'utf8')
