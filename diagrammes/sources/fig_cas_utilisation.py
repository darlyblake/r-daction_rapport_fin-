# Génère exports/fig_cas_utilisation.svg (diagramme de cas d'utilisation UML)
from html import escape
W, H = 1000, 1010
NAVY, GREY, FILL = "#1f3a5f", "#5a6675", "#eef1f5"
ucs = [  # (id, texte, ligne(s))
 ("u1","Gérer établissements|et abonnements"),
 ("u2","Traiter les demandes|de support"),
 ("u3","Gérer comptes, rôles|et paramètres"),
 ("u4","Paramétrer frais, réductions|et organismes payeurs"),
 ("u5","Gérer personnel et paie"),
 ("u6","Gérer élèves, classes|et inscriptions"),
 ("u7","Enregistrer paiements|et échéanciers"),
 ("u8","Saisir les notes"),
 ("u9","Pointer début|et fin de cours"),
 ("u10","Faire l'appel"),
 ("u11","Traiter les justificatifs|d'absence"),
 ("u12","Pointer arrivée|et départ du personnel"),
 ("u13","Consulter la situation|de ses enfants"),
 ("u14","Déposer un justificatif,|demander un document"),
]
top, step = 100, 62
cx = W/2
pos = {u: (cx, top + i*step) for i,(u,_) in enumerate(ucs)}
def y(u): return pos[u][1]
actors = {  # id: (label, x, y, side)
 "pa": ("Administrateur|de plateforme", 100, (y("u1")+y("u2"))/2, "L"),
 "ad": ("Administrateur|d'établissement", 100, (y("u3")+y("u12"))/2-20, "L"),
 "di": ("Direction", 100, (y("u3")+y("u12"))/2+120, "L"),
 "se": ("Secrétariat", W-100, y("u6"), "R"),
 "co": ("Comptabilité", W-100, y("u7"), "R"),
 "en": ("Enseignant", W-100, y("u9"), "R"),
 "su": ("Surveillance", W-100, y("u11"), "R"),
 "pr": ("Parent", W-100, (y("u13")+y("u14"))/2, "R"),
}
links = {
 "pa":["u1","u2"],
 "ad":["u3","u4","u5","u6","u7","u8","u9x","u10","u11","u12"],
 "se":["u6"], "co":["u7"], "en":["u8","u9","u10"], "su":["u10","u11","u12"], "pr":["u13","u14"],
}
links["ad"].remove("u9x")
aw, ah, ew, eh = 190, 58, 165, 24
o = []
o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="DejaVu Sans, Arial, sans-serif">')
o.append(f'<rect width="{W}" height="{H}" fill="white"/>')
bx0, bx1 = 270, W-270
o.append(f'<rect x="{bx0}" y="30" width="{bx1-bx0}" height="{H-60}" rx="14" fill="none" stroke="{NAVY}" stroke-width="1.6"/>')
o.append(f'<text x="{cx}" y="62" text-anchor="middle" font-size="17" font-weight="bold" fill="{NAVY}">Application de gestion administrative scolaire</text>')
# liens
for a, targets in links.items():
    lab, ax, ay, side = actors[a]
    sx = ax + aw/2 if side=="L" else ax - aw/2
    for t in targets:
        tx, ty = pos[t]
        ex = tx - ew*0.93 if side=="L" else tx + ew*0.93
        o.append(f'<line x1="{sx}" y1="{ay}" x2="{ex}" y2="{ty}" stroke="{NAVY}" stroke-width="1.1"/>')
# généralisation Direction -> Administrateur
dl, dx, dy, _ = actors["di"]; al, axx, ay, _ = actors["ad"]
o.append(f'<defs><marker id="tri" markerWidth="12" markerHeight="12" refX="11" refY="6" orient="auto"><path d="M1,1 L11,6 L1,11 Z" fill="white" stroke="{NAVY}" stroke-width="1.2"/></marker></defs>')
o.append(f'<line x1="{dx}" y1="{dy-ah/2}" x2="{axx}" y2="{ay+ah/2+2}" stroke="{NAVY}" stroke-width="1.3" marker-end="url(#tri)"/>')
# cas d'utilisation
for u, txt in ucs:
    x, yy = pos[u]
    o.append(f'<ellipse cx="{x}" cy="{yy}" rx="{ew}" ry="{eh+7}" fill="white" stroke="{NAVY}" stroke-width="1.3"/>')
    parts = txt.split("|")
    base = yy - (len(parts)-1)*8 + 5
    for i,p in enumerate(parts):
        o.append(f'<text x="{x}" y="{base+i*17}" text-anchor="middle" font-size="12" fill="#111">{escape(p)}</text>')
# acteurs
for a,(lab, x, yy, side) in actors.items():
    o.append(f'<rect x="{x-aw/2}" y="{yy-ah/2}" width="{aw}" height="{ah}" rx="9" fill="{FILL}" stroke="{NAVY}" stroke-width="1.4"/>')
    parts = lab.split("|")
    base = yy - (len(parts)-1)*8 + 4
    for i,p in enumerate(parts):
        o.append(f'<text x="{x}" y="{base+i*19}" text-anchor="middle" font-size="15.5" fill="#111">{escape(p)}</text>')
o.append(f'<text x="{W/2}" y="{H-12}" text-anchor="middle" font-size="13" font-style="italic" fill="{GREY}">Direction : mêmes permissions que l\'administrateur d\'établissement côté base de données (généralisation).</text>')
o.append('</svg>')
open("exports/fig_cas_utilisation.svg","w",encoding="utf-8").write("\n".join(o))
print("ok")
