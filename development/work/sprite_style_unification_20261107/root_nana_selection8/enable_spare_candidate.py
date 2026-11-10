"""Version the exact packer; allow only independently enumerated unused slots."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;W=H.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
report=json.loads((W/'zero_audit/nana_selection8_capacity01/report.json').read_text('utf8'))
assert report['input']['sha256']=='a577566919c4dad695950347151ce3a57af8c3247172b04c1f36c5ec6f7101b5'
assert report['texture_bytes']==116736 and report['texture_directory']==[0,40960,90112] and not report['cross_bank_access_into_X_tail']
spares=report['unconsumed_unrestricted_UV_tiles'];assert len(spares)==28
src=W/'pack_selection_mirrors.py';s=src.read_text('utf8')
s=s.replace('bank, targets, overrides):','bank, targets, overrides, spares=()):')
needle='    free=[t for t in range(len(texture)//128) if t not in reserved]'
assert s.count(needle)==1
s=s.replace(needle,"    consumed={p['page']*256+p['tile'] for n in range(count) for p in composition_frame(original_parts,bank,n)['parts']}\n    assert set(spares).isdisjoint(consumed)\n    assert all(0<=t<len(texture)//128 and t%16!=0 and t%256>=16 for t in spares)\n    reserved-=set(spares)\n"+needle)
dest=H/'pack_selection_spares.py';assert not dest.exists();dest.write_text(s,'utf8')
p=H/'sync_standing_selection.py';s=p.read_text('utf8')
s=s.replace('from pack_selection_mirrors import repack as repack_mirrors','from pack_selection_spares import repack as repack_mirrors')
s=s.replace('DY={n:0 for n in range(1,9)}',f'DY={{n:0 for n in range(1,9)}}\nSPARES={spares!r}')
s=s.replace('repack_mirrors(texture,one,positioned,0,small,{})','repack_mirrors(texture,one,positioned,0,small,{},SPARES)')
s=s.replace('assert set(changed_tiles)<=owned','assert set(changed_tiles)<=owned|set(SPARES)')
s=s.replace("'builder_v5_guard_pending':True","'spare_slots':SPARES,'spare_slots_used':sorted(set(changed_tiles)&set(SPARES)),'native_spare_access_review_pending':True,'builder_v5_guard_pending':True")
dest=H/'sync_standing_selection_spares.py';assert not dest.exists();dest.write_text(s,'utf8')
print(json.dumps({'spares':spares,'template_sha256':sha(src.read_bytes()),'candidate_only':True}))
