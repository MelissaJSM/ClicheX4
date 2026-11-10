"""Verified US Zero rising-saber body and paired effect references."""
SCOPE='wall_spin_ice_rise_bank1_v1'
TURN_SCOPE='wall_spin_ice_rise_turn_bank1_v2'
BODY=frozenset((86,87,*range(144,161,2)))
NEW_BODY=frozenset(range(144,160,2))
EFFECTS=frozenset(range(145,160,2))
RISE_LOOP=frozenset((148,150,152,154))
TURN_VIEWS={str(n):('rear' if n in RISE_LOOP else 'front') for n in NEW_BODY}
