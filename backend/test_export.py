import sys
sys.path.insert(0, r'c:\Users\PHOENIX\editor-pdf\backend')
import pdf_service
from models import EditOperation, Rect

doc_id = 'a79ed556b1a51394'

# 1) Ver o texto da pagina 0
pt = pdf_service.extract_page_text(doc_id, 0)
print(f'Page dimensions: {pt.width} x {pt.height}')
print(f'Num spans: {len(pt.spans)}')
for i, s in enumerate(pt.spans[:20]):
    print(f'  span[{i}]: text="{s.text}" font={s.font} size={s.size} flags={s.flags} origin_y={s.origin_y:.1f} rect=({s.rect.x0:.1f},{s.rect.y0:.1f},{s.rect.x1:.1f},{s.rect.y1:.1f})')

# 2) Encontrar o span "36500000" (o CEP que está na screenshot)
cep_span = None
for s in pt.spans:
    if '36500000' in s.text or '365' in s.text:
        cep_span = s
        print(f'\n*** Found target span: text="{s.text}" font={s.font} size={s.size} flags={s.flags} origin_y={s.origin_y:.1f}')
        print(f'    rect=({s.rect.x0:.1f},{s.rect.y0:.1f},{s.rect.x1:.1f},{s.rect.y1:.1f})')

# 3) Testar o export
if cep_span:
    edit = EditOperation(
        page=0,
        rect=Rect(x0=cep_span.rect.x0, y0=cep_span.rect.y0, x1=cep_span.rect.x1, y1=cep_span.rect.y1),
        original_text=cep_span.text,
        new_text='36500001',
        font=cep_span.font,
        font_size=cep_span.size,
        color=cep_span.color,
        flags=cep_span.flags,
        origin_y=cep_span.origin_y,
    )
    result = pdf_service.apply_edits(doc_id, [edit])
    out_path = r'c:\Users\PHOENIX\editor-pdf\backend\data\test_output.pdf'
    with open(out_path, 'wb') as f:
        f.write(result)
    print(f'\n*** Exported to {out_path} ({len(result)} bytes)')

    # 4) Verificar o texto no PDF gerado
    import fitz
    doc2 = fitz.open(out_path)
    page2 = doc2[0]
    text2 = page2.get_text()
    if '36500001' in text2:
        print('*** SUCCESS: "36500001" found in exported PDF!')
    else:
        print('*** FAIL: "36500001" NOT found in exported PDF')
        # check if old text still there
        if '36500000' in text2:
            print('*** Old text "36500000" still present')
    doc2.close()
