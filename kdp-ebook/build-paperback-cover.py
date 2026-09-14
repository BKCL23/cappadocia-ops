#!/usr/bin/env python3
"""Build a KDP wraparound paperback cover PDF (back + spine + front).
Usage: python3 build-paperback-cover.py <page_count>
"""
import sys, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

random.seed(7)
PAGES = int(sys.argv[1]) if len(sys.argv) > 1 else 32

# ---- KDP geometry (5.5 x 8.5 trim) ----
DPI = 300
TRIM_W, TRIM_H = 5.5, 8.5
BLEED = 0.125
PPI_WHITE = 0.002252                      # spine thickness per page, white paper
spine = PAGES * PPI_WHITE
full_w_in = BLEED + TRIM_W + spine + TRIM_W + BLEED
full_h_in = BLEED + TRIM_H + BLEED
FW, FH = round(full_w_in*DPI), round(full_h_in*DPI)
back_left = 0
back_right = round((BLEED + TRIM_W) * DPI)
spine_right = round((BLEED + TRIM_W + spine) * DPI)
front_w = FW - spine_right
S = front_w / 1600.0                       # scale vs the ebook reference (1600px wide)

SANS_B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
SANS_R = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
SERIF_I = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
def font(p, s): return ImageFont.truetype(p, max(8, int(s)))

CREAM = (255, 247, 233); GOLD = (233, 195, 108); PLUM = (34, 22, 60)

# ---------- sky ----------
stops = [(0.00,(34,22,60)),(0.22,(78,34,82)),(0.40,(150,58,92)),(0.56,(216,96,84)),
         (0.70,(240,150,92)),(0.82,(255,206,150)),(0.90,(240,178,120)),(1.00,(150,96,66))]
def lerp(a,b,t): return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
def sky(fy):
    for i in range(len(stops)-1):
        y0,c0=stops[i]; y1,c1=stops[i+1]
        if y0<=fy<=y1: return lerp(c0,c1,(fy-y0)/(y1-y0))
    return stops[-1][1]

def chimney(d,x,base_y,h,w,color,cap=False):
    tip=max(4.0,w*0.14); top=base_y-h
    d.polygon([(x-w/2,base_y),(x+w/2,base_y),(x+tip,top),(x-tip,top)],fill=color)
    d.ellipse([x-tip,top-tip,x+tip,top+tip],fill=color)
    if cap:
        cw=w*0.30; d.ellipse([x-cw,top-cw*0.75,x+cw,top+cw*0.35],fill=color)

combos=[[(214,69,65),(242,201,76)],[(64,145,163),(240,240,235)],[(120,81,169),(242,201,76)],
        [(226,114,52),(247,238,214)],[(46,110,140),(214,69,65)],[(212,84,120),(250,244,230)],
        [(70,150,110),(242,201,76)],[(230,150,50),(120,81,169)]]
