from pathlib import Path
import os,re,html,json
from PIL import Image as PImage
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,Image,KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

R=Path(__file__).parent
# In the repository this script sits beside STYLE-GUIDE.md. For the session build,
# pass the active carousel and character assets through environment variables.
ROOT=Path(os.environ.get('MIM_REPOSITORY_ROOT',str(R.parents[2])))
ASSETS=Path(os.environ.get('MIM_CAROUSEL_ASSETS',str(ROOT/'vk-carousel/assets/05-elena-v6')))
FONT=Path(os.environ.get('MIM_GUIDE_FONT_DIR',str(R/'fonts')))
from fontTools.ttLib import TTFont as FTFont
from fontTools.varLib.instancer import instantiateVariableFont
pdf_fonts=R/'pdf-fonts';pdf_fonts.mkdir(exist_ok=True)
for weight,name,alias in [(500,'Medium','M'),(700,'Bold','MB'),(800,'ExtraBold','MX')]:
    f=instantiateVariableFont(FTFont(FONT/'Manrope-variable.ttf'),{'wght':weight},inplace=False)
    # Unique embedded PostScript names prevent ReportLab from deduplicating different weights.
    names={1:'Manrope Guide',2:name,3:'ManropeGuide-'+name+'-2.3',4:'Manrope Guide '+name,6:'ManropeGuide-'+name}
    for rec in f['name'].names:
        if rec.nameID in names:rec.string=names[rec.nameID].encode(rec.getEncoding())
    dest=pdf_fonts/f'Manrope-{name}.ttf';f.save(dest)
    pdfmetrics.registerFont(TTFont(alias,str(dest)))
pdfmetrics.registerFontFamily('M',normal='M',bold='MB',italic='M',boldItalic='MB')
DARK='#202426';LIME='#C5F74E';GRAY='#E1E3DF';INK='#171B1E';WHITE='#F5F6F7'
P=ParagraphStyle('body',fontName='M',fontSize=10.3,leading=15.2,spaceAfter=9,textColor=colors.HexColor(INK))
H=ParagraphStyle('heading',fontName='MX',fontSize=17,leading=22,spaceBefore=16,spaceAfter=10,keepWithNext=True,textColor=colors.HexColor(INK))
H3=ParagraphStyle('subheading',parent=H,fontSize=13,leading=18,spaceBefore=8)
SM=ParagraphStyle('small',parent=P,fontSize=9,leading=13)
B=ParagraphStyle('bullet',parent=P,leftIndent=12,firstLineIndent=0,bulletIndent=0,spaceAfter=5)
COVER=ParagraphStyle('cover',fontName='MX',fontSize=38,leading=45,textColor=colors.HexColor(WHITE),spaceAfter=16)
CW=ParagraphStyle('coverbody',parent=P,textColor=colors.HexColor(WHITE),fontSize=12,leading=18)

def inline(s):
    s=html.escape(s)
    s=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',lambda m:'<a href="'+m.group(2)+'"><u>'+m.group(1)+'</u></a>',s)
    s=re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',s)
    s=re.sub(r'(?<!["=])(https?://[^\s<>]+)',lambda m:m.group(0) if 'href=' in s[max(0,m.start()-8):m.start()] else m.group(0),s)
    return s
def Ptxt(s,style=P):return Paragraph(inline(s),style)
def blocks(text):
    out=[]
    for chunk in re.split(r'\n\s*\n',text.strip()):
        if not chunk.strip():continue
        if chunk.startswith('### '):out.append(Ptxt(chunk[4:],H3));continue
        ls=chunk.splitlines()
        if all(l.startswith('- ') for l in ls):
            out.extend(Paragraph(inline(l[2:]),B,bulletText='•') for l in ls)
        elif all(re.match(r'^\d+\. ',l) for l in ls):
            for l in ls:
                n,body=l.split('. ',1);out.append(Paragraph(inline(body),B,bulletText=n+'.'))
        else:out.append(Ptxt(' '.join(ls)))
    return out

cache=R/'pdf-images';cache.mkdir(exist_ok=True)
def jpg(source,key,maxsize=(1000,1300)):
    im=PImage.open(source).convert('RGBA');bg=PImage.new('RGBA',im.size,GRAY);bg.alpha_composite(im);im=bg.convert('RGB');im.thumbnail(maxsize,PImage.Resampling.LANCZOS);dest=cache/(key+'.jpg');im.save(dest,quality=89,optimize=True);return dest
def picture(source,key,w,h):
    f=jpg(source,key);im=PImage.open(f);scale=min(w/im.width,h/im.height);return Image(str(f),width=im.width*scale,height=im.height*scale)
