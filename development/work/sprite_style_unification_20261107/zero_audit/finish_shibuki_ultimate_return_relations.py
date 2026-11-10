from pathlib import Path
import hashlib,json
D=Path(__file__).parent;O=D/'shibuki_ultimate_return_relations01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((O/'report.json').read_text('utf8'))
q={
 'source_sha256':r['source_sha256'],'technical_report_sha256':sha(O/'report.json'),
 'actually_viewed':[{'path':p['path'],'sha256':p['sha256']}for p in r['readbacks']],
 'findings':[
  '현재156..161은 b43e 부모와 원시·5층·조립 의미가 모두 같다. 156/157/158은 각각15/18/31타일의 서로 독립된 압축stream이다.',
  '158은 두폼 모두 해당 현재156을 y−10 이동한 색인 그림을 역사159의1875px 빛 위에 그린 것과 정확히 같다. Nana용 에너지 색상 변환은 없다. 과거 before 알파로 after를 자르는 코드가 있으나 현재 이 교집합 제한으로 바뀌는 픽셀은0이다.',
  '157의 overlay5는156 overlay5 y−1과 exact이다. 그러나 완성그림은156 y−1+Chebyshev 색9/14 테두리와 after437/before470px 다르며 몸 내부의51px도 다르다. 새156의 단순 동일 사본이라고 쓰지 않는다.',
  '157 after는 과거 normalized156 y−1+Chebyshev1/2 색9/14를 만든 다음 역사157의 overlay가 없는 영역을 역사base로 되돌리는 코드로0픽셀 오차 재현된다. before는 역사full157 전체와exact이다. 이 가림 예외는 과거 수용 그림의 출처이며 새원화에 자동 적용할 규칙으로 확대하지 않는다.',
  '156의 빈6/7/8층 레코드는0/141/142와,158의 빈6/7/8층은88/89/231/232와 공유한다.159 layer5는18과,160/161의 일부 레코드도 서로 및105/119/220과 겹친다. 새몸 패킹은 비대상 소비 타일·조립 의미를 보호해야 한다.',
  '159 전체빛은 역사18개 레코드와 소비tile0..17 전체색인을 보고서에 해시로 기록했다. 159/160/161은 새몸체로 교체할 대상이 아니다.',
  '원US EXE에서 animation3와40은 같은주소0x80119550을 사용하며156(3)→157(5)→158(2)→159(2)→160(3)→160(96,정지)의 실제바이트를 재대조했다. 숫자는 중단되지 않을 때 원호출횟수이며 실기시간 관찰이 아니다.',
  '양폼156..161 정수배 두 판을 직접 열람했다. 몸체→발광테두리→큰 빛→기둥 순서가 보이며 기존157의 머리/윤곽 색 차이는 별도 역사 파생으로 읽힌다. 새 원화의 미술 수용은 이 판에서 판단하지 않았다.'
 ],
 'next_art_policy':[
  '새156을 작성하면157의 새몸+테두리 생성 방식은 명시적인 신규 제작정책으로 정하고 루트 미술 검토를 받는다. 역사437/470색 차이를 그대로 옮겨 새머리 세부를 훼손하지 않는다.',
  '158의 역사빛 전체를 보존하며 새각폼156 y−10을 같은순서로 합성하고 원표3/40 연결을 검토한다. 새body밖빛과 순수159..161은 별도로 검사한다.'
 ],
 'new_art_or_archive_written':False,'producer_functions_called':False,'runtime_verified':False,'user_accepted':False,
 'limits':['원US의X와 현재Shibuki156..158 형상은 서로 다른 그림이다. 현재 제작 파생을 원US의 동일복사라고 주장하지 않는다.','원MIPS/GPU 실행·실제 전송장면 관찰·신규 후보 검증은 이번 읽기에 포함하지 않는다.']
}
(O/'conclusions.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'report':sha(O/'report.json'),'conclusions':sha(O/'conclusions.json'),'extra':r['historical_reconstruction']['157_overlay5_vs_current156_overlay5_yminus1']}))
