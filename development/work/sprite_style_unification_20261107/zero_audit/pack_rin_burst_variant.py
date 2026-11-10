"""New184/185 art, joint native ownership, no hidden-data cleanup."""
from pathlib import Path
import sys,json,hashlib
D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_priority_body as core
core.P=D/'rin_extension/prepared_priority_final_v2/PL01_U.ARC'
core.SHA='3536c3773f3a1a8da48e948b64c556986d2b3a51c7592baf4930b07b837b198d'
core.ART=D/'rin_extension/burst_variant185_01/native'
core.OUT=D/'rin_extension/prepared_burst_pair_main_v1'
core.MAP={(1,184):('b1_185',False),(1,185):('b1_185',False)}
if __name__=='__main__':
 p=core.ART/'b1_185_indices.png';core.EXPECTED_SHA={'b1_185':'85871ee3c0804c886b6ea80134e949a97f5bc23edb9dc7c411b8c7246d96ac21'}
 # Exact authored source is pinned together with the registered source.
 meta=json.loads((core.ART/'registration.json').read_text('utf8'))
 assert meta['source_art_sha256']=='519584a9898e388798652ad5bdf95f205d0720324dfc5dedbdad68a0fa0808f4'
 assert hashlib.sha256((core.ART.parent/'generated.png').read_bytes()).hexdigest()==meta['source_art_sha256']
 core.main();p=core.OUT/'proposal.json';j=json.loads(p.read_text('utf8'));j['cumulative_main_refs']=52;j['victory5_included']=True;j['verification'].pop('previous42_exact',None);j['verification']['previous50_exact']=True;j['user_accepted']=False;j['root_review_only']=True;j['static_burst23_sync_required']=True;j['static_burst24_sync_required']=False;j['registration']=str((core.ART/'registration.json').relative_to(core.ROOT));j['art_png_sha256']=core.EXPECTED_SHA['b1_185'];p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
