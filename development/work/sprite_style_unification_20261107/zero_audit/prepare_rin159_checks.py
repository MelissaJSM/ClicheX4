"""Bind the frozen previous audit pattern to the new five-reference candidate."""
from pathlib import Path
import json
D=Path(__file__).parent;R=D/'rin_extension';P=R/'prepared_air_saber01';j=json.loads((R/'rin154_components.json').read_text('utf8'));sha='2be858c073b05568f1b7d83b98e62b4f94a71899ae09a078cc0c3083e85c3a11'
j['resources']['PL01_U.ARC'].update(path=str(P/'PL01_U.ARC'),after=sha)
(R/'rin159_components.json').write_text(json.dumps(j,indent=2)+'\n','utf8')
s=(D/'verify_rin154_readback.py').read_text('utf8').replace('prepared_ground_remaining_v1','prepared_air_saber01').replace('after141_registered_v2','air_saber_registered_v1').replace('prepared_ground_wall_v1','prepared_ground_remaining_v1')
s=s.replace('247b47bcbf91eea64697305ba5a705de02207682c46fbbab0b527f9df00d6bb6','a8a268fa92912678e70b01b776ffa477dd46c16e791f16f3346c76cd55016319')
s=s.replace("assert sha(new)=='a8a268fa92912678e70b01b776ffa477dd46c16e791f16f3346c76cd55016319'",f"assert sha(new)=='{sha}'")
start=s.index('mapping=');end=s.index('targets={}',start);s=s[:start]+"mapping={(0,n):(0,n)for n in[213,215,217,219]};mapping[1,160]=(0,213)\n"+s[end:]
s=s.replace("support={(0,n)for n in(84,86,88,90,92,94,106,108)}","support={(0,n)for n in(214,216,218,220)}")
s=s.replace("op['polygon']","op.get('polygon',op.get('new_hand_forearm_polygon'))")
s=s.replace("r['old_body_or_head_override']","r['old_head_or_body_override']")
s=s.replace("counts['authored_exact']==13 and counts['other_display_exact']==423","counts['authored_exact']==5 and counts['other_display_exact']==431")
s=s.replace('rin154_components_native_checks','rin159_components_native_checks').replace('final154_readback_audit','final159_readback_audit')
s=s.replace("'cumulative_authored_refs':154,'incremental_refs':13,'previous141_preserved':True","'cumulative_authored_refs':159,'incremental_refs':5,'previous154_preserved':True")
(D/'verify_rin159_readback.py').write_text(s,'utf8')
g=(D/'check_rin154_guards.py').read_text('utf8').replace('pack_rin_after141','pack_rin_air_saber01').replace('rin154_guard_checks','rin159_guard_checks')
g=g.replace("('parent_hash','missing83','extra147','bad_palette','altered130','changed_saber84','wrong_alias93','changed_prior62')","('parent_hash','missing213','extra147','bad_palette','altered219','changed_saber214','wrong_alias160','changed_prior62')")
g=g.replace('missing83','missing213').replace('t[0,83]','t[0,213]').replace('t[0,85]','t[0,215]').replace('altered130','altered219').replace('t[0,130]','t[0,219]').replace('changed_saber84','changed_saber214').replace('t[0,84]','t[0,214]').replace('wrong_alias93','wrong_alias160').replace('t[0,93]','t[1,160]')
# The wrong alias must differ from its original master213.
g=g.replace("elif case=='wrong_alias160':t[1,160]=t[0,213].copy()","elif case=='wrong_alias160':t[1,160]=t[0,215].copy()")
(D/'check_rin159_guards.py').write_text(g,'utf8')
print(P)
