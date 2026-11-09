import re
def norm_code(s):
    s=s.upper().replace(' ','')
    return s
def extract_code(brand,text):
    t=text.upper()
    if brand=='Miele':
        m=re.search(r'\b(W[A-Z]{1,2}\s?\d{3}[A-Z]?|WQ\s?1000|WTD\s?\d{3}|WT[A-Z]\s?\d{3})\b',t)
        return m.group(1).replace(' ','') if m else None
    if brand in ('Bosch','Siemens'):
        m=re.search(r'\b(W[A-Z]{1,2}\d{2,5}[A-Z0-9]{2,5})\b',t)
        return m.group(1) if m else None
    if brand=='AEG':
        m=re.search(r'\b(L[A-Z0-9]{6,10})\b',t)
        return m.group(1) if m else None
def family(brand,code):
    c=norm_code(code)
    if brand=='Miele':
        m=re.match(r'W[A-Z]?([A-Z])(\d{2})\d',c)          # WSG883 -> G88, WWA128 -> A12
        if c.startswith('WQ'): return 'Miele WQ1000'
        if c.startswith('WT'): 
            m2=re.match(r'WT([A-Z])(\d{2})',c); return f'Miele WT {m2.group(1)}{m2.group(2)}' if m2 else c
        return f'Miele W1 {m.group(1)}{m.group(2)}x' if m else c
    if brand in ('Bosch','Siemens'):
        m=re.match(r'(W[A-Z])(\d{2})([A-Z])(\d)',c)       # Siemens WG44G2.., WM14N2.., WN54G2..
        if m: return f'{brand} {m.group(0)}'
        m=re.match(r'(W[A-Z]{2})(\d{3})',c)              # Bosch WGG244.., WAN282.., WNG254..
        if m: return f'{brand} {m.group(0)}'
        return f'{brand} {c}'
    if brand=='AEG':
        m=re.match(r'(L[A-Z]{1,3})(\d{3})',c)            # LR733.., LWR732..
        if m: return f'AEG {m.group(0)}'
        m=re.match(r'(L[A-Z]{1,3}\d[A-Z]\d)',c)          # LR6E2..
        return f'AEG {m.group(1)}' if m else f'AEG {c}'
    return c
if __name__=='__main__':
    for b,c in [('Bosch','WAN2829WSN'),('Bosch','WAN2829ESN'),('Bosch','WGE0340LSN'),('Bosch','WGE03400SN'),('Bosch','WNG2540LSN'),('Bosch','WNG254AKSN'),('Siemens','WG56G2MEDN'),('Siemens','WM14N22EDN'),('Miele','WWG888'),('Miele','WSG883'),('Miele','WSB363'),('Miele','WWB360'),('AEG','LR733E94Q'),('AEG','LR733W96W'),('AEG','LR6E2W94W')]:
        print(c,family(b,c))
