from pathlib import Path
import html,base64,json,math,subprocess,hashlib,random,shutil
from collections import deque,defaultdict
from PIL import Image,ImageFont,ImageDraw,ImageFilter
import numpy as np,cv2

R=Path(__file__).parent; W,H=1086,1448
LIME='#C5F74E'; DARK='#202426'; GRAY='#E1E3DF'; INK='#171B1E'; WHITE='#F5F6F7'; BLUE='#087BFF'
FONTS={500:R/'fonts/Manrope-Medium.ttf',700:R/'fonts/Manrope-Bold.ttf',800:R/'fonts/Manrope-ExtraBold.ttf'}
TEXT_LOG=[]
# Instantiate font weights locally for measurement; SVG keeps live text and variable Manrope.
if not (R/'fonts/Manrope-ExtraBold.ttf').exists():
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    for weight,name in [(500,'Medium'),(700,'Bold'),(800,'ExtraBold')]:
        f=instantiateVariableFont(TTFont(R/'fonts/Manrope-variable.ttf'),{'wght':weight},inplace=False)
        f.save(R/'fonts'/f'Manrope-{name}.ttf')
for name in ['masters','publication']:(R/name).mkdir(exist_ok=True)

def tw(s,fs,weight=500,ls=0):return ImageFont.truetype(str(FONTS[weight]),fs).getlength(s)+max(0,len(s)-1)*ls
def tx(x,y,s,fs=38,weight=500,fill=INK,ls=0):
    TEXT_LOG.append(dict(text=s,font_size=fs,weight=weight,x=x,y=y,fill=fill))
    return f'<text x="{x}" y="{y}" font-family="Manrope" font-weight="{weight}" font-size="{fs}" letter-spacing="{ls}" fill="{fill}">{html.escape(s)}</text>'
def lines(strings,x,y,fs=38,step=None,weight=500,fill=INK,ls=0):
    return ''.join(tx(x,y+i*(step or fs*1.35),s,fs,weight,fill,ls) for i,s in enumerate(strings))
def wrap(s,width,fs=38,weight=500):
    out=[];line=''
    for word in s.split():
        t=(line+' '+word).strip()
        if tw(t,fs,weight)>width and line:out.append(line);line=word
        else:line=t
    if line:out.append(line)
    return out
def rect(x,y,w,h,fill=WHITE,r=26,stroke=None):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"'+(f' stroke="{stroke}" stroke-width="2"' if stroke else '')+'/>'
def layer(name,body):return f'<g id="{name}" inkscape:groupmode="layer" inkscape:label="{name}">{body}</g>'
def card(x,y,w,h,fill='url(#paper)',r=26):return f'<g filter="url(#shadow)">{rect(x,y,w,h,fill,r)}</g>'
def img(path,x,y,w,h):
    data=base64.b64encode(Path(path).read_bytes()).decode()
    return f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{data}"/>'
def dots(x,y):return ''.join(f'<circle cx="{x+i*17}" cy="{y}" r="5" fill="{c}"/>' for i,c in enumerate(['#FF6B64','#FFC94C','#57C779']))
def icon(kind,x,y,size=56):
    q=''
    if kind=='doc':q='<rect x="8" y="3" width="42" height="52" rx="7" fill="#087BFF"/><path d="M18 17h21M18 28h21M18 39h15" stroke="white" stroke-width="4" stroke-linecap="round"/>'
    elif kind=='chat':q='<rect x="3" y="6" width="52" height="40" rx="12" fill="#087BFF"/><path d="M14 39v16l16-13" fill="#087BFF"/>'+''.join(f'<circle cx="{v}" cy="26" r="3.7" fill="white"/>' for v in [17,29,41])
    elif kind=='video':q='<rect x="1" y="7" width="56" height="42" rx="11" fill="#087BFF"/><path d="M23 17l17 12-17 12Z" fill="white"/>'
    elif kind=='send':q='<rect x="1" y="1" width="56" height="56" rx="13" fill="#087BFF"/><path d="M12 28l33-15-10 32-9-13Z" fill="white"/><path d="M26 32l19-19" stroke="#087BFF" stroke-width="2"/>'
    return f'<g transform="translate({x},{y}) scale({size/58})">{q}</g>'
