"""205 후보의 실제 표101/102/93 순서 비교를 준비한다."""
from pathlib import Path
D=Path(__file__).parent
s=(D/'review_rin200.py').read_text('utf8').replace('spin200_review','followthrough205_review').replace("old=(D/'prepared_ice01/PL01_U.ARC').read_bytes();new=(D/'prepared_spin01/PL01_U.ARC').read_bytes()","old=(D/'prepared_spin01/PL01_U.ARC').read_bytes();new=(D/'prepared_followthrough01/PL01_U.ARC').read_bytes()")
s=s.replace('cf0b079549ea6f1968f3eeb8be37541583f070c134a628c7ea5131fc745dee2a','d3bee17d11b9181d96395fcd0274353f78ef5f7f1bc7c8c5428e573fae3d88b8')
s=s.replace("groups={'air_spin':(100,'Air spin native 100'),'rising_start':(101,'Rising start native 101')}","groups={'rising_start':(101,'Rising start native 101'),'rising_recovery':(102,'Rising recovery native 102'),'ladder_entry':(93,'Ladder entry native 93')}")
s=s.replace('린200 원순서 검토','린205 원순서 검토').replace('린 회전·용염인 진입 비교','린 용염인 준비·회복·사다리 진입 비교')
s=s.replace('빙열참·공중회전 표는 원래 몸/이펙트 자원 참조를 나열한다.','용염인·사다리 표는 원래 몸/이펙트 자원 참조를 나열한다.')
(D/'review_rin205.py').write_text(s,'utf8')