catalog=json.loads((R/'catalog.json').read_text()) if (R/'catalog.json').exists() else json.loads((R/'assets-current.json').read_text())
guide=(R/'STYLE-GUIDE.md').read_text()

story=[Spacer(1,20),Ptxt('МИМ · РУКОВОДСТВО ДЛЯ КРЕАТОРА',CW),Spacer(1,15),Paragraph('Фото,<br/>интерфейсы<br/>и <font color="'+LIME+'">персонажи</font>',COVER),Ptxt('Стиль 2.3 · 29 октября 2026',CW),Spacer(1,5),Ptxt('Сценарий, типографика, интерфейсы, характеры героев, качество и редактируемые исходники.',CW),Spacer(1,17)]
thumbs=[picture(ASSETS/f'{n:02}.png',f'cover-{n}',150,200) for n in [1,3,6]]
tab=Table([thumbs],colWidths=[166,166,166]);tab.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0)]));story+=[tab,Spacer(1,24)]
buttons=Table([[Ptxt('[Открыть весь пак]('+catalog['style_folder']+')',P),Ptxt('[Краткий бриф](https://drive.google.com/file/d/13Orjey9rmrKkZXidAAxca81-BD4Sma6v/view)',P)]],colWidths=[249,249]);buttons.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor(LIME)),('TOPPADDING',(0,0),(-1,-1),11),('BOTTOMPADDING',(0,0),(-1,-1),4)]));story+=[buttons,PageBreak()]
sections=re.split(r'^## ',guide,flags=re.M)[1:]
for sec in sections:
    title,body=sec.split('\n',1)
    if title.startswith('13.'):
        parts=re.split(r'^### ',body,flags=re.M);intro=parts[0]
        for idx,part in enumerate(parts[1:]):
            name,profile=part.split('\n',1);ch=catalog['characters'][idx]
            story.append(PageBreak());story.append(Ptxt('Персонажи · '+str(idx+1)+' / 4',H3));story.append(Ptxt(name,H))
            ps=re.split(r'\n\s*\n',profile.strip());status=ps[0];core=ps[1]
            fallback=ROOT/('vk-carousel/style-packs/01-photo-notifications/characters/'+['01-elena','02-dmitry','03-lyudmila','04-alexander'][idx]+'/assets/01-front.png')
            env='MIM_CHARACTER_'+ch['key'].upper();photo=Path(os.environ.get(env,str(fallback)))
            image=picture(photo,'portrait-'+ch['key'],150,208)
            right=[Ptxt(status,SM),Ptxt(core)]
            table=Table([[image,right]],colWidths=[167,331]);table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),8)]));story+=[table,Spacer(1,12)]
            for para in ps[2:]:story+=blocks(para)
            story.append(Ptxt('Профессия — контекст, не предел личности. Выбирать позы и реакции по сюжету, сохраняя индивидуальность.',SM))
        continue
    if title.startswith('14.'):
        story+=[PageBreak(),Ptxt(title,H)]
        figs=[picture(ASSETS/f'{n:02}.png',f'case-{n}',240,320) for n in [2,3]]
        captions=[Ptxt('Взгляд в телефон; ответ Елены; фигура до края и полупрозрачный низ.',SM),Ptxt('Просьба Людмилы; фотоаватары вместо имён; пузыри мессенджера.',SM)]
        t=Table([figs,captions],colWidths=[249,249]);t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),9)]));story+=[t,Spacer(1,10)]
    else:
        if title.startswith('15.'):story.append(PageBreak())
        story.append(Ptxt(title,H))
    story+=blocks(body)

def page(can,doc):
    can.saveState();can.setFillColor(colors.HexColor(DARK if doc.page==1 else GRAY));can.rect(0,0,595.28,841.89,fill=1,stroke=0);can.setFillColor(colors.HexColor('#B6C0C5' if doc.page==1 else '#596269'));can.setFont('M',8);can.drawString(42,22,'МИМ · стиль 2.3 · 29.10.2026');can.drawRightString(553,22,str(doc.page));can.restoreState()
dest=R/'МИМ-Стиль-и-персонажи-v2.3.pdf'
doc=SimpleDocTemplate(str(dest),pagesize=(595.28,841.89),leftMargin=42,rightMargin=42,topMargin=35,bottomMargin=43,title='МИМ — руководство по стилю 2.3',author='МИМ · редакционный проект')
doc.build(story,onFirstPage=page,onLaterPages=page)
print(str(dest),dest.stat().st_size)
