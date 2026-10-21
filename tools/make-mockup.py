import sys
from PIL import Image, ImageDraw, ImageFilter
src, out = sys.argv[1], sys.argv[2]
S=2  # supersampling
img=Image.open(src).convert("RGB"); top=img.crop((0,0,1024,768)); bot=img.crop((0,792,1024,1560))
SW,SH=560*S,420*S            # screen size
PAD=46*S; W=SW+2*PAD+180*S*2; 
shellW=SW+2*PAD+300*S
H_top=SH+2*PAD; H_bot=SH+2*PAD+40*S
M=60*S; GAP=26*S
CW=shellW+2*M; CH=H_top+GAP+H_bot+2*M
c=Image.new("RGBA",(CW,CH),(0,0,0,0)); d=ImageDraw.Draw(c)
body=(46,48,54); edge=(70,73,80); bez=(18,18,20)
x0=M
# shadow
sh=Image.new("RGBA",(CW,CH),(0,0,0,0)); sd=ImageDraw.Draw(sh)
sd.rounded_rectangle((x0+10*S,M+16*S,x0+shellW+10*S,CH-M+16*S),radius=40*S,fill=(0,0,0,110))
sh=sh.filter(ImageFilter.GaussianBlur(18*S)); c=Image.alpha_composite(c,sh); d=ImageDraw.Draw(c)
# top shell
d.rounded_rectangle((x0,M,x0+shellW,M+H_top),radius=40*S,fill=body,outline=edge,width=3*S)
sx=x0+(shellW-SW)//2; sy=M+PAD
d.rounded_rectangle((sx-14*S,sy-14*S,sx+SW+14*S,sy+SH+14*S),radius=14*S,fill=bez)
c.paste(top.resize((SW,SH),Image.LANCZOS),(sx,sy))
# hinge
hy=M+H_top
d.rounded_rectangle((x0+60*S,hy-6*S,x0+shellW-60*S,hy+GAP+6*S),radius=12*S,fill=(34,35,40))
# bottom shell
by=hy+GAP
d.rounded_rectangle((x0,by,x0+shellW,by+H_bot),radius=40*S,fill=body,outline=edge,width=3*S)
bsy=by+PAD
d.rounded_rectangle((sx-14*S,bsy-14*S,sx+SW+14*S,bsy+SH+14*S),radius=14*S,fill=bez)
c.paste(bot.resize((SW,SH),Image.LANCZOS),(sx,bsy))
# controls (generic)
lx=x0+(sx-x0)//2; cy=bsy+SH//3
a=26*S; t=24*S; col=(28,29,33)
d.rounded_rectangle((lx-t//2,cy-a-t//2,lx+t//2,cy+a+t//2),radius=5*S,fill=col)
d.rounded_rectangle((lx-a-t//2,cy-t//2,lx+a+t//2,cy+t//2),radius=5*S,fill=col)
rx=sx+SW+(x0+shellW-sx-SW)//2
for dx,dy in ((0,-30),(30,0),(0,30),(-30,0)):
    r=15*S; d.ellipse((rx+dx*S-r,cy+dy*S-r,rx+dx*S+r,cy+dy*S+r),fill=col)
for xx in (lx, rx):
    r=30*S; yy=bsy+SH*3//4; d.ellipse((xx-r,yy-r,xx+r,yy+r),fill=(38,39,44),outline=col,width=4*S)
c=c.resize((CW//S,CH//S),Image.LANCZOS); c.save(out,optimize=True)
print(c.size)
