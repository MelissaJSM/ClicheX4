from pathlib import Path
D=Path(__file__).resolve().parent;s=(D.parent/'root_nana_standing/freeze_candidate.py').read_text('utf8')
pairs=[('pack_standing','pack_recoil'),('packed_standing03','packed_recoil03'),('nana_base_standing3_independent01','nana_base_recoil2_independent01'),('standing_components','recoil_components'),('root_review_checkpoint117','root_review_checkpoint121'),('cd1f54a23bc607ff18552bbec14ca312a5a8adf8da79491e886de13facc1ea3c','0f9f7687adc324eaab3692c8366558db40733df0919ef9a9ed343ff5ec7a488f'),('joint_layers06','joint_layers02'),('[88,89,97]','[90,91]'),('[89,97]','[90,91]'),('[88]','[]'),('새89/97 두 의상과88 원래X-1/83효과. 눈 양자화·새총 공통화·베일 소유06 입력. 반려01..05/pack01..02 제외.','새90/91 두 의상. 동일20texel8px총, 새상단베일 head5 소유02. 기존head9조립레코드에 새머리픽셀 보존. 반려pack01/02 제외.'),('새89/97 몸체4셀·88 원효과파생. 재현2/거부7·원MIPS/GPU·96부분조합·독립/루트시각·원표3/21스텝/506canvas 통과. 실기발동 별도, 인접90/91및138139의 세부는 후속 잔여.','새90/91 몸체4셀. 재현2/거부7·원MIPS/GPU·64부분조합·독립/루트시각·원표91/7스텝/262canvas 통과. 실기발동 별도, 전체 미술 완료 아님.')]
for a,b in pairs:
 assert a in s,a;s=s.replace(a,b)
p=D/'freeze_candidate.py';assert not p.exists();p.write_text(s,'utf8')
