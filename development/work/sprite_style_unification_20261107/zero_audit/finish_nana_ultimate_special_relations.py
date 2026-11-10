from pathlib import Path
import hashlib,json,numpy as np
from PIL import Image
D=Path(__file__).parent;ROOT=D.parents[2];O=D/'nana_ultimate_special_relations01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
j=json.loads((O/'report.json').read_text('utf8'))
assert sha(O/'report.json')=='6c5ebd4f5b8af48b4185fe9bf27e0881651b39f91afe3c296b88001a96ec0007'
norm=ROOT/'work/overhaul_20261105/sprites/nana_preultimate/normalized'
pairs=[]
for s,t in ((95,96),(98,99)):
 a=np.array(Image.open(norm/f'{s:03}.png'));b=np.array(Image.open(norm/f'{t:03}.png'));a=np.roll(a,1,axis=1)
 pairs.append({'source':s,'target':t,'historical_normalized_after_changed':int((a!=b).sum()),'alpha_changed':int(((a>0)!=(b>0)).sum())})
out={'source_report_sha256':sha(O/'report.json'),'current_sha256':j['current_sha256'],
 'original_vs_current':[q for q in j['relations']if q['archive']in('original_US','current')],
 'historical_normalized_pairs':pairs,
 'conclusions':[
 '원US PL02의95→96·98→99는5층과완성두폼에서x+1 exact다. 현재Nana before도완성그림x+1 exact지만after는각118픽셀/alpha20 및117픽셀/alpha25가다르다. 원작관계와현재after의픽셀동일성을구분해야한다.',
 '현재after 98/99는역사overhaul normalized PNG와각각exact다. 그정규화의별도special_00셀등록단계부터117픽셀차이가존재하며원게임의별도반동명령근거가아니다. 95/96도역사정규화에118픽셀차이가있다. 이후각36픽셀후속변경은현재읽기에서발생원인을완전히추적하지않았으나before/after양쪽과쌍에같이존재해현재x+1차이수치를바꾸지않는다.',
 '95after 차이bbox[-10,-17,17,0)는턱/어깨·몸통·뒤머리쪽,98after 차이bbox[-16,-6,19,12)는팔/몸통·골반쪽이다. 이두관계의차이를별도효과라고보존할근거는없다. 원작의공통몸체x+1을새원화정책으로채택할수있으나현재after원형exact복원이라고표현하지않는다.',
 '88의원US효과는tile7/8 두전체타일,파트6/7의83불투명색인12이며실제조립은몸6파트→효과2파트→마지막몸1파트다. 현재before는89x−1과효과영역안55셀만다르고밖몸체exact다. 원83중28은현재전폼몸/overlay에가려지거나동일색으로덮여있으므로화면의55셀과원효과83셀을같은수치로취급하지않는다.',
 '현재after88은89x−1대비163셀다르고그중105셀은원효과83좌표밖몸체차이다. 이를전부charge효과로추출하면몸통·머리·의상표본이섞인다. 독립저장effect_088_original.npy와원두전체타일·그리기순서를출처로삼고새몸체가림정책을별도로명시한다.',
 '현재88/89,95/96,98/99는각서로만raw공유이며97은독립이다. 빈6/7/8을포함한조립레코드타참조공유목록은report.frames.layers.record_owners를보호한다. 실제그림공통과raw공유는서로다른조건이다.',
 '기존원PS1바이트읽기근거를재사용했다. 그림95/96은표95/96과복제체표97(ref96)에,그림97/98/99는표104/105에연결된다. 표91은85→86→88→89→90→91→92라새89를만들때88몸체파생과90/91후속을따로검토해야한다. 원표95/96의138139,104/105의81도연결범위다.',
 '같은표가서로다른폼의layer표시를선택할뿐현재118/117셀차이를생성하는별도코드근거는없다. 이번조사는EXE읽기기존근거재사용/자원독립읽기이며실행·패킹·아트변경은없다.'
 ],'actually_viewed':j['boards'],'visual_observations':[
 'before/after의평행이동비교두판을실제열람했다. before95/96과98/99는정렬후동일하고after는상의경계·뒤머리/팔·골반음영차이가보인다.',
 '88원효과위치와after몸통의차이를분홍진단표시로분리해확인했다. 이판으로새원화품질수용이나실기통과를주장하지않는다.'
 ],'limits':['95/96의역사정규화이후각36셀변경의정확제작단계는이읽기범위에서미확인.','이번읽기는최신특수후보제작전동결부모dcaf/493bf의관계다. 새89/97등록은검사하지않았다.'],
 'producer_functions_called':False,'gameplay_verified':False,'new_native_execution':False}
(O/'conclusions.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'report':sha(O/'report.json'),'conclusions':sha(O/'conclusions.json'),'normalized_pairs':pairs}))
