from pathlib import Path
D=Path(__file__).parent
s=(D/'audit_nana_ladder_relations.py').read_text('utf8')
s=s[:s.index('result =')]
s=s.replace("'nana_ladder_relations01'", "'nana_ultimate_ladder_relations01'")
s=s.replace("'nana_audit/hurt_repaint/packed_hurt_candidate_v1/PL00_U.ARC'", "'nana_audit/ultimate_return_repaint/packed_return_candidate_v1/PL02_U.ARC'")
s=s.replace('978a9fc18e31f221d20568d747078f098f37fb120c303c64afc916442721be9f','493bf2706aae33b64c4ffe70be1576a7ed63b0a4f62c54e89ca5876131392e29')
s=s.replace("(0, 1, 'base'), (15, 1, 'fourth_arm1'), (15, 2, 'fourth_arm2')", "(0, 1, 'after'), (15, 1, 'before_arm1'), (15, 2, 'before_arm2')")
s=s.replace("for row, mask in enumerate((0, 15)):", "for row, mask in enumerate((15, 0)):")
end=r'''
# 레코드 완전범위뿐 아니라 부분주소 공유도 독립 수집한다.
record_sharing=[]
for pb in PBS:
 maps={n:{p['record_offset']for p in cp(n,pb)['parts']}for n in range(cp(0,pb)['bank_frame_count'])}
 for n in REFS:
  other=[m for m,addresses in maps.items()if m not in REFS and maps[n]&addresses]
  record_sharing.append({'ref':n,'bank':pb,'non_target_overlapping_refs':other})
outside=[]
Y,X=np.indices((384,384));Y-=160;X-=160
for target_ref in(150,155):
 for source_ref in(149,154):
  for mask,form in((0,'after'),(15,'before')):
   v=np.asarray(a.composite(source_ref,mask,2)[0]);w=np.asarray(a.composite(target_ref,mask,2)[0]);m=np.any(v!=w,axis=2)
   roi=(X>=-28)&(X<=5)&(Y>=-20)&(Y<=1)
   outside.append({'source':source_ref,'target':target_ref,'form':form,'outside_broad_arm_gun_ROI':int((m&~roi).sum()),'ROI_inclusive':[-28,-20,5,1],'difference':delta(v,w)})
for name,refs in(('body_a.png',[143,144,146,149]),('body_b.png',[151,153,154,183])):sheet(name,refs)
result={'scope':'현재 나나 Ultimate 사다리14: 5층·원시 공유·반전·사격 관계 읽기. 새원화/패킹/실기 검사 아님.',
 'source':rel(SOURCE),'source_sha256':EXPECTED,'graphics_groups':groups,'frames':frames,'mirror_pairs':pairs,
 'shooting_comparisons':shotcomparisons,'shooting_outside_broad_ROI':outside,'pistol_historical_PL00_source_comparison':gunproof,
 'non_target_record_sharing':record_sharing,'original_code_evidence':[{'path':rel(p),'sha256':sha(p.read_bytes())}for p in(shotold,mirrorold)],
 'original_92_93':old['sequences'][-2:],'sheets':sheets,'actual_sheet_views':False,'producer_functions_called':False,'runtime_verified':False,
 'limits':['PL00 제작정책을 현재 PL02의 동일성으로 가정하지 않았다.','gun150/155의 역사 PL00 출처 창은 위치 비교용이다. 현재 Ultimate 실제총이 그 원화와 같다는 주장은 mismatch 수가0일 때만 가능하다.','unused_by_player5_layers는 조사된 소비범위이며 삭제허용 목록이 아니다.']}
assert SOURCE.read_bytes()==data
(OUT/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'report_sha256':sha((OUT/'report.json').read_bytes()),'groups':[{'owners':g['owners'],'tiles':g['tile_count']}for g in groups],'mirrors':[{'source':p['source'],'target':p['target'],'forms':p['forms'],'layer_changes':{k:v['expected_k_comparison']['changed_pixels']for k,v in p['layers'].items()}}for p in pairs],'shots':shotcomparisons,'outside':outside,'guns':gunproof,'non_target_record_sharing':[q for q in record_sharing if q['non_target_overlapping_refs']]},ensure_ascii=False))
'''
(D/'audit_nana_ultimate_ladder_relations.py').write_text(s+end,'utf8')