def clock(x,y,hour,minute,r=68):
    def point(a,l):a=math.radians(a-90);return x+math.cos(a)*l,y+math.sin(a)*l
    a=minute*6;b=(hour%12+minute/60)*30
    xx,yy=point(a,r*.74);hx,hy=point(b,r*.48)
    s=f'<circle cx="{x}" cy="{y}" r="{r+12}" fill="{DARK}"/>'
    s+=f'<path d="M{x-r} {y+1} C{x-r-5} {y-r*.62} {x-r*.56} {y-r-3} {x+1} {y-r} C{x+r*.64} {y-r-3} {x+r+2} {y-r*.52} {x+r} {y+1} C{x+r+1} {y+r*.63} {x+r*.55} {y+r+3} {x} {y+r} C{x-r*.6} {y+r+1} {x-r-2} {y+r*.56} {x-r} {y+1}Z" fill="none" stroke="{LIME}" stroke-width="5"/>'
    for i in range(12):
        x1,y1=point(i*30,r*.83);x2,y2=point(i*30,r*.92)
        s+=f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{LIME}" stroke-width="4" stroke-linecap="round"/>'
    return s+f'<path d="M{x} {y}L{xx} {yy}M{x} {y}L{hx} {hy}" stroke="{LIME}" stroke-width="7" stroke-linecap="round"/><circle cx="{x}" cy="{y}" r="5" fill="{LIME}"/>'
def rays(x,y,scale=1):return f'<g transform="translate({x},{y}) scale({scale})" fill="none" stroke="{LIME}" stroke-width="8" stroke-linecap="round"><path d="M0 0l12-28M30 18l27-17M44 49l30-2"/></g>'
def highlight(s,x,y,fs=96):return rect(x-12,y-fs+3,tw(s,fs,800,-3)+26,fs+22,LIME,16)+tx(x,y,s,fs,800,INK,-3)
def avatar(cx,cy,r=28):
    return f'<circle cx="{cx}" cy="{cy}" r="{r+4}" fill="{LIME}"/><g clip-path="url(#av)">{img(R/"avatar.png",cx-r,cy-r,r*2,r*2)}</g>' if False else f'<circle cx="{cx}" cy="{cy}" r="{r+4}" fill="{LIME}"/><svg x="{cx-r}" y="{cy-r}" width="{2*r}" height="{2*r}" viewBox="0 0 100 100"><defs><clipPath id="avcircle"><circle cx="50" cy="50" r="50"/></clipPath></defs><g clip-path="url(#avcircle)">{img(R/"avatar.png",0,0,100,100)}</g></svg>'

# Fixed interface-maze, approved visual direction #3: actual UI panels form its walls.
main=[(170,710),(170,595),(170,430),(425,430),(425,165),(460,165),(460,100),(555,100)]
branches=[[(170,430),(75,430)],[(425,430),(580,430)],[(170,430),(170,165),(300,165)],[(425,430),(425,515),(300,515)]]
graph=defaultdict(set)
for path in [main]+branches:
    for a,b in zip(path,path[1:]):graph[a].add(b);graph[b].add(a)
def route(a,b):
    q=deque([(a,[a])]);seen={a}
    while q:
        a,p=q.popleft()
        if a==b:return p
        for v in sorted(graph[a]):
            if v not in seen:seen.add(v);q.append((v,p+[v]))
    raise ValueError('Disconnected maze')
stops=[(170,710),(75,430),(580,430),(300,165),(300,515),(555,100),(555,100)]
def xy(node):return node
def pathsvg(nodes,col,sw=9):
    return '<polyline points="'+' '.join(f'{x},{y}' for x,y in nodes)+f'" stroke="{col}" stroke-width="{sw}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
