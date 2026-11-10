"""리본 폭과 분리된 접지 기준. 몸 전체를 정수 이동하고 화소를 보존한다."""
import numpy as np

def contact_span(pixels,origin=128):
    y,x=np.nonzero(pixels)
    if not len(x):raise ValueError('Empty body')
    floor=int(y.max());cols=x[y>=floor-2]
    return {'center_x':(int(cols.min())+int(cols.max()))/2-origin,'floor_y':floor-origin}

def translate_body_x(pixels,dx):
    if not isinstance(dx,int):raise ValueError('Whole pixel translation required')
    yy,xx=np.nonzero(pixels)
    if not len(xx):raise ValueError('Empty body')
    if int(xx.min())+dx<0 or int(xx.max())+dx>=pixels.shape[1]:raise ValueError('Translation would crop body')
    result=np.zeros_like(pixels);result[yy,xx+dx]=pixels[yy,xx]
    return result


def align_contact_x(pixels,target,origin=128):
    before=contact_span(pixels,origin);dx=round(target-before['center_x'])
    result=translate_body_x(pixels,dx);after=contact_span(result,origin)
    if abs(after['center_x']-target)>.5 or before['floor_y']!=after['floor_y']:raise ValueError('Invalid ground anchor')
    return result,{'before':before,'after':after,'translate_x':dx,'target_x':target,'error_x':after['center_x']-target,'pixel_values_count_preserved':True}
