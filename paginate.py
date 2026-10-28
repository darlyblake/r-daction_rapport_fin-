import json,subprocess,sys
from pypdf import PdfReader
S="/tmp/claude-0/-home-claude/6c8842db-edf7-55b9-8481-b0ec396d9f22/scratchpad"
H="/home/claude/livrables/final/"
def render():
    subprocess.run(["python3","-I",S+"/mkpdf.py",H+"Dossier_projet_gestion_administrative_scolaire_FINAL.html",H+"Dossier_projet_gestion_administrative_scolaire_FINAL.pdf"],check=True)
def pages():
    r=PdfReader(H+"Dossier_projet_gestion_administrative_scolaire_FINAL.pdf")
    idx={id(p.indirect_reference.idnum) if False else p.indirect_reference.idnum:i+1 for i,p in enumerate(r.pages)}
    out={}
    for k,v in r.named_destinations.items():
        out[k.lstrip('/')]=r.get_destination_page_number(v)+1
    return out,len(r.pages)
prev=None
for i in range(4):
    subprocess.run(["python3","build_dossier.py"]+(["pages.json"] if prev else []),check=True,cwd=H)
    render(); pg,n=pages()
    if pg==prev: print("stable",n); break
    prev=pg; json.dump(pg,open(H+"pages.json","w"))