def maze_window(x,y,w,h,kind=None):
    s=rect(x+4,y+10,w,h,'#788087',15)+card(x,y,w,h,'url(#paper)',15)
    s+=rect(x,y,w,27,'#D9DEE5',13)+dots(x+15,y+13)
    if kind:s+=icon(kind,x+13,y+42,min(52,w-26))
    elif w>75:s+=f'<circle cx="{x+25}" cy="{y+53}" r="12" fill="#B6BEC8"/>'
    if w>120:
        for k in range(min(3,max(0,(h-65)//25))):
            xx=x+(80 if kind else 47);yy=y+48+k*25;ww=max(20,w-(94 if kind else 61))
            s+=rect(xx,yy,ww,9,'#C2C9D2',4)
    elif h>125:
        for k in range((h-94)//29):
            yy=y+89+k*29;s+=rect(x+15,yy,w-30,9,'#C2C9D2',4)
    return s
def maze(n,x,y,sc=1):
    s=card(0,0,652,738,'#2D3438',22)
    history=[]
    for i in range(1,n):
        seg=route(stops[i-1],stops[i]);history.extend(seg if not history else seg[1:])
    if history:s+=pathsvg(history,'#91A275',7)
    current=route(stops[n-2],stops[n-1]) if n>1 else [(170,738),(170,710)]
    s+=pathsvg(current,LIME,11)
    # Large recognizable chat windows, video frame and lists, with real free corridors between.
    panels=[(20,20,190,120,'chat'),(235,20,210,80,None),(490,20,140,120,'doc'),(20,200,115,190,None),(210,200,175,150,'video'),(470,200,160,190,'chat'),(20,470,115,230,None),(210,555,230,145,None),(520,470,110,230,None)]
    for a,b,c,d,k in panels:s+=maze_window(a,b,c,d,k)
    # Interface strips cap the video and forwarding side branches.
    s+=maze_window(354,108,42,91,None)
    s+=maze_window(255,451,130,20,None)
    s+=maze_window(210,480,45,64,None)
    for node,kind in [((75,430),'chat'),((580,430),'chat'),((300,165),'video'),((300,515),'send')]:
        a,b=node;s+=card(a-23,b-23,46,46,'url(#paper)',10)+icon(kind,a-19,b-19,38)
    a,b=stops[n-1];s+=avatar(a,b,25)
    if n==7:
        s+=rect(399,110,199,92,LIME,12)+tx(412,145,'Следующий',21,700)+tx(412,174,'шаг →',21,700)
    return f'<g transform="translate({x},{y}) scale({sc})">{s}</g>'


def video(x,y,w,h,small=False):
    fs=34 if small else 43
    s=card(x,y,w,h,'#22282C',24)+dots(x+23,y+22)
    s+=lines(['Как не отвлекаться:','узнай за минуту'],x+28,y+85,fs,fs*1.35,800,WHITE,-1)
    s+=f'<circle cx="{x+w*.5}" cy="{y+h*.67}" r="{32 if small else 43}" fill="{LIME}"/><path d="M{x+w*.5-9} {y+h*.67-17}l27 17-27 17Z" fill="{INK}"/>'
    s+=tx(x+w-99,y+h-24,'00:58',27,700,WHITE)
    s+=f'<path d="M{x+28} {y+h-30}h{w-150}" stroke="#657078" stroke-width="4" stroke-linecap="round"/>'
    return s

DEFS='''<defs>
 <linearGradient id="paper" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#FFFFFF"/><stop offset="1" stop-color="#E9ECF0"/></linearGradient>
 <linearGradient id="wall" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#FFFFFF"/><stop offset=".5" stop-color="#E8EBF0"/><stop offset="1" stop-color="#B9C0C7"/></linearGradient>
 <filter id="shadow" x="-.2" y="-.2" width="1.5" height="1.6" color-interpolation-filters="sRGB"><feGaussianBlur in="SourceAlpha" stdDeviation="10" result="blur"/><feOffset in="blur" dx="0" dy="10" result="offset"/><feFlood flood-color="#000000" flood-opacity=".18" result="color"/><feComposite in="color" in2="offset" operator="in" result="shadow"/><feMerge><feMergeNode in="shadow"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
 </defs>'''

# Photo layers are already checked and locally retouched; rebuilding must not retouch them again.
clean=R/'photos'

manifest=[]
for n in range(1,8):
    TEXT_LOG.clear();bg=DARK if n%2 else GRAY;ink=WHITE if n%2 else INK
    body=layer('01-background',rect(0,0,W,H,bg,0))
    if n==1:
        body+=layer('02-maze',maze(n,38,420,.91))
        body+=layer('03-photo',img(clean/'01.png',360,558,800,1067))
        body+=layer('04-title',tx(62,151,'Лабиринт',116,800,WHITE,-4)+tx(62,265,'чатов и добрых',102,800,LIME,-4)+tx(62,377,'намерений',115,800,WHITE,-4))
        bubble=card(585,525,444,145)+f'<path d="M740 656l31 42 5-45" fill="#E9ECF0"/>'+lines(['Зашла ответить','на одно сообщение'],611,579,33,44,700)
        body+=layer('05-speech',bubble)+layer('06-markers',rays(982,762,.8))
        body+=layer('07-clock',clock(950,421,10,0,61))
    elif n==2:
        body+=layer('02-maze',maze(n,60,944,.48))
        body+=layer('03-photo',img(clean/'02.png',420,310,745,993))
        body+=layer('04-speech',tx(64,153,'Всё,',116,800,INK,-4)+highlight('ответила.',64,278,112))
        ui=card(64,381,538,126)+tx(92,426,'Елена',24,700,'#697078')+tx(92,477,'Хорошо, до завтра.',36,700)
        ui+=card(89,538,558,171)+icon('chat',112,565,49)+lines(['Смотри, какая','статья'],180,600,39,52,700)
        body+=layer('05-chat',ui)+layer('06-markers',rays(979,496,.8))
        body+=layer('07-clock',clock(943,142,10,10,68))
    elif n==3:
        body+=layer('02-maze',maze(n,43,743,.65))
        body+=layer('03-photo',img(clean/'03.png',435,633,783,1044))
        incoming=card(64,86,772,291)+tx(94,135,'Коллега',25,700,'#697078')+lines(['Можешь посоветовать','что-нибудь, чтобы','не отвлекаться?'],94,205,48,63,700)
        outgoing=card(164,417,687,200,LIME)+tx(194,462,'Елена',25,700,INK)+lines(['Сейчас поищу, думаю,','всем пригодится.'],194,522,43,59,700)
        body+=layer('04-dialogue',incoming+outgoing)+layer('05-markers',rays(983,780,.75))
        body+=layer('07-clock',clock(948,160,10,25,63))
    elif n==4:
        body+=layer('02-maze',maze(n,58,878,.41))
        body+=layer('03-photo',img(clean/'04.png',465,413,650,867))
        body+=layer('04-speech',tx(64,149,'Всего',113,800,INK,-3)+highlight('на минуту.',64,275,107))
        body+=layer('05-video',video(64,418,504,375))
        body+=layer('06-social-cta',lines(['Перешлите тому,','кто тоже заходит «на минутку».'],64,1296,34,48,700,INK))
        body+=layer('07-clock',clock(946,143,10,40,67))+layer('08-markers',rays(996,522,.7))
    elif n==5:
        body+=layer('02-maze',maze(n,44,1013,.37))
        doc=card(585,442,435,690)+dots(610,471)+tx(610,526,'Мой документ',27,700)+f'<path d="M609 553h385" stroke="#CDD3D9" stroke-width="2"/>'+tx(613,619,'Начать стоит с…',31,500)+f'<path d="M886 593v34" stroke="{BLUE}" stroke-width="3"/>'
        body+=layer('03-working-document',doc)
        body+=layer('04-narrator',tx(64,139,'Всем помогла.',95,800,WHITE,-3)+tx(64,247,'А что с рабочим',89,800,LIME,-3)+tx(64,350,'документом?',99,800,LIME,-3))
        ui=card(64,438,662,441)+tx(94,484,'Елена',25,700,'#697078')+tx(94,537,'Держите, как раз по теме!',36,700)+video(93,565,603,280,True)
        for x,y,w,reply in [(413,915,550,'Классно, посмотрю!'),(353,1017,441,'Здорово!'),(489,1119,495,'Супер, спасибо!')]:
            ui+=card(x,y,w,78)+f'<circle cx="{x+37}" cy="{y+39}" r="15" fill="{BLUE}"/>'+tx(x+67,y+52,reply,32,700)
        body+=layer('05-forward-and-replies',ui)+layer('07-clock',clock(947,133,11,20,62))
    elif n==6:
        body+=layer('02-photo',img(clean/'06.png',0,385,1086,1448))
        body+=layer('03-speech',tx(64,145,'Так… А на чём',94,800,INK,-3)+highlight('я остановилась?',64,254,91))
        # Affine projection stays inside the actual visible screen plane.
        scr=f'<g transform="translate(0,385)"><g transform="matrix(.396 .051 -.0686 .39 672 502)">'+tx(74,111,'Мой документ',45,700,'#565D63')+f'<path d="M60 146h870" stroke="#B7BDC2" stroke-width="3"/>'+tx(75,270,'Начать стоит с…',76,500,INK)+f'<path d="M737 195v95" stroke="{BLUE}" stroke-width="7"/></g></g>'
        body+=layer('04-screen-text',scr)
        body+=layer('05-maze',maze(n,45,1036,.39))
        body+=layer('07-clock',clock(946,386,11,30,64))
    elif n==7:
        body+=layer('02-maze',maze(n,804,626,.32))
        head=tx(64,128,'Перед переключением —',72,800,WHITE,-2)+tx(64,238,'оставьте точку',99,800,WHITE,-3)+tx(64,348,'возврата.',111,800,LIME,-3)
        body+=layer('03-title',head)
        copy=lines(['Даже если пока не получается не отвлекаться,','можно помочь себе вернуться.'],64,440,35,49,500,WHITE)
        copy+=lines(['Перед тем как открыть другой документ','или чат, коротко запишите:'],64,563,35,49,500,WHITE)
        for i,s in enumerate(['На чём остановились.','Что сделать следующим шагом.','Где лежат нужные материалы.']):
            yy=710+i*72;copy+=f'<circle cx="80" cy="{yy-12}" r="7" fill="{LIME}"/>'+tx(105,yy,s,35,700,WHITE)
        body+=layer('04-return-point',copy)
        iwe=['В IWE — интеллектуальной рабочей среде —','материалы, решения и следующие шаги собраны','в контексте проекта. Это помогает продолжать','работу вместе с ИИ, сохраняя нить задачи.']
        body+=layer('05-iwe-explanation',lines(iwe,64,968,34,48,500,WHITE))
        body+=layer('06-main-cta',rect(64,1187,958,143,LIME,22)+lines(['Посмотрите, как это устроено в IWE.','Ссылка в подписи.'],91,1243,37,52,800,INK,-.5))
        body+=layer('07-clock',clock(950,529,11,40,53))
    body+=layer('99-footer',rect(0,1391,1086,57,bg,0)+tx(64,1427,f'{n:02} / 07',25,700,ink)+tx(928,1427,'МИМ',26,700,ink))
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="1086" height="1448" viewBox="0 0 1086 1448"><title>Лабиринт чатов и добрых намерений · {n}/7</title>{DEFS}{body}</svg>'
    # Correct Inkscape namespace for genuine editable layers.
    svg=svg.replace('http://www.inkscape.org/namespaces/inkscape','http://www.inkscape.org/namespaces/inkscape')
    sp=R/'masters'/f'{n:02}.svg';sp.write_text(svg)
    png=R/'publication'/f'{n:02}.png'
    subprocess.run(['inkscape',str(sp),'--export-type=png',f'--export-filename={png}'],capture_output=True,check=True)
    data=png.read_bytes();manifest.append(dict(order=n,name=png.name,width=W,height=H,size=len(data),sha256=hashlib.sha256(data).hexdigest(),git_blob_sha=hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest(),clock=['10:00','10:10','10:25','10:40','11:20','11:30','11:40'][n-1],text=list(TEXT_LOG),maze_stop=stops[n-1]))
    Image.open(png).resize((360,480),Image.Resampling.LANCZOS).save(R/f'phone-{n:02}.png')
(R/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
(R/'maze-geometry.json').write_text(json.dumps({'main':main,'branches':branches,'stops':stops,'edges':[[list(a),list(b)] for a in sorted(graph) for b in sorted(graph[a]) if a<b],'note':'Fixed connected tree; terminal side branches, one actual route to document.'},indent=2))
print('Built seven layered SVGs and seven ordered PNGs; phone previews saved.')
