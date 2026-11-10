"""기존 검증된 원표 재생기를 새 후보 전용 파일로 복제한다. 기존 파일은 보존."""
from pathlib import Path
H=Path(__file__).resolve().parent
def main():
    src=(H/'review_nova_ultimate_preparation.py').read_text('utf8')
    src=src.replace('nova_ultimate_sequence01','nova_strike_ultimate_sequence01').replace('prepared_nova_ultimate01','prepared_nova_strike_ultimate01').replace('687fb27b10b9a7c13dd6d0c9fd6976dbb04f88f9b3b775f3d33482ebb7efb86f','01997c949968d5a1a12d89e09c5eb46448bbcf245009feb9953e3d9e9356efd7').replace('sprite_style_unification_20261107_v26','sprite_style_unification_20261107_v28').replace('b99860d4a87e8b152d2476ea65851583eb01d7978f9b97488a8d88ad7b536f27','13d52f8be48ef29962dd78fc94f236897d216ef6c56f39406bb2bb67bbea5c77')
    line=next(x for x in src.splitlines()if "d/f'{form}_preparation_order.png'"in x)
    src=src.replace(line,line+'\n'+line.replace("s['steps'][:5]","s['steps'][4:]").replace('preparation_order','strike_order').replace('scale=4','scale=3'))
    src=src.replace('213..216만 새 원화이며217..220은 부모를 보존했습니다.','213..216은 앞선 동결 원화입니다.217/218/220은 새 맨팔 몸체,219는 새 몸 실루엣입니다.218 현재3효과점은 그대로이고220의 새몸 가림93셀은 별도 제작정책입니다.').replace('노바 준비4와 기존 효과 연결','노바 준비와 새 돌진몸·효과 연결')
    src=src.replace("'new_art_steps':4","'new_art_steps':sum(q['frame']>=217 for q in s['steps'])").replace("'new_refs':[213,214,215,216]","'new_refs':[217,218,219,220]").replace("'parent_preserved_effect_refs':[217,218,219,220]","'parent_preserved_effect_refs':[], 'effect218_three_pixels_preserved':True, 'effect220_occlusion_changes':93").replace("'new_steps':4","'new_steps':sum(q['frame']>=217 for q in s['steps'])")
    dest=H/'review_nova_strike_ultimate.py';assert not dest.exists();dest.write_text(src,'utf8')
    src=(H/'check_nova_strike_base_browser.py').read_text('utf8').replace('nova_strike_base_sequence01','nova_strike_ultimate_sequence01')
    dest=H/'check_nova_strike_ultimate_browser.py';assert not dest.exists();dest.write_text(src,'utf8')
if __name__=='__main__':main()
