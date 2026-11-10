from pathlib import Path
D=Path(__file__).resolve().parent;S=D.parent/'root_nana_shot85'
s=(S/'freeze_candidate.py').read_text('utf8')
for a,b in [('import pack_shot','import pack_settle'),('packed_shot01','packed_settle01'),('nana_base_shot2_independent01','nana_base_settle87_92_independent01'),('root_review_checkpoint137','root_review_checkpoint138'),('0d1849fed1565602ea6860437debdc2d3b660262cdc53f7464b9e045107a3e5e','b8832490d86f21e4a46b5efb3a0b9b7e793da21551272e0f4b87a48e1e069261'),('shot_components','settle_components'),('c9a43669cde78ee2747dd0e467baec410cbb38084226d73dc65dff79f0442a37','ab899d91a95b290b8afa5bcd9fcf9afe4e278c40d6b9de15bcc3c8b2f675dcd6'),('joint_targets03','joint_targets02'),('새85/86 네 의상셀. 정본 사랑이20셀(86은 피부1셀 가림), 새손·얼굴·다리와 joint03 베일소유. 옛joint01/02 최종입력 제외.','새87/92 네 의상셀. 새손·얼굴공유와 같은행 다리등록, joint02 베일소유. 92의 떠있던1셀을 가진joint01은 최종입력 제외.'),('[85,86]','[87,92]'),('정본 총구·홍채·발 높이','홍채·몸체전체높이·발 높이'),("ind/'visual_review.json'","ind/'visual.json',ind/'READER_INPUT_LOCK.json'"),('재현2/거부7','재현1/거부7')]:
 assert a in s,a;s=s.replace(a,b)
p=D/'freeze_candidate.py';assert not p.exists();p.write_text(s,'utf8')
