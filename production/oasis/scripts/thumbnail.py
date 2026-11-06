from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
EP="/home/user/Ai-mation/docs/oasis-team/ep01"; F="/tmp/claude-0/-home-user-Ai-mation/2bd9efd6-c97a-5f39-86d7-33d600586032/scratchpad/fonts"
W,H=1280,720
def bg(name, zoom=1.0, cx=0.5, cy=0.5):
    im=Image.open(f"{EP}/{name}.jpg").convert("RGB"); w,h=im.size; cw,ch=int(w/zoom),int(h/zoom)
    x=min(max(0,int(cx*w-cw/2)),w-cw); y=min(max(0,int(cy*h-ch/2)),h-ch)
    im=im.crop((x,y,x+cw,y+ch)).resize((W,H),Image.LANCZOS)
    im=ImageEnhance.Color(im).enhance(1.25); im=ImageEnhance.Contrast(im).enhance(1.08); return im
def text(d,xy,t,size,fill,stroke=12,font="Lalezar.ttf",anchor="mm",sc="#2a1203"):
    f=ImageFont.truetype(f"{F}/{font}",size)
    d.text((xy[0]+6,xy[1]+8),t,font=f,anchor=anchor,fill=(0,0,0,150),stroke_width=stroke,stroke_fill=(0,0,0,150),direction="rtl")
    d.text(xy,t,font=f,anchor=anchor,fill=fill,stroke_width=stroke,stroke_fill=sc,direction="rtl")
def pill(d,box,fill,t,size,tc="white"):
    d.rounded_rectangle(box,radius=(box[3]-box[1])//2,fill=fill,outline="white",width=6)
    f=ImageFont.truetype(f"{F}/Lalezar.ttf",size); d.text(((box[0]+box[2])//2,(box[1]+box[3])//2+4),t,font=f,anchor="mm",fill=tc,direction="rtl")
def vignette(im):
    v=Image.new("L",(W,H),0); dv=ImageDraw.Draw(v); dv.rectangle((0,0,W,H),fill=0)
    g=Image.new("RGB",(W,H),(0,0,0)); m=Image.radial_gradient("L").resize((W,H)); m=m.point(lambda p:int(p*0.55))
    return Image.composite(g,im,m)

# A: the race
a=vignette(bg("s06",1.12,0.5,0.55)); d=ImageDraw.Draw(a,"RGBA")
text(d,(W//2,92),"سباق الكثبان!",150,"#FFD54A")
pill(d,(40,H-150,430,H-40),"#E53935","من سيفوز؟",78)
a.save("thumb_A.jpg",quality=92)

# B: the hook (lost)
b=vignette(bg("s01",1.35,0.5,0.45)); d=ImageDraw.Draw(b,"RGBA")
text(d,(W*0.30,H*0.30),"ضاع في",120,"#FFFFFF")
text(d,(W*0.30,H*0.52),"الصحراء!",140,"#FFD54A")
pill(d,(60,H-150,520,H-50),"#E53935","كيف يعود؟",76)
text(d,(W-90,120),"؟",230,"#FFD54A",stroke=14)
b.save("thumb_B.jpg",quality=92)

# mobile preview: both at 320px wide side by side
s=Image.new("RGB",(660,190),"white")
s.paste(a.resize((320,180)),(5,5)); s.paste(b.resize((320,180)),(335,5)); s.save("mobile.jpg")