def balloon(base,cx,cy,r,combo,alpha=255):
    Wb,Hb=int(r*2.2),int(r*3.05)
    if Wb<4 or Hb<4: return
    layer=Image.new("RGBA",(Wb,Hb),(0,0,0,0)); mask=Image.new("L",(Wb,Hb),0)
    md=ImageDraw.Draw(mask)
    md.ellipse([int(Wb*0.04),0,int(Wb*0.96),int(Hb*0.72)],fill=255)
    md.polygon([(int(Wb*0.22),int(Hb*0.52)),(int(Wb*0.78),int(Hb*0.52)),(Wb//2,int(Hb*0.80))],fill=255)
    ld=ImageDraw.Draw(layer); n=10
    for i in range(n):
        c=combo[i%len(combo)]
        ld.rectangle([int(Wb*i/n),0,int(Wb*(i+1)/n),Hb],fill=(c[0],c[1],c[2],255))
    sh=Image.new("RGBA",(Wb,Hb),(0,0,0,0)); ImageDraw.Draw(sh).rectangle([0,int(Hb*0.4),Wb,Hb],fill=(0,0,0,45))
    layer=Image.alpha_composite(layer,sh)
    m=mask.point(lambda p:p*alpha//255)
    layer.putalpha(ImageChops.multiply(layer.split()[3],m))
    bd=ImageDraw.Draw(layer); bx0,bx1=int(Wb*0.42),int(Wb*0.58); by=int(Hb*0.90)
    lw=max(1,int(r*0.03))
    bd.line([(int(Wb*0.30),int(Hb*0.70)),(bx0,by)],fill=(60,40,25,alpha),width=lw)
    bd.line([(int(Wb*0.70),int(Hb*0.70)),(bx1,by)],fill=(60,40,25,alpha),width=lw)
    bd.rectangle([bx0,by,bx1,int(Hb*0.95)],fill=(96,60,32,alpha))
    base.alpha_composite(layer,(int(cx-Wb/2),int(cy-Hb/2)))

def draw_scene(W,H):
    s=W/1600.0
    grad=Image.new("RGB",(1,H)); gp=grad.load()
    for y in range(H): gp[0,y]=sky(y/H)
    img=grad.resize((W,H)).convert("RGBA")
    glow=Image.new("RGBA",(W,H),(0,0,0,0)); gd=ImageDraw.Draw(glow)
    gx,gy=int(W*0.5),int(H*0.80)
    for rad,a in [(720,26),(520,34),(340,50),(200,70),(110,110)]:
        rr=int(rad*s); gd.ellipse([gx-rr,gy-rr,gx+rr,gy+rr],fill=(255,236,200,a))
    glow=glow.filter(ImageFilter.GaussianBlur(int(60*s)))
    img=Image.alpha_composite(img,glow)
    # far ridge
    far=Image.new("RGBA",(W,H),(0,0,0,0)); fd=ImageDraw.Draw(far)
    bf=int(H*0.865); xf=-20
    while xf<W+40:
        chimney(fd,xf,bf,random.randint(110,220)*s,random.randint(40,74)*s,(120,82,74,190),random.random()<0.35)
        xf+=random.randint(54,92)*s
    far=far.filter(ImageFilter.GaussianBlur(int(3*s))); img=Image.alpha_composite(img,far)
    d=ImageDraw.Draw(img)
    bn=int(H*0.935); xn=-30
    while xn<W+50:
        chimney(d,xn,bn,random.randint(200,380)*s,random.randint(66,128)*s,(44,27,20,255),random.random()<0.4)
        xn+=random.randint(66,116)*s
    d.rectangle([0,bn-4,W,H],fill=(38,23,17,255))
    balloons=[(0.30,0.42,30,150),(0.68,0.40,26,140),(0.50,0.46,34,160),(0.16,0.50,40,180),
        (0.83,0.49,38,175),(0.40,0.55,52,205),(0.62,0.57,58,215),(0.24,0.62,66,230),
        (0.78,0.63,62,230),(0.50,0.66,80,245),(0.36,0.72,92,255),(0.66,0.73,88,255),
        (0.14,0.70,60,235),(0.88,0.71,56,235),(0.50,0.79,104,255),(0.22,0.80,74,255),(0.80,0.81,70,255)]
    for i,(fx,fy,r,a) in enumerate(balloons):
        balloon(img,fx*W,fy*H,r*s,combos[i%len(combos)],a)
    # vignette
    vig=Image.new("L",(W,H),0); vd=ImageDraw.Draw(vig)
    vd.ellipse([-int(W*0.25),-int(H*0.15),int(W*1.25),int(H*1.15)],fill=255)
    vig=vig.filter(ImageFilter.GaussianBlur(int(220*s)))
    dark=Image.new("RGB",(W,H),(18,10,26))
    return Image.composite(img.convert("RGB"),dark,vig)

# ---------- build full canvas ----------
canvas_img=Image.new("RGB",(FW,FH),PLUM)

# front panel with title
front=draw_scene(front_w,FH).convert("RGBA")
fd=ImageDraw.Draw(front,"RGBA")
def tracked_w(d,text,fnt,tr):
    return sum(d.textlength(c,font=fnt)+tr for c in text)-tr if text else 0
def tracked(d,cx,y,text,fnt,tr,fill,shadow=None):
    x=cx-tracked_w(d,text,fnt,tr)/2
    for c in text:
        if shadow:
            sc,off=shadow; d.text((x+off,y+off),c,font=fnt,fill=sc)
        d.text((x,y),c,font=fnt,fill=fill); x+=d.textlength(c,font=fnt)+tr
Wf=front_w
plate=Image.new("RGBA",(Wf,FH),(0,0,0,0))
ImageDraw.Draw(plate).rectangle([0,int(FH*0.045),Wf,int(FH*0.30)],fill=(20,12,34,70))
plate=plate.filter(ImageFilter.GaussianBlur(int(40*S)))
front=Image.alpha_composite(front,plate); fd=ImageDraw.Draw(front,"RGBA")
SHADOW=((10,6,20,170),max(2,int(5*S)))
tracked(fd,Wf/2,int(FH*0.075),"CAPPADOCIA",font(SANS_B,176*S),int(6*S),CREAM,SHADOW)
rw=int(Wf*0.34); ry=int(FH*0.20)
fd.rectangle([Wf/2-rw/2,ry,Wf/2+rw/2,ry+max(3,int(5*S))],fill=GOLD)
for dx in (-rw/2,rw/2):
    fd.polygon([(Wf/2+dx,ry-9*S),(Wf/2+dx+11*S,ry+2*S),(Wf/2+dx,ry+13*S),(Wf/2+dx-11*S,ry+2*S)],fill=GOLD)
tracked(fd,Wf/2,int(FH*0.223),"THE COMPLETE TRAVELER’S GUIDE",font(SANS_R,50*S),int(7*S),CREAM,((10,6,20,150),max(2,int(3*S))))
tracked(fd,Wf/2,int(FH*0.895),"FAIRY CHIMNEYS  ·  BALLOONS  ·  CAVE HOTELS  ·  VALLEYS",font(SANS_R,31*S),int(3*S),(255,240,220),((10,6,20,150),2))
byf=font(SERIF_I,44*S); by="WRITTEN BY A CAPPADOCIA HOTEL OWNER"
bw=fd.textlength(by,font=byf)
fd.text((Wf/2-bw/2,int(FH*0.94)),by,font=byf,fill=GOLD)
canvas_img.paste(front.convert("RGB"),(spine_right,0))

# ---------- back panel ----------
bd=ImageDraw.Draw(canvas_img,"RGBA")
bx0=int((BLEED+0.30)*DPI); bx1=back_right-int(0.30*DPI); bw_area=bx1-bx0
y=int((BLEED+0.55)*DPI)
# hook
hf=font(SANS_B,int(58*S))
def wrap(d,text,fnt,maxw):
    words=text.split(); lines=[]; cur=""
    for w in words:
        t=(cur+" "+w).strip()
        if d.textlength(t,font=fnt)<=maxw: cur=t
        else: lines.append(cur); cur=w
    if cur: lines.append(cur)
    return lines
for ln in wrap(bd,"The balloons don’t wait for the unprepared.",hf,bw_area):
    bd.text((bx0,y),ln,font=hf,fill=CREAM); y+=int(hf.size*1.2)
y+=int(0.18*DPI)
bodyf=font(SANS_R,int(33*S)); lh=int(bodyf.size*1.42)
para=("Cappadocia is one of the most breathtaking places on Earth — a moonscape of "
      "fairy chimneys, cave churches, and a sky that fills with a hundred hot-air balloons "
      "at dawn. But it quietly punishes travelers who improvise.")
for ln in wrap(bd,para,bodyf,bw_area):
    bd.text((bx0,y),ln,font=bodyf,fill=(238,228,214)); y+=lh
y+=int(0.14*DPI)
bd.text((bx0,y),"Written by a hotel owner who lives here, this guide gives you:",font=bodyf,fill=(238,228,214)); y+=int(lh*1.15)
bullets=["When to go — month by month, built around your odds of flying",
         "The hot-air balloon, demystified — pricing, safety, the rule that gets you airborne",
         "Where to stay, the best valleys, and 1–4 day itineraries",
         "Food, photography, and how to avoid the common scams"]
bf2=font(SANS_R,int(31*S)); blh=int(bf2.size*1.38)
for b in bullets:
    bd.ellipse([bx0,y+int(bf2.size*0.35),bx0+int(9*S),y+int(bf2.size*0.35)+int(9*S)],fill=GOLD)
    for i,ln in enumerate(wrap(bd,b,bf2,bw_area-int(0.28*DPI))):
        bd.text((bx0+int(0.28*DPI),y),ln,font=bf2,fill=(238,228,214)); y+=blh
    y+=int(0.05*DPI)
# tagline above barcode zone
tf=font(SERIF_I,int(34*S))
bd.text((bx0,back_right and int((BLEED+TRIM_H-0.7)*DPI)),"Come prepared. Travel kindly. Look up often.",font=tf,fill=GOLD)
# leave bottom-right clear for KDP barcode (~2 x 1.2 in)

canvas_img.save("cover-full.png","PNG")

# ---------- wrap into a PDF at exact point size ----------
c=canvas.Canvas("Cappadocia-Paperback-Cover.pdf",pagesize=(full_w_in*72,full_h_in*72))
c.drawImage(ImageReader("cover-full.png"),0,0,width=full_w_in*72,height=full_h_in*72)
c.save()
print("spine=%.4f in | full cover=%.3f x %.3f in | %dx%d px" % (spine,full_w_in,full_h_in,FW,FH))
