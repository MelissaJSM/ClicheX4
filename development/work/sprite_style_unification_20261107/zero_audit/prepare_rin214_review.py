"""원표93 사다리베기 및104 질풍아의 실제 순서 검토."""
from pathlib import Path
D=Path(__file__).parent
s=(D/'review_rin205.py').read_text('utf8').replace('followthrough205_review','ladder_dash214_review').replace("old=(D/'prepared_spin01/PL01_U.ARC').read_bytes();new=(D/'prepared_followthrough01/PL01_U.ARC').read_bytes()","old=(D/'prepared_followthrough01/PL01_U.ARC').read_bytes();new=(D/'prepared_ladder_dash01/PL01_U.ARC').read_bytes()")
s=s.replace('d3bee17d11b9181d96395fcd0274353f78ef5f7f1bc7c8c5428e573fae3d88b8','c2ec4099740eb77cca2d37e4b0f997728e1748a35e47b45475289725ec1dd09b')
s=s.replace("groups={'rising_start':(101,'Rising start native 101'),'rising_recovery':(102,'Rising recovery native 102'),'ladder_entry':(93,'Ladder entry native 93')}","groups={'ladder_saber':(93,'Ladder saber native 93'),'ground_dash_saber':(104,'Ground dash saber native 104')}")
s=s.replace('린205 원순서 검토','린214 원순서 검토').replace('린 용염인 준비·회복·사다리 진입 비교','린 사다리 베기·질풍아 준비 비교').replace('용염인·사다리 표는','사다리 베기·질풍아 표는')
(D/'review_rin214.py').write_text(s,'utf8')
s=(D/'check_rin205_browser.py').read_text('utf8').replace('followthrough205_review','ladder_dash214_review').replace("'#group','rising_start'","'#group','ladder_saber'");(D/'check_rin214_browser.py').write_text(s,'utf8')
