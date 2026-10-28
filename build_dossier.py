#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère Dossier_projet_gestion_administrative_scolaire_FINAL.html (source modifiable du dossier).
Usage : python3 build_dossier.py [pages.json]
Les chiffres sur le dépôt sont recalculés à partir du clone local (REPO)."""
import json, os, re, sys, glob, html
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get("SAS_REPO_PATH", os.path.abspath(os.path.join(HERE, "../Syst-me-Administratif-Scolaire")))
OUT = os.path.join(HERE, "Dossier_projet_gestion_administrative_scolaire_FINAL.html")
PAGES = {}
if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
    PAGES = json.load(open(sys.argv[1], encoding="utf-8"))

esc = html.escape

# ------------------------------------------------------------------ statistiques du dépôt
def grep_names(pattern, group=1, exts=(".ts", ".tsx")):
    names = set()
    for d in ("app", "components", "hooks", "lib", "services"):
        for root, _, files in os.walk(os.path.join(REPO, d)):
            for f in files:
                if f.endswith(exts):
                    t = open(os.path.join(root, f), encoding="utf-8", errors="ignore").read()
                    names.update(re.findall(pattern, t))
    return sorted(names)

RPCS = grep_names(r"\.rpc\(\s*[\"']([a-z_0-9]+)[\"']")
TABLES_USED = grep_names(r"\.from\([\"']([a-z_0-9]+)[\"']\)")
MIG = sorted(glob.glob(os.path.join(REPO, "supabase/migrations/*.sql")))
CREATED = OrderedDict()
for f in MIG:
    t = open(f, encoding="utf-8", errors="ignore").read()
    for m in re.finditer(r"create\s+table\s+(?:if\s+not\s+exists\s+)?(?:public\.)?\"?(\w+)\"?\s*\(", t, re.I):
        CREATED.setdefault(m.group(1), os.path.basename(f)[:8])
N_PAGES = len(glob.glob(os.path.join(REPO, "app/**/page.tsx"), recursive=True))
N_MIG = len(MIG)

def classify(rpc):
    if rpc.startswith("pointage_") or rpc == "get_teacher_weekly_pointage": return "Pointage"
    if rpc.startswith("platform_admin") or rpc in ("create_platform_establishment", "set_establishment_status",
        "get_my_auth_context", "monitor_subscription_expirations", "run_subscription_expiry_monitor_internal"): return "Plateforme et authentification"
    if "support" in rpc: return "Support technique"
    if "transfer" in rpc: return "Transferts d'élèves"
    if rpc.startswith("teacher") or "teacher_establishment" in rpc or rpc == "list_active_establishments_for_teacher": return "Enseignants"
    if "attendance" in rpc: return "Présences et justificatifs"
    if "payroll" in rpc or "staff" in rpc or "establishment_member" in rpc: return "Personnel et paie"
    if "payment" in rpc or "tuition" in rpc or "finance" in rpc or "family" in rpc or rpc in ("get_effective_enrollment_fees", "add_enrollment_option"): return "Finance, familles et prises en charge"
    if "notification" in rpc or "document" in rpc: return "Notifications et documents"
    return "Élèves et inscriptions"
RPC_GROUPS = OrderedDict()
for r in RPCS:
    RPC_GROUPS.setdefault(classify(r), []).append(r)

# ------------------------------------------------------------------ numérotation (deux passes)
FIGS = OrderedDict()   # clé -> (numéro, titre)
TABS = OrderedDict()
HEADS = []             # (niveau, id, texte) pour le sommaire
_state = {"pass": 1}
FIG_NUM = {}
TAB_NUM = {}

def ref_fig(k): return f'<a class="ref" href="#fig-{k}">figure&nbsp;{FIG_NUM.get(k, "?")}</a>'
def ref_tab(k): return f'<a class="ref" href="#tab-{k}">tableau&nbsp;{TAB_NUM.get(k, "?")}</a>'

def fig(key, title, img=None, capture=False, paysage=False, note=None, h=None):
    if key not in FIGS:
        FIGS[key] = (len(FIGS) + 1, title)
    n = FIGS[key][0]
    FIG_NUM[key] = n
    if capture:
        inner = f'<div class="capture capture-vide" data-n="{n}" style="min-height:{h or 62}mm"></div>'
        if img:
            inner = f'<div class="capture"><img src="captures/{img}" alt="" onerror="this.parentNode.className=\'capture capture-vide\';this.remove()"></div>'
    else:
        inner = f'<div class="diagramme"><img src="diagrammes/exports/{img}" alt="{esc(title)}"></div>'
    cap = f'<figcaption><strong>Figure&nbsp;{n}</strong> — {esc(title)}'
    if note: cap += f'<span class="note-fig">{note}</span>'
    cap += '</figcaption>'
    body = f'<figure id="fig-{key}">{inner}{cap}</figure>'
    if paysage:
        return f'<section class="paysage">{body}</section>'
    return body

def tab(key, title, content, cls="", paysage=False, source=None):
    if key not in TABS:
        TABS[key] = (len(TABS) + 1, title)
    n = TABS[key][0]
    TAB_NUM[key] = n
    src = f'<p class="source">{source}</p>' if source else ""
    t = (f'<div class="tableau {cls}" id="tab-{key}"><div class="tab-titre"><strong>Tableau&nbsp;{n}</strong> — {esc(title)}</div>'
         f'{content}{src}</div>')
    if paysage:
        return f'<section class="paysage tab-paysage">{t}</section>'
    return t

def table(head, rows, widths=None, small=False):
    cols = ""
    if widths:
        cols = "<colgroup>" + "".join(f'<col style="width:{w}">' for w in widths) + "</colgroup>"
    th = "".join(f"<th>{h}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="{"petit" if small else ""}">{cols}<thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'

def h1(partie, ident):
    HEADS.append((0, ident, partie))
    return f'<h1 class="partie" id="{ident}">{partie}</h1>'

def chap(num, titre, ident, nouvelle_page=True):
    HEADS.append((1, ident, f"Chapitre {num}. {titre}"))
    return (f'<h2 class="chapitre{" np" if nouvelle_page else ""}" id="{ident}"><span class="num">Chapitre {num}</span>{esc(titre)}</h2>')

def sec(titre, ident=None, simple=True, hid=True):
    if simple:
        HEADS.append((0, ident, titre))
    return f'<h2 class="simple" id="{ident}">{esc(titre)}</h2>'

def p(t): return f"<p>{t}</p>"
def ul(items): return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"
def ol(items): return "<ol>" + "".join(f"<li>{i}</li>" for i in items) + "</ol>"
def h3(t): return f"<h3>{t}</h3>"

# ------------------------------------------------------------------ contenu
def contenu():
    FIGS.clear() if _state["pass"] == 1 else None
    HEADS.clear()
    o = []

    # ===== Corps =====
    o.append(sec("Introduction générale", "intro"))
    o.append(p("Dans un établissement scolaire, presque aucune tâche administrative ne se fait seule. Inscrire un élève suppose d'ouvrir son dossier, de le placer dans une classe, de calculer ce que sa famille doit payer, puis de suivre ses paiements, ses présences et ses résultats pendant toute l'année. Quand ces opérations reposent sur des registres papier, des tableurs et des messages échangés au fil de l'eau, une information mise à jour à un endroit et oubliée à un autre suffit à rendre un dossier incohérent."))
    o.append(p("C'est à partir de ce constat que j'ai choisi comme projet de fin de licence la conception et la réalisation d'une application web de gestion administrative scolaire, présentée sur sa page d'accueil sous le nom NOVA. L'idée est de regrouper dans un même outil les dossiers des élèves, les inscriptions, les frais, les présences, les notes et la communication avec les familles, et de donner à chacun un accès adapté à son rôle : un parent n'a pas à voir ce que voit la comptabilité, et un enseignant n'a pas à ouvrir les données d'un autre établissement."))
    o.append(p("La question à laquelle ce travail répond est la suivante : <em>comment concevoir et réaliser une application web qui centralise la gestion administrative d'un établissement scolaire tout en limitant l'accès de chaque utilisateur à ce que son rôle l'autorise à voir ?</em>"))
    o.append(p(f"J'ai examiné le code de la branche <code>main</code> du dépôt applicatif (commit <code>d7905796b35dc7729c08b62c9aee7df39a523ef4</code>) et l'état de la base Supabase liée le 28 octobre 2026. Je décris les choix que j'ai faits et les éléments présents dans le code : une migration SQL ne suffit pas à prouver qu'un parcours est achevé, mais l'absence d'une case cochée dans un ancien fichier Markdown ne signifie pas non plus que la fonctionnalité n'existe pas. Pour chaque domaine, je distingue donc l'interface, le branchement au backend et le niveau de vérification disponible."))
    o.append(p("Le plan suit le déroulement du projet. La première partie pose le contexte et les objectifs. La deuxième présente les besoins, les règles de gestion et le modèle de données. La troisième décrit les espaces de l'application, de la connexion à l'espace parent. La quatrième traite de l'architecture, de la sécurité et des tests. La cinquième dresse le bilan, avec ses limites et les suites envisagées."))
    o.append(p("<strong>Vocabulaire.</strong> Le produit emploie l'expression « année académique » (table <code>academic_years</code>). Je la conserve dans tout le document pour désigner la période de référence d'une inscription, et je réserve « période » aux subdivisions de cette année (trimestres ou semestres)."))

    # ----- Partie 1
    o.append(h1("Première partie — Présentation du projet", "p1"))
    o.append(chap(1, "Contexte, problématique et objectifs", "c1", False))
    o.append(h3("1.1. La gestion administrative d'un établissement"))
    o.append(p("La gestion d'une école ne s'arrête pas pendant l'année scolaire. Elle commence avec les inscriptions et les réinscriptions, se poursuit avec la répartition des élèves par niveau et par classe, puis avec le suivi des frais de scolarité, des présences et des évaluations. À cela s'ajoutent, selon les établissements, la gestion du personnel enseignant, le contrôle des heures effectuées et la communication avec les familles."))
    o.append(p("Chaque dossier d'élève réunit des éléments de natures différentes : identité, responsables légaux, parcours scolaire, situation financière, absences. Ils sont tenus par des personnes différentes, à des moments différents. C'est cette dispersion qui crée des difficultés."))
    o.append(h3("1.2. Difficultés rencontrées lorsque l'information est dispersée"))
    o.append(p("Lorsque les informations sont réparties entre plusieurs supports, une même donnée doit être recopiée à plusieurs endroits, ce qui prend du temps et multiplie les erreurs. Retrouver l'historique des paiements d'un élève ou son nombre d'absences sur un trimestre oblige à consulter plusieurs sources. Les soldes calculés à la main se trompent facilement, surtout lorsque des réductions familiales ou des prises en charge par un organisme entrent en jeu. Enfin, les familles et les enseignants n'ont pas d'accès direct et encadré à ce qui les concerne."))
    o.append(p("Ces difficultés varient d'un établissement à l'autre. Une application n'en supprime pas la totalité ; elle peut en réduire une partie, à condition d'être construite à partir des gestes réels du personnel et de rester fiable sur les montants et les droits d'accès."))
    o.append(h3("1.3. Problématique"))
    o.append(p("La question de départ a trois dimensions. Sur le plan fonctionnel, il faut déterminer les opérations à prendre en charge et leur enchaînement. Sur le plan technique, il faut choisir une architecture qui garantisse la cohérence des données et l'isolation entre établissements. Sur le plan organisationnel, il faut séparer les accès selon les rôles sans rendre l'usage pénible."))
    o.append(h3("1.4. Objectifs"))
    o.append(p("L'objectif général est de réaliser une application web de gestion administrative scolaire. Il se décline en objectifs précis, formulés pour pouvoir être vérifiés dans le code :"))
    o.append(ol([
        "regrouper les dossiers des élèves, leurs responsables légaux et leurs inscriptions dans une base partagée ;",
        "calculer et suivre les frais de scolarité, les échéanciers, les paiements, les réductions familiales et les prises en charge par un organisme ;",
        "enregistrer les présences, absences, retards et justificatifs, et le pointage des enseignants ;",
        "saisir les évaluations et les notes par classe et par matière ;",
        "offrir un espace distinct à l'administration de la plateforme, au personnel d'établissement, aux enseignants et aux parents ;",
        "isoler les données de chaque établissement ;",
        "rendre l'application accessible depuis un navigateur, sur ordinateur comme sur téléphone."]))
    o.append(h3("1.5. Périmètre"))
    o.append(p("Le projet couvre une application web responsive déployée sur Vercel, avec Supabase pour l'authentification et les données des modules raccordés au backend. L'application a évolué au fil du développement : je vérifie donc chaque domaine à partir de ses pages, hooks, services et migrations, au lieu de généraliser à partir d'un README ancien. Les dossiers <code>android</code>, <code>ios</code> et <code>electron</code> présents dans le dépôt ne suffisent pas, à eux seuls, à considérer une application mobile native ou une version de bureau comme livrée."))

    # ----- Partie 2
    o.append(h1("Deuxième partie — Analyse et conception", "p2"))
    o.append(chap(2, "Besoins, règles de gestion et modélisation", "c2", False))
    o.append(h3("2.1. Les profils d'utilisateurs"))
    o.append(p(f"L'application distingue quatre types de compte, renvoyés par la fonction <code>get_my_auth_context</code> : administrateur de plateforme, membre d'un établissement, enseignant et parent. Parmi les membres d'un établissement, la base de données reconnaît sept rôles : propriétaire (<code>owner</code>), administrateur (<code>admin</code>), direction (<code>director</code>), secrétariat (<code>secretary</code>), comptabilité (<code>accountant</code>), surveillance (<code>supervisor</code>) et enseignant (<code>teacher</code>). Le {ref_tab('roles')} résume ces profils à partir des permissions réellement codées dans la fonction SQL <code>private.has_permission</code>."))
    roles_rows = [
        ["Administrateur de plateforme", "Compte <code>platform_admin</code> (table <code>platform_admins</code>)", "Gère les établissements, les abonnements, les administrateurs et les demandes de support.", "Satisfait tous les tests de permission ; hiérarchie de permissions propre (migration <code>platform_admin_hierarchy</code>)."],
        ["Propriétaire, administrateur, direction", "Rôles <code>owner</code>, <code>admin</code>, <code>director</code>", "Gestion globale de l'établissement : membres, structure académique, élèves, inscriptions, frais, paiements, notes, présences, personnel, rapports.", "Les trois rôles ont exactement les mêmes permissions dans <code>has_permission</code>."],
        ["Secrétariat", "Rôle <code>secretary</code>", "Structure académique, élèves, inscriptions ; lecture des présences ; rapports.", "Pas de permission d'écriture sur les paiements."],
        ["Comptabilité", "Rôle <code>accountant</code>", "Frais de scolarité, paiements, rapports.", "Pas de lecture des élèves via <code>students.read</code> ; pas d'accès aux notes."],
        ["Surveillance", "Rôle <code>supervisor</code>", "Lecture des élèves et des inscriptions ; présences et pointage.", "Pas d'accès financier ni aux notes."],
        ["Enseignant", "Rôle <code>teacher</code> ou compte <code>teacher</code> lié par <code>teacher_establishments</code>", "Consultation des élèves, appel, saisie des notes, cahier de textes, pointage de ses cours.", "Un enseignant peut être rattaché à plusieurs établissements après une demande approuvée."],
        ["Parent", "Compte <code>parent</code> lié aux élèves par <code>student_guardians</code>", "Consulte la situation de ses enfants, signale une absence, demande un document.", "Accès limité aux élèves auxquels son compte est lié ; cadre à tester (chapitre 8)."],
    ]
    o.append(tab("roles", "Profils d'utilisateurs, rôles et responsabilités", table(["Profil", "Compte ou rôle dans le code", "Responsabilités principales", "Limites relevées"], roles_rows, ["17%", "23%", "34%", "26%"], small=True),
                 source="Source : <code>lib/supabase/types/roles.ts</code>, <code>supabase/migrations/20260903214000_fix_enrollment_read_permissions.sql</code>."))
    o.append(p("Les rôles personnalisés (table <code>establishment_roles</code> et <code>establishment_role_permissions</code>) existent aussi : un établissement peut définir ses propres rôles. Le code du navigateur utilise un registre de permissions plus détaillé (<code>dashboard.view</code>, <code>students.edit</code>, <code>payments.refund</code>, etc.) que celui de la fonction SQL (<code>students.read</code>, <code>students.manage</code>, <code>payments.manage</code>…). La correspondance exacte entre les deux nomenclatures n'a pas été vérifiée jusqu'au bout ; elle figure parmi les limites du chapitre 9."))

    o.append(h3("2.2. Besoins fonctionnels"))
    o.append(p(f"Le {ref_tab('bf')} liste les besoins fonctionnels retenus. La colonne de droite indique ce qui, dans le dépôt, correspond à chacun ; elle ne dit pas que la fonction est validée, ce que traite le chapitre 8."))
    bf = [
        ["BF1", "S'authentifier et récupérer son contexte (compte, établissement, rôle)", "Supabase Auth ; RPC <code>get_my_auth_context</code> ; page <code>/connexion</code>"],
        ["BF2", "Gérer les comptes et les rôles d'un établissement", "Fonctions Edge <code>manage-school-user-account</code>, <code>create-establishment-super-admin</code> ; <code>/ecole/settings</code>"],
        ["BF3", "Gérer les dossiers d'élèves et leurs responsables légaux", "RPC <code>create_student</code>, <code>update_student</code>, <code>list_students_paginated</code> ; <code>/ecole/students</code>"],
        ["BF4", "Inscrire, réinscrire et transférer un élève", "Pages <code>/ecole/inscriptions/*</code> ; RPC d'inscription, <code>create_student_transfer</code>, <code>finalize_student_transfer</code>"],
        ["BF5", "Organiser années académiques, cycles, niveaux, classes, matières, emplois du temps", "Hooks <code>useAcademicStructure</code>, <code>useClasses</code> ; services <code>matieres</code> et <code>emploi-du-temps</code>"],
        ["BF6", "Définir les frais, plans de paiement et échéanciers", "RPC <code>create_tuition_plan_with_billing</code> ; tables <code>tuition_plans</code>, <code>payment_schedules</code>"],
        ["BF7", "Enregistrer les paiements et recalculer le solde", "RPC <code>create_payment_with_allocations</code>, <code>get_payment_summary</code>"],
        ["BF8", "Appliquer des réductions familiales et des prises en charge", "Tables <code>school_families</code>, <code>family_discount_rules</code>, <code>sponsoring_organizations</code> ; migration <code>organizations_family_discounts</code>"],
        ["BF9", "Enregistrer les présences et gérer les justificatifs", "RPC <code>record_attendance</code>, <code>request_attendance_justification</code>, <code>review_attendance_justification</code>"],
        ["BF10", "Pointer l'arrivée, le départ et les cours du personnel enseignant", "Migrations <code>pointage_*</code> ; RPC <code>pointage_*</code> ; <code>/ecole/personnel/pointage</code>"],
        ["BF11", "Saisir évaluations et notes ; produire des bulletins", "Services <code>notes</code>, <code>evaluations</code> ; <code>/ecole/notes/*</code>"],
        ["BF12", "Suivre le personnel, les avances et la paie", "RPC <code>generate_payroll_period</code>, <code>create_payroll_payment</code> ; <code>/ecole/finance/paie</code>"],
        ["BF13", "Publier et demander des documents scolaires", "Tables <code>documents</code>, <code>parent_document_requests</code> ; stockage <code>school-documents</code>, <code>parent-documents</code>"],
        ["BF14", "Communiquer : notifications, messagerie, événements", "Tables <code>notifications</code>, <code>conversations</code>, <code>messages</code>, <code>school_events</code>"],
        ["BF15", "Offrir un espace parent", "Pages <code>/parents/*</code> ; hook <code>use-parent-portal</code>"],
        ["BF16", "Administrer la plateforme : établissements, abonnements, support", "Pages <code>/admin/*</code> ; RPC <code>platform_admin_*</code>"],
    ]
    o.append(tab("bf", "Besoins fonctionnels et éléments correspondants du dépôt", table(["N°", "Besoin", "Éléments du dépôt"], bf, ["8%", "42%", "50%"], small=True)))
    o.append(h3("2.3. Exigences non fonctionnelles"))
    o.append(p(f"Les exigences non fonctionnelles sont distinguées des besoins fonctionnels : elles décrivent des qualités attendues, et non des fonctions. Le {ref_tab('bnf')} indique, pour chacune, ce qui a été constaté et ce qui reste à démontrer."))
    bnf = [
        ["EX1", "Sécurité et confidentialité", "Authentification obligatoire ; fonctions SQL avec contrôle de rôle ; politiques RLS dans les migrations.", "Contrôle réel côté base non testé (chapitre 8)."],
        ["EX2", "Isolation par établissement", "Colonne <code>establishment_id</code> et appels à <code>private.has_permission</code> dans les politiques.", "Test croisé entre deux établissements non réalisé."],
        ["EX3", "Cohérence des montants", "Paiement et affectation créés dans une seule fonction SQL.", "Scénarios de solde non rejoués."],
        ["EX4", "Utilisation sur téléphone", "Mise en page responsive avec Tailwind CSS ; manifeste d'application web et service worker.", "Affichage sur téléphone non vérifié."],
        ["EX5", "Traçabilité", "Table <code>audit_logs</code> ; historique des événements de pointage.", "Couverture de l'audit non mesurée."],
        ["EX6", "Performance", "Fonctions de liste paginées côté serveur (<code>list_*_paginated</code>).", "Aucune mesure de charge."],
        ["EX7", "Maintenabilité", "Organisation page, hook, service ; types TypeScript.", "Quatre fichiers de tests seulement ; erreurs de types ignorées au build (chapitre 7)."],
    ]
    o.append(tab("bnf", "Exigences non fonctionnelles", table(["N°", "Exigence", "Constat dans le dépôt", "Limite"], bnf, ["7%", "21%", "44%", "28%"], small=True)))

    o.append(h3("2.4. Règles de gestion confirmées par le code"))
    o.append(p(f"Seules les règles que le code applique réellement sont retenues dans le {ref_tab('rg')}. Chaque règle renvoie à sa source. Une règle présente dans une ancienne feuille de route mais absente du code n'y figure pas."))
    rg = [
        ["RG1", "Un paiement est enregistré par un utilisateur authentifié ayant l'un des rôles <code>owner</code>, <code>admin</code>, <code>director</code> ou <code>accountant</code>.", "RPC <code>create_payment_with_allocations</code>"],
        ["RG2", "Un paiement vise une seule échéance, et le total des affectations est égal au montant payé ; le montant est strictement positif.", "Migration <code>20260930013000_fix_enrollment_schedule_and_sequential_payments</code>"],
        ["RG3", "Les paiements d'un échéancier suivent un ordre séquentiel.", "Même migration (paiements séquentiels)"],
        ["RG4", "Une famille est une entité explicite : les élèves y sont rattachés par <code>student_family_members</code>, et non par ressemblance de noms.", "Migration <code>20261011210000_organizations_family_discounts</code>"],
        ["RG5", "Une règle de réduction familiale précise un nombre minimal d'enfants, un type (pourcentage ou montant fixe) et des catégories de frais ; chaque réduction appliquée est conservée dans un instantané par inscription.", "Même migration (<code>family_discount_rules</code>, <code>enrollment_discount_snapshots</code>)"],
        ["RG6", "Une prise en charge par un organisme exige un organisme actif ; elle est calculée par catégorie et conservée dans un instantané.", "Même migration (<code>organization_coverage_rules</code>, <code>organization_coverage_snapshots</code>)"],
        ["RG7", "Le mode de prise en charge d'une inscription vaut <code>family</code>, <code>state</code> ou <code>other</code> ; le mode <code>state</code> exige que l'établissement l'ait activé.", "Migration <code>20261010150000_fix_enrollment_funding_and_orphans</code>"],
        ["RG8", "Une réduction familiale ou une prise en charge partielle ne s'applique qu'après l'enregistrement de l'inscription ; les paiements viennent ensuite.", "Message d'erreur de la migration <code>20261011210000</code>"],
        ["RG9", "Un justificatif d'absence ne peut être demandé que pour un élève lié à un compte parent actif ; sa revue est réservée à un membre de l'établissement qui n'est pas un parent ; le statut vaut <code>approved</code> ou <code>rejected</code>.", "Migrations <code>20261008123000</code> et <code>20261008143000</code>"],
        ["RG10", "Le pointage reconnaît quatre événements (<code>arrival</code>, <code>departure</code>, <code>course_start</code>, <code>course_end</code>) ; il exige le droit <code>attendance.manage</code> ; le code personnel est comparé par empreinte ; seul un enseignant peut pointer un début ou une fin de cours ; un cours déjà clôturé ne peut pas l'être de nouveau.", "Migrations <code>pointage_course_lifecycle_and_audit</code>, <code>pointage_security_and_admin_actions</code>"],
        ["RG11", "Les données métier portent l'identifiant de leur établissement et les politiques d'accès le comparent aux droits de l'utilisateur.", "Politiques des migrations (appels à <code>private.has_permission</code>)"],
    ]
    o.append(tab("rg", "Règles de gestion confirmées", table(["N°", "Règle", "Source"], rg, ["8%", "62%", "30%"], small=True)))

    o.append(h3("2.5. Modèle de données"))
    o.append(p(f"Le relevé direct de la base Supabase liée au projet montre 87 tables dans le schéma <code>public</code>, toutes avec la sécurité par ligne (RLS) activée, 226 politiques RLS et 232 fonctions SQL. Ces chiffres décrivent le schéma actuellement déployé ; ils ne prouvent pas, à eux seuls, que chaque opération est correctement protégée ou que l'interface utilise chaque objet."))
    o.append(p(f"Le dépôt applicatif versionne {N_MIG} fichiers SQL sous <code>supabase/migrations</code>, tandis que l'historique des migrations de la base active comporte 228 entrées au relevé du 28 octobre 2026. Ces deux nombres ne sont pas interchangeables : l'historique appliqué en base est plus large que les fichiers actuellement versionnés dans le dépôt. Cette différence limite la reproductibilité complète du schéma à partir du dépôt seul. Les relations dessinées ci-dessous sont donc de deux sortes. Un trait plein est une clé étrangère déclarée dans un fichier de migration du dépôt. Un trait pointillé est une relation observée dans les requêtes SQL des migrations, sans que la déclaration de la contrainte figure dans le dépôt. Aucune relation n'a été ajoutée par déduction à partir des seuls noms de colonnes."))
    o.append(p(f"La {ref_fig('domaines')} regroupe les tables en sept domaines. Les cinq figures suivantes détaillent les relations centrales, domaine par domaine, sans reproduire les 87 tables : elles se limitent aux tables nécessaires à la compréhension du reste du dossier."))
    o.append(fig("domaines", "Vue d'ensemble des domaines de données", "fig_vue_domaines.png", paysage=True))
    o.append(p(f"Les inscriptions, les échéanciers et les paiements ({ref_fig('erd_ins')}) forment le cœur financier : un paiement est affecté à des échéances (<code>payment_allocations</code>), et ces échéances appartiennent à une inscription. Les familles et les organismes payeurs ({ref_fig('erd_fam')}) se greffent sur ce cœur au moyen d'instantanés qui conservent, pour chaque inscription, la réduction ou la prise en charge appliquée."))
    o.append(fig("erd_ins", "Modèle de données : inscriptions, frais et paiements", "fig_erd_inscription_paiements.png",
                 note=" Trait pointillé : relation observée dans les requêtes SQL ; contrainte non déclarée dans le dépôt."))
    o.append(fig("erd_fam", "Modèle de données : familles, réductions et financement par des tiers", "fig_erd_familles_financement.png", paysage=True,
                 note=" Trait plein : clé étrangère déclarée dans une migration du dépôt ; trait pointillé : relation observée dans les requêtes."))
    o.append(p(f"La vie scolaire ({ref_fig('erd_vie')}) rassemble les présences, leurs justificatifs, les notes et les documents. Les enseignants et le cahier de textes sont représentés à part ({ref_fig('erd_ens')}), de même que le pointage ({ref_fig('erd_poi')}), dont les tables sont toutes créées par des migrations du dépôt."))
    o.append(fig("erd_vie", "Modèle de données : présences, notes et documents", "fig_erd_vie_scolaire_documents.png", paysage=True))
    o.append(fig("erd_ens", "Modèle de données : enseignants et cahier de textes", "fig_erd_enseignants_cahier.png", paysage=True))
    o.append(fig("erd_poi", "Modèle de données : pointage des enseignants", "fig_erd_pointage.png", paysage=True))
    ent = [
        ["<code>establishments</code>, <code>establishment_members</code>", "Établissements et appartenance des utilisateurs, avec leur rôle", "Établissement et accès"],
        ["<code>academic_years</code>, <code>grade_levels</code>, <code>school_classes</code>", "Années académiques, niveaux, classes", "Structure scolaire"],
        ["<code>students</code>, <code>student_guardians</code>", "Élèves et responsables légaux liés à un compte", "Structure scolaire"],
        ["<code>enrollments</code>", "Inscription d'un élève à une classe pour une année académique", "Structure scolaire"],
        ["<code>tuition_plans</code>, <code>payment_schedules</code>", "Plans de frais et échéances d'une inscription", "Finance scolaire"],
        ["<code>payments</code>, <code>payment_allocations</code>", "Paiements et leur affectation à des échéances", "Finance scolaire"],
        ["<code>school_families</code>, <code>student_family_members</code>", "Familles et rattachement explicite des élèves", "Familles et financement tiers"],
        ["<code>family_discount_rules</code>, <code>sponsoring_organizations</code>", "Règles de réduction et organismes payeurs", "Familles et financement tiers"],
        ["<code>attendance_records</code>, <code>attendance_justification_requests</code>", "Présences et demandes de justification", "Vie scolaire"],
        ["<code>assessments</code>, <code>grades</code>", "Évaluations et notes", "Vie scolaire"],
        ["<code>pointage_*</code>, <code>teacher_lesson_attendance</code>", "Codes, sessions QR, événements, alertes, séances de cours", "Personnel, pointage et paie"],
        ["<code>notifications</code>, <code>conversations</code>, <code>documents</code>", "Communication et documents scolaires", "Communication et documents"],
    ]
    o.append(tab("entites", "Principales entités de données", table(["Tables", "Rôle", "Domaine"], ent, ["38%", "40%", "22%"], small=True)))

    o.append(h3("2.6. Cas d'utilisation"))
    o.append(p(f"La {ref_fig('uc')} présente les acteurs confirmés et les actions que le code leur ouvre. Tous les acteurs ne sont pas reliés à tous les cas : par exemple, seul l'enseignant pointe un début ou une fin de cours, et seul le parent dépose un justificatif. La direction est représentée comme une spécialisation de l'administrateur d'établissement, parce que la fonction <code>private.has_permission</code> leur donne les mêmes permissions. Le cas « gérer personnel et paie » est inscrit tel que le code l'expose ; son niveau de validation est discuté au chapitre 8."))
    o.append(fig("uc", "Diagramme de cas d'utilisation de l'application", "fig_cas_utilisation.png"))

    # ----- Partie 3
    o.append(h1("Troisième partie — L'application", "p3"))
    o.append(chap(3, "Connexion, navigation et espace d'administration", "c3", False))
    o.append(h3("3.1. Accès à l'application"))
    o.append(p("L'application est déployée sur Vercel à l'adresse <a href=\"https://syst-me-administratif-scolaire.vercel.app/\">syst-me-administratif-scolaire.vercel.app</a>. Au 14 octobre 2026, une requête sur cette adresse renvoie la page d'accueil publique, intitulée « NOVA — Système de Gestion Scolaire », qui présente trois espaces (établissement, enseignant, parent) et un bouton de connexion. Le rapprochement entre la version en ligne et le dernier commit de <code>main</code> n'a pas pu être confirmé depuis l'extérieur."))
    o.append(p(f"L'authentification utilise Supabase Auth. Après la saisie de l'adresse électronique et du mot de passe, le fournisseur d'authentification de l'application appelle <code>signInWithPassword</code>, puis la fonction SQL <code>get_my_auth_context</code>, qui renvoie le type de compte, les établissements de l'utilisateur et son rôle. Un compte pour lequel aucun contexte n'est renvoyé est immédiatement déconnecté, avec le message « Votre compte n'est pas encore configuré ». La {ref_fig('seq_auth')} détaille ces étapes. La {ref_fig('cap_login')} présente la page de connexion."))
    o.append(fig("cap_login", "Page de connexion de l'application", "connexion.png", capture=True))
    o.append(fig("seq_auth", "Séquence d'authentification et de contrôle d'accès selon le rôle", "fig_sequence_authentification.png"))
    o.append(p("<strong>Ce que le contrôle d'accès est, et ce qu'il n'est pas.</strong> Selon le type de compte, l'utilisateur est redirigé vers <code>/admin</code>, <code>/etablissement</code>, <code>/enseignant</code> ou <code>/parents/tableau-de-bord</code>. Pour l'espace établissement, un composant nommé <code>PermissionRoute</code> compare la permission associée à la route aux droits du rôle et redirige vers le tableau de bord en cas de refus. Ce contrôle s'exécute dans le navigateur. Le dépôt ne contient pas de fichier <code>middleware</code> Next.js, alors qu'une ancienne feuille de route (<code>IMPLEMENTATION-ECOLE.md</code>) en mentionne un. La protection réelle des données repose donc sur les fonctions SQL et sur les politiques RLS, point développé au chapitre 7."))
    o.append(p("La récupération du mot de passe passe par un code à usage unique envoyé par courriel (page <code>/auth/mot-de-passe-oublie</code>)."))
    o.append(h3("3.2. Espace d'administration de la plateforme"))
    o.append(p("L'espace <code>/admin</code> sert à l'administration générale : liste et fiche des établissements, création d'un établissement, abonnements, administrateurs, enseignants, parents, demandes d'établissement et service technique. Il s'appuie sur une quinzaine de fonctions SQL préfixées <code>platform_admin_</code> et sur des fonctions Edge (<code>create-platform-admin</code>, <code>create-establishment-super-admin</code>). Une tâche planifiée Vercel appelle chaque jour à 7 h (UTC) la route interne <code>/api/internal/subscription-monitor</code>, qui contrôle les échéances d'abonnement. La page de paramètres de cet espace a évolué au fil des corrections ; son mode de persistance doit être confirmé à partir du parcours actuel avant d'être classé comme local ou distant."))
    o.append(h3("3.3. Espace établissement"))
    o.append(p(f"L'espace <code>/ecole</code> est le plus étendu : l'analyse statique y relève une soixantaine de pages. Il regroupe le tableau de bord, les élèves, les inscriptions, les classes et matières, l'emploi du temps, les notes, le registre d'appel, le personnel et le pointage, les finances, les documents, la communication et les paramètres. Les utilisateurs de rôle propriétaire, administrateur ou direction y disposent de tous les modules, les autres rôles de ceux que leurs permissions autorisent. La {ref_fig('cap_dash')} présente le tableau de bord."))
    o.append(fig("cap_dash", "Tableau de bord de l'espace établissement", "dashboard-admin.png", capture=True))
    o.append(p(f"Les paramètres scolaires (<code>/ecole/settings</code>) permettent de définir l'année académique, les niveaux et la structure des classes, les frais, les options, les prises en charge et les utilisateurs. La {ref_fig('cap_set')} présente la structure scolaire."))
    o.append(fig("cap_set", "Gestion des classes et structure académique", "structure-classes.png", capture=True))

    o.append(chap(4, "Scolarité : élèves, inscriptions et résultats", "c4"))
    o.append(h3("4.1. Dossiers d'élèves"))
    o.append(p(f"La liste des élèves est paginée côté serveur (<code>list_students_paginated</code>) avec recherche et filtres. Le dossier d'un élève rassemble son identité, ses responsables légaux, sa classe et ses inscriptions. Les opérations de création, de mise à jour et de désactivation passent par des fonctions SQL (<code>create_student</code>, <code>update_student</code>, <code>deactivate_student</code>) qui vérifient les droits. Un import CSV d'élèves pris en charge par l'État existe aussi (<code>import_state_students</code>). La {ref_fig('cap_eleve')} présente la liste et à la fiche d'un élève, avec des données fictives."))
    o.append(fig("cap_eleve", "Liste des élèves et fiche d'un élève (comptes de test)", "eleves.png", capture=True))
    o.append(h3("4.2. Inscription, réinscription et transfert"))
    o.append(p(f"Le formulaire d'inscription suit l'ordre de travail du secrétariat : recherche d'un dossier existant pour éviter les doublons (<code>find_duplicate_student_for_enrollment</code>), choix de l'année académique, de la classe et du plan de frais, options facultatives, puis enregistrement par une fonction SQL unique, qui crée l'élève s'il est nouveau, l'inscription et l'échéancier. Lorsque l'élève est un frère ou une sœur d'un élève déjà inscrit, ou lorsqu'un organisme prend en charge une partie des frais, l'inscription est d'abord enregistrée seule ; les réductions et prises en charge sont ensuite calculées, et les paiements sont saisis dans le module des finances (règle RG8). La {ref_fig('act_ins')} décrit ce parcours, y compris les refus du serveur, dont les messages d'erreur sont ceux du code."))
    o.append(p("La variante avec famille (<code>create_student_enrollment_with_family_funding</code>) transmet en plus l'élève apparenté, le lien de parenté et l'organisme. Le dernier commit du dépôt porte précisément sur la confirmation du code famille de l'enfant associé : cette partie évolue encore."))
    o.append(fig("act_ins", "Activité d'inscription et de réinscription", "fig_activite_inscription.png", paysage=True))
    o.append(p(f"Le transfert d'un élève entre établissements est géré comme une demande avec approbation (<code>create_student_transfer</code>, <code>review_student_transfer</code>, <code>finalize_student_transfer</code>), l'approbation étant séparée de l'inscription proprement dite (migration <code>20261011190000</code>). La réinscription conserve le dossier existant et crée une nouvelle inscription pour l'année académique suivante ; une fonction de progression académique (<code>get_student_next_academic_progression</code>) propose la classe suivante. La {ref_fig('cap_insc')} présente la liste des dossiers d'inscription, avec la colonne des responsables floutée."))
    o.append(fig("cap_insc", "Liste des dossiers d'inscription (colonne des responsables floutée)", "inscription.png", capture=True))
    o.append(h3("4.3. Classes, matières et emplois du temps"))
    o.append(p("Les cycles, niveaux, classes, matières et créneaux d'emploi du temps sont lus et écrits dans la base (services <code>classes.supabase.service.ts</code>, <code>matieres.supabase.service.ts</code>, <code>emploi-du-temps.supabase.service.ts</code>). Plusieurs commits du 11 octobre corrigent les effectifs, la répartition par niveau et le contexte d'établissement de la page des classes : ce module est donc stable depuis peu. La structure académique et l'emploi du temps utilisent des tables Supabase ; les références locales éventuellement restantes doivent être confirmées sur le parcours actuel."))
    o.append(h3("4.4. Notes, évaluations et bulletins"))
    o.append(p("Les évaluations et les notes passent par des services branchés sur la base (<code>evaluations.service.ts</code>, <code>notes.service.ts</code>, <code>periodes-notes.service.ts</code>), avec des périodes de notes par année académique. Les pages <code>/ecole/notes/saisie</code>, <code>/ecole/notes/bulletins</code> et <code>/ecole/notes/statistiques</code> existent. La page <code>/ecole/evaluation</code> doit être vérifiée séparément afin de confirmer sa source de données actuelle. Du côté parent, la feuille de route <code>PARENT-TODO.md</code> laisse non cochés les bulletins, leur téléchargement et le classement : je les considère comme non démontrés."))

    o.append(chap(5, "Finances : frais, paiements, familles et prises en charge", "c5"))
    o.append(h3("5.1. Frais, échéanciers et paiements"))
    o.append(p(f"Un plan de frais (<code>tuition_plans</code>) fixe, pour une année académique et un niveau, un mode de paiement et un montant ; ses échéances sont créées côté serveur (<code>create_tuition_plan_with_billing</code>). Chaque inscription reçoit un échéancier (<code>payment_schedules</code>). Pour enregistrer un paiement, l'interface appelle <code>create_payment_with_allocations</code>, fonction SQL unique, donc exécutée dans une seule transaction, qui vérifie le rôle, le montant, l'unicité de l'échéance visée et l'ordre séquentiel, puis insère le paiement et son affectation. Le solde affiché provient de <code>get_payment_summary</code> et <code>get_enrollment_financial_summary</code>. La {ref_fig('seq_pay')} décrit la séquence."))
    o.append(fig("seq_pay", "Séquence d'enregistrement d'un paiement et de mise à jour du solde", "fig_sequence_paiement.png"))
    o.append(p("Un paiement partiel sert ici de scénario de test, non de preuve de réussite : un versement sur la première échéance doit réduire le solde de cette échéance sans toucher aux suivantes. Ce scénario figure dans la grille du chapitre 8 avec le statut « non testé »."))
    o.append(p(f"L'historique du dépôt montre que ce module a demandé de nombreuses corrections en quelques jours (inscription exonérée affichant tout de même un montant dû, import des élèves pris en charge par l'État, affichage de l'inscription avant les échéances mensuelles). Le {ref_tab('anom')} les recense. La {ref_fig('cap_pay')} présente le suivi de la scolarité (échéances mensuelles, retards, bouton d'encaissement), avec des comptes de test."))
    o.append(fig("cap_pay", "Suivi des échéances et des versements par élève (comptes de test)", "paiements.png", capture=True))
    o.append(h3("5.2. Familles, réductions et organismes payeurs"))
    o.append(p("La notion de famille repose sur des relations explicites. Une famille (<code>school_families</code>) regroupe des élèves par l'intermédiaire de <code>student_family_members</code> ; la recherche des frères et sœurs d'un élève passe par <code>search_family_sibling_candidates</code>, qui interroge ces relations. Aucune règle ne déduit une famille d'une simple égalité de noms."))
    o.append(p("Une règle de réduction (<code>family_discount_rules</code>) fixe un nombre minimal d'enfants (au moins deux), un nombre maximal éventuel, un type (pourcentage ou montant fixe), les catégories de frais concernées (inscription, scolarité, option, caution, autre), une période de validité et un indicateur de cumul. Un organisme payeur (<code>sponsoring_organizations</code>) est associé à des règles de couverture par catégorie (<code>organization_coverage_rules</code>). Pour chaque inscription, les montants réellement déduits sont enregistrés dans des instantanés, ce qui permet de reconstituer le calcul après une modification des règles."))
    o.append(p("Quatre opérations doivent rester distinctes : le paramétrage des règles, le calcul du reste à payer, l'enregistrement d'un paiement, et la validation de l'inscription ou la confirmation de la prise en charge. La séparation est visible dans le code, où l'inscription est enregistrée avant que réductions et prises en charge ne soient appliquées. Les prises en charge par l'État disposent d'un paramétrage propre (<code>establishment_finance_settings</code>) et d'un import dédié. Les corrections répétées des 10 et 11 octobre montrent que ce domaine est récent et encore en évolution."))
    o.append(fig("cap_fam", "Prises en charge et réductions : ajout d'un organisme payeur", "familles-reductions.png", capture=True))
    o.append(h3("5.3. Comptabilité et suivi du personnel"))
    o.append(p("À côté du suivi des frais de scolarité, le dépôt contient des pages de dépenses, de caisse, d'avances, de rapports et de paie sous <code>/ecole/finance</code>, ainsi que des fonctions SQL de paie (<code>generate_payroll_period</code>, <code>create_payroll_payment</code>, <code>create_payroll_advance</code>). Ces fonctions de comptabilité générale et de paie sont distinctes du suivi des frais de scolarité. Les tables de comptabilité, de dépenses et de paie existent dans la base active. Le raccordement de chaque écran et la persistance de chaque opération doivent être vérifiés au niveau des services et des parcours ; la seule présence de ces tables ne suffit pas à conclure que le domaine est entièrement migré."))

    o.append(chap(6, "Enseignants, parents, vie scolaire et pointage", "c6"))
    o.append(h3("6.1. Espace enseignant"))
    o.append(p(f"L'espace <code>/enseignant</code> donne à l'enseignant la liste de ses établissements, de ses classes, de ses élèves, son planning, ses documents, le cahier de textes et le pointage. Un enseignant peut être rattaché à plusieurs établissements : il en fait la demande, l'établissement l'approuve ou la refuse (<code>teacher_request_establishment</code>, <code>approve_teacher_establishment_request</code>), et le contexte actif est mémorisé dans le navigateur. La {ref_fig('cap_ens')} présente cet espace."))
    o.append(fig("cap_ens", "Espace enseignant (affichage sur téléphone)", "espace-enseignant.png", capture=True))
    o.append(h3("6.2. Registre d'appel et justificatifs"))
    o.append(p(f"L'appel enregistre, pour une séance, la présence, l'absence ou le retard de chaque élève (<code>record_attendance</code>, <code>record_lesson_attendance</code>). Plusieurs commits du 8 octobre précisent le fonctionnement : vérification des appels par créneau, signalement des cours passés sans appel, distinction entre l'appel de l'enseignant et le rattrapage administratif, blocage du rattrapage des cours futurs. Un parent peut demander un justificatif pour une absence (<code>request_attendance_justification</code>) ; un membre du personnel le valide ou le refuse (<code>review_attendance_justification</code>). La {ref_fig('act_app')} décrit ces deux flux. L'appel des élèves ne doit pas être confondu avec le pointage du personnel, traité plus bas."))
    o.append(fig("act_app", "Activité du registre d'appel et du traitement des justificatifs", "fig_activite_appel.png"))
    o.append(fig("cap_appel", "Appel d'une classe dans l'espace enseignant (comptes de test)", "appel.png", capture=True))
    o.append(h3("6.3. Pointage du personnel enseignant"))
    o.append(p(f"Le pointage vise quatre événements : l'arrivée à l'établissement, le départ, le début d'un cours et la fin d'un cours. L'identification se fait par un code personnel, comparé par empreinte, ou par un QR code temporaire affiché sur un poste central et lu depuis le téléphone de l'enseignant. Pour un début de cours, le système retrouve le cours dans l'emploi du temps de l'enseignant à partir de l'heure, avec une tolérance, puis crée une séance. Les heures créditées dépendent de paramètres : durée complète si le retard ne dépasse pas un seuil, durée réduite sinon. Des alertes sont générées à partir de l'emploi du temps (cours non pointé, cours sans clôture), et une personne autorisée peut clôturer un cours avec un motif. La {ref_fig('seq_poi')} montre les trois premiers parcours et la {ref_fig('seq_ale')} la clôture administrative."))
    o.append(fig("seq_poi", "Séquence de pointage : arrivée, départ, début et fin de cours", "fig_sequence_pointage.png"))
    o.append(fig("seq_ale", "Clôture administrative d'un cours et alertes de pointage", "fig_sequence_alertes.png"))
    o.append(p("<strong>État du module.</strong> Le document de travail <code>POINTAGE-IMPLEMENTATION.md</code> indique que le backend a été audité puis renforcé (migration du 3 octobre 2026) et que la phase frontend reste à finaliser. Le code actuel montre des pages reliées aux fonctions SQL de pointage (<code>/ecole/personnel/pointage</code>, la page de lecture associée, la page de l'enseignant). En revanche, les vérifications prévues par ce même document (test du code, du QR, de l'arrivée, du départ, du calcul des heures, des droits RLS, du double pointage) sont toutes non cochées. Le module est donc présenté comme partiel : le backend est présent et durci, l'interface est présente, mais le parcours n'a pas été validé de bout en bout."))
    o.append(fig("cap_poi", "Page de pointage de l'enseignant (aucun cours en cours)", "pointage.png", capture=True))
    o.append(h3("6.4. Espace parent"))
    o.append(p(f"L'espace parent (<code>/parents</code>) est relié à la base de données et à des politiques de sécurité dédiées (plusieurs migrations d'octobre « parent_portal »). Après connexion, le parent choisit un enfant parmi ceux auxquels son compte est lié, et consulte le tableau de bord, les notes, les absences, les paiements, le cahier de textes, l'emploi du temps, les événements, les documents et les notifications. Il peut signaler une absence, déposer un justificatif (stockage <code>parent-documents</code>) et demander un document à l'établissement. L'association d'un enfant se fait par un code ou un identifiant (fonction Edge <code>claim-student</code>)."))
    o.append(p("La feuille de route <code>PARENT-TODO.md</code> est précise sur ce qui reste à faire : vérification de l'identité de l'enfant, bulletins et leur téléchargement, reste à payer, reçus, calendrier scolaire, messagerie complète, service technique, profil et paramètres du compte, et surtout la quasi-totalité des tests finaux (parent avec plusieurs enfants, accès croisé, compte désactivé, tests RLS). Ces éléments sont des limites du projet. Même les points cochés dans ce fichier ne sont pas tenus pour démontrés tant que le parcours n'a pas été exécuté."))
    o.append(fig("cap_par", "Espace parent avec un compte de test et des données fictives", "espace-parent.png", capture=True))
    o.append(h3("6.5. Documents, notifications et communication"))
    o.append(p("Les documents scolaires et les demandes de documents (<code>school_document_requests</code>, <code>parent_document_requests</code>, <code>parent_document_publications</code>) reposent sur des tables et sur deux espaces de stockage (<code>school-documents</code>, <code>parent-documents</code>) avec des liens signés. Les notifications sont lues et marquées comme lues par des fonctions SQL ; des migrations d'octobre ajoutent des notifications automatiques, notamment pour les paiements en retard. La messagerie s'appuie sur <code>conversations</code> et <code>messages</code>. Le domaine des documents est raccordé à Supabase pour plusieurs parcours, notamment les demandes et les publications ; les écrans doivent être évalués séparément pour identifier les éventuelles références locales restantes."))
    o.append(fig("cap_doc", "Documents et bulletins dans l'espace parent", "documents.png", capture=True))

    # ----- Partie 4
    o.append(h1("Quatrième partie — Réalisation technique", "p4"))
    o.append(chap(7, "Architecture, technologies et sécurité", "c7", False))
    o.append(h3("7.1. Organisation du code"))
    o.append(p(f"Le dépôt suit le principe documenté dans <code>docs/ARCHITECTURE.md</code> : page ou composant d'interface, puis hook de domaine, puis service, puis source de données. Il compte {N_PAGES} pages, 26 hooks, 56 fichiers de services dans <code>services/</code> et 21 services dans <code>lib/supabase/services/</code>. La source de données dépend du module : <code>localStorage</code> ou Supabase. La {ref_fig('archi')} représente cette organisation, avec le déploiement."))
    o.append(fig("archi", "Architecture logicielle et déploiement", "fig_architecture.png", paysage=True,
                 note=" Flèches bleues : flux applicatif ; flèches orange en pointillés : déploiement."))
    o.append(h3("7.2. Technologies"))
    techn = [
        ["Next.js 15 (15.5.24)", "Cadre applicatif : pages, routes, rendu et tâche planifiée (route interne appelée par Vercel)."],
        ["React 18 et TypeScript 5", "Composants d'interface et typage. Le fichier <code>next.config.js</code> désactive toutefois le blocage du build sur les erreurs TypeScript et ESLint."],
        ["Tailwind CSS 4", "Mise en forme et adaptation aux tailles d'écran."],
        ["Radix UI, Lucide React", "Composants d'interface accessibles et icônes."],
        ["React Hook Form et Zod", "Gestion et validation des formulaires."],
        ["Supabase (<code>supabase-js</code>)", "Authentification, base PostgreSQL, fonctions SQL (RPC), stockage de fichiers et fonctions Edge, selon les modules."],
        ["<code>localStorage</code>", "Stockage dans le navigateur pour les modules non encore migrés ; données propres à chaque appareil."],
        ["jsPDF, html2canvas, PapaParse", "Génération de documents PDF et import de fichiers CSV côté navigateur."],
        ["Jest et ts-jest", "Tests automatisés (quatre fichiers). Le paquet <code>jest</code> lui-même n'est pas déclaré dans <code>package.json</code>."],
        ["Vercel et GitHub", "Hébergement et déploiement à partir de la branche <code>main</code> ; tâche planifiée quotidienne."],
        ["Capacitor, Electron", "Préparation d'un conteneur mobile et d'une version de bureau (dossiers <code>android</code>, <code>ios</code>, <code>electron</code>) ; aucune application finale n'est démontrée."],
    ]
    o.append(tab("tech", "Technologies et rôle exact dans le projet", table(["Technologie", "Rôle exact"], techn, ["30%", "70%"], small=True)))
    o.append(p("L'application est une application web responsive. Un manifeste d'application web et un service worker de mise en cache de la page d'accueil et de la page hors ligne sont présents ; le comportement hors ligne n'a pas été testé. Ce n'est pas une application mobile native."))
    o.append(h3("7.3. Ce que « Supabase » désigne, module par module"))
    o.append(p("Dire que l'application « utilise Supabase » est insuffisant, parce que cinq situations différentes sont possibles. L'existence d'un schéma SQL n'implique pas qu'une page l'utilise. Une fonctionnalité reliée à Supabase n'a pas pour autant une interface terminée. Une politique RLS présente dans une migration n'est pas une règle vérifiée en situation. Une interface terminée n'est pas une fonctionnalité testée. Et un déploiement en ligne n'atteste que la disponibilité d'une version, non sa conformité."))
    o.append(p("Pour analyser la persistance, j'ai examiné les références au backend dans les espaces <code>/admin</code>, <code>/ecole</code>, <code>/enseignant</code> et <code>/parents</code>. Une recherche textuelle reste indicative : une page peut passer par un hook ou un service et ne contenir aucun appel direct à Supabase. Je ne reprends donc pas les anciens totaux issus d'une version précédente comme s'ils décrivaient nécessairement la version actuelle. Le constat à retenir est que Supabase est réellement intégré à plusieurs domaines, tandis que les éventuels mécanismes locaux doivent être confirmés dans les modules concernés avant d'être présentés comme une limite globale."))
    src = [
        ["Authentification, contexte de compte, administration de plateforme", "Supabase (Auth, RPC)", "Service <code>authentification.supabase.service.ts</code> ; pages <code>/admin/*</code> pour la plupart"],
        ["Élèves, inscriptions, transferts, frais, paiements, familles, organismes", "Supabase (RPC, tables)", "Services <code>lib/supabase/services</code> ; hooks <code>useStudents</code>, <code>useEnrollment</code>, <code>usePayments</code>"],
        ["Structure académique, matières, emploi du temps", "Supabase (tables)", "Services <code>*.supabase.service.ts</code>, hook <code>useAcademicStructure</code>"],
        ["Présences, justificatifs, pointage, cahier de textes", "Supabase (RPC)", "Hook <code>useAttendance</code> ; services <code>pointage</code>, <code>enseignant-pointage</code>, <code>ecole-cahier</code>"],
        ["Espaces enseignant et parent", "Supabase (RPC, tables, stockage)", "Hook <code>use-parent-portal</code> ; services <code>enseignant-portal</code>, <code>teacher-account</code>"],
        ["Classes, documents, archivage, inscriptions, paramètres, tableau de bord de l'établissement", "À confirmer module par module", "Les appels effectifs des pages et services doivent être vérifiés ; une référence à une source ne suffit pas à qualifier toute la persistance du module"],
        ["Fiche enseignant, ajout d'enseignant, évaluations, événements, heures vacataires et paramètres de plateforme", "À vérifier module par module", "Établir l'état actuel à partir des appels effectifs des pages et services ; l'ancien décompte de treize pages n'est pas repris comme une mesure actuelle."],
    ]
    o.append(tab("sources", "Source de données selon le module (analyse statique du dépôt)", table(["Module", "Source de données", "Éléments relevés"], src, ["38%", "20%", "42%"], small=True)))
    o.append(h3("7.4. Fonctionnement et enchaînement des espaces"))
    o.append(p(f"La {ref_fig('fonc')} donne la vue fonctionnelle : quatre espaces, quatre services transversaux (authentification et permissions, notifications, documents, support), puis les deux sources de données. Elle ne représente aucun service distinct : l'application est un ensemble unique déployé sur Vercel, qui interroge Supabase depuis le navigateur."))
    o.append(fig("fonc", "Vue fonctionnelle des espaces et des services transversaux", "fig_vue_fonctionnelle.png", paysage=True))
    o.append(h3("7.5. Sécurité"))
    o.append(p(f"La sécurité repose sur plusieurs couches dont la solidité est inégale. Les contrôles faits dans le navigateur (composant <code>PermissionRoute</code>, masquage de boutons) améliorent l'usage mais ne protègent pas les données, puisqu'un utilisateur peut les contourner. La protection réelle vient de la base. Les migrations du dépôt comptent 136 définitions de fonctions, dont plus de 90 déclarées avec les droits de leur propriétaire (<code>security definer</code>), 156 instructions <code>create policy</code> et 19 déclencheurs. Les fonctions de pointage, de paiement et de justificatif vérifient explicitement l'utilisateur et son rôle avant d'agir. Plusieurs migrations d'août à octobre sont consacrées à durcir les accès, notamment pour le portail parent (isolation parent-enfant, isolation entre établissements, suppression de dépendances circulaires dans les politiques) et pour retirer des droits d'exécution aux utilisateurs anonymes."))
    o.append(p("Cette protection ne suffit pas à elle seule à garantir la sécurité de l'ensemble. Trois points restent à renforcer ou à vérifier :"))
    o.append(ul([
        "<strong>Cohérence des permissions.</strong> La dernière définition versionnée de <code>private.has_permission</code> ne connaît pas les noms de permission <code>settings.read</code>, <code>settings.manage</code> et <code>payments.read</code>, alors que des politiques récentes (familles, organismes payeurs) les emploient. Une migration antérieure avait déjà remplacé ces noms pour une autre table. Selon la définition réellement active dans la base déployée, ces politiques pourraient être plus restrictives que prévu. Ce point doit être contrôlé sur la base.",
        "<strong>Versionnement incomplet du backend.</strong> L'historique Supabase comporte 228 migrations, contre 91 fichiers SQL dans ce dépôt, et 12 fonctions Edge sont actives en base ; certaines ne sont pas versionnées ici. Le schéma et le code déployés ne sont donc pas entièrement reproductibles à partir du seul dépôt.",
        "<strong>Contrôles côté serveur de l'application.</strong> Aucun middleware Next.js ne filtre les routes. L'application interroge directement Supabase depuis le navigateur avec une clé publique, ce qui est le fonctionnement normal de Supabase mais rend les règles de la base indispensables."]))
    o.append(p("Aucun secret (clé de service, jeton privé) n'est utilisé côté navigateur dans le code examiné ; la clé de service n'apparaît que dans une configuration serveur lue depuis l'environnement. Les valeurs publiques de connexion sont fournies en secours dans le code client, ce qui est sans risque pour des valeurs conçues pour être publiques, mais mérite d'être mentionné."))

    o.append(chap(8, "Tests et validation", "c8"))
    o.append(h3("8.1. Méthode et état de la vérification"))
    o.append(p("J'ai réalisé des vérifications pendant le développement, et le dépôt conserve des tests automatisés de services (comptabilité, enseignants, messages et notifications), ainsi que des scripts de tests manuels portant notamment sur l'authentification, les modales, les emplois du temps et la persistance. Des vérifications de compilation et de déploiement ont également été effectuées sur des versions antérieures. Lors de cette revue documentaire, je n'ai toutefois pas pu relancer de manière fiable toute la suite Jest, car l'installation des dépendances a échoué dans l'environnement utilisé. Cette difficulté de reproduction ne signifie donc pas qu'aucun test n'a été réalisé ; elle signifie que les résultats détaillés de tous les scénarios ne sont pas tous disponibles dans cette revue. La grille qui suit recense les scénarios à rejouer ou à documenter pour compléter la validation."))
    o.append(p(f"La grille du {ref_tab('tests')} réunit les scénarios de validation métier. Des tests manuels et des vérifications ciblées ont été réalisés pendant le développement. J'ai notamment contrôlé le schéma Supabase et ses règles RLS, vérifié une requête de l'emploi du temps qui retournait quatre créneaux visibles, et travaillé sur les corrections d'accès aux notes, aux participants de conversation et aux fichiers/documents publiés. Ces contrôles ciblés ne remplacent pas la validation complète de chaque parcours depuis l'interface. Les statuts indiquent si le résultat précis du scénario est conservé et reproductible pour la version examinée. « Non rejoué lors de cette revue » ne signifie pas que le scénario n'a jamais été testé ; cela signifie qu'aucune preuve exploitable de son exécution sur cette version n'est annexée ici. Le code qui implémente le comportement attendu n'est pas, à lui seul, une preuve de validation."))
    tests = [
        ["T01", "Connexion d'un membre d'établissement", "Compte actif et configuré", "Saisir e-mail et mot de passe, valider", "Accès à l'espace établissement", "Non rejoué lors de cette revue", "Résultat non consigné pour ce scénario", "<code>authentification.supabase.service.ts</code>"],
        ["T02", "Connexion avec identifiants invalides", "Aucune", "Saisir un mot de passe erroné", "Message « Email ou mot de passe incorrect »", "Non rejoué lors de cette revue", "Résultat non consigné pour ce scénario", "Même service"],
        ["T03", "Redirection selon le type de compte", "Un compte de chaque type", "Se connecter avec chacun", "Redirection vers <code>/admin</code>, <code>/etablissement</code>, <code>/enseignant</code>, <code>/parents/tableau-de-bord</code>", "Non rejoué lors de cette revue", "Résultat non consigné pour ce scénario", "<code>getRedirectionPath</code>"],
        ["T04", "Page non autorisée pour le rôle", "Compte secrétariat", "Ouvrir une page financière", "Redirection vers le tableau de bord", "Non rejoué lors de cette revue", "Résultat non consigné pour ce scénario", "<code>PermissionRoute.tsx</code>"],
        ["T05", "Inscription d'un nouvel élève", "Année, classe, plan de frais définis", "Remplir et valider le formulaire", "Élève, inscription et échéancier créés", "Non rejoué lors de cette revue", "Résultat non consigné pour ce scénario", "RPC d'inscription"],
        ["T06", "Inscription d'un élève pris en charge par l'État", "Option activée pour l'établissement", "Choisir le mode « État », valider", "Inscription créée sans montant familial", "Non rejoué lors de cette revue", "Résultat non consigné pour ce scénario", "Migration <code>20261010150000</code>"],
        ["T07", "Paiement partiel sur la première échéance", "Inscription avec échéancier", "Saisir un montant inférieur à l'échéance", "Solde de l'échéance réduit du montant, suivantes inchangées", "Non rejoué lors de cette revue", "Résultat non consigné pour ce scénario", "<code>create_payment_with_allocations</code>"],
        ["T08", "Paiement par un rôle non autorisé", "Compte secrétariat", "Tenter d'enregistrer un paiement", "Refus « Permission insuffisante »", "Non rejoué lors de cette revue", "Résultat non consigné pour ce scénario", "Même fonction"],
        ["T09", "Réduction familiale", "Règle active, deux enfants d'une famille", "Inscrire le second enfant", "Réduction appliquée et instantané enregistré", "Non rejoué lors de cette revue", "Résultat non consigné pour ce scénario", "Migration <code>20261011210000</code>"],
        ["T10", "Prise en charge par un organisme", "Organisme et règle actifs", "Inscrire avec l'organisme", "Part de l'organisme et part de la famille calculées", "Non rejoué lors de cette revue", "Résultat non consigné pour ce scénario", "Même migration"],
        ["T11", "Appel d'une séance", "Enseignant avec classe attribuée", "Saisir présent, absent, retard ; valider", "Présences enregistrées, statistiques mises à jour", "Non rejoué lors de cette revue", "Résultat non consigné pour ce scénario", "<code>record_attendance</code>"],
        ["T12", "Justificatif d'absence", "Absence enregistrée, parent lié", "Demande par le parent, revue par le personnel", "Statut accepté ou refusé", "Non rejoué lors de cette revue", "Résultat non consigné pour ce scénario", "Migrations <code>20261008123000</code>, <code>20261008143000</code>"],
        ["T13", "Isolation parent-enfant", "Deux parents, deux enfants", "Chercher les données de l'enfant de l'autre", "Aucune donnée renvoyée", "Non rejoué lors de cette revue", "Résultat non consigné pour ce scénario", "Migrations <code>parent_portal</code>"],
        ["T14", "Isolation entre établissements", "Deux établissements", "Tenter de lire les données de l'autre", "Aucune donnée renvoyée", "Non rejoué lors de cette revue", "Résultat non consigné pour ce scénario", "Politiques RLS"],
        ["T15", "Pointage d'arrivée par code", "Code personnel émis", "Saisir le code sur le poste central", "Événement enregistré", "Non rejoué lors de cette revue", "Résultat non consigné pour ce scénario", "<code>pointage_record_by_code</code>"],
        ["T16", "Début de cours par QR", "Cours à l'emploi du temps", "Scanner le QR dans la tolérance", "Séance créée", "Non rejoué lors de cette revue", "Résultat non consigné pour ce scénario", "<code>pointage_start_teacher_course_by_qr</code>"],
        ["T17", "Clôture administrative d'un cours", "Cours non terminé", "Clôturer avec un motif", "Cours clôturé, événement tracé", "Non rejoué lors de cette revue", "Résultat non consigné pour ce scénario", "<code>pointage_close_lesson_admin</code>"],
        ["T18", "Tests automatisés Jest", "Dépendances installées", "Lancer <code>npm test</code>", "Quatre fichiers de test réussis", "Installation des dépendances impossible dans l'environnement de vérification", "Non reproductible ici", "<code>tests/</code>"],
        ["T19", "Disponibilité de la version en ligne", "Aucune", "Requête sur l'adresse déployée", "Page d'accueil renvoyée", "Page d'accueil « NOVA » reçue le 14 octobre 2026 ; connexion non essayée", "Partiel", "Requête HTTP du 14 octobre 2026"],
        ["T20", "Affichage sur téléphone", "Téléphone ou émulation", "Parcourir les pages principales", "Mise en page utilisable", "Non rejoué lors de cette revue", "Résultat non consigné pour ce scénario", "Classes Tailwind responsive"],
    ]
    o.append(tab("tests", "Grille de tests (plan et état d'exécution)", table(["ID", "Scénario", "Précondition", "Étapes", "Résultat attendu", "Résultat observé", "Statut", "Preuve ou référence"], tests,
                 ["4.5%", "13%", "11%", "13%", "17%", "15%", "7%", "19.5%"], small=True), cls="tests", paysage=True))
    o.append(h3("8.2. Anomalies relevées"))
    o.append(p(f"Le {ref_tab('anom')} rassemble les anomalies qui ressortent de l'historique du dépôt (historique du dépôt consulté jusqu'au commit <code>d7905796b35dc7729c08b62c9aee7df39a523ef4</code>) et de l'examen du code. Pour les premières, la cause n'est pas détaillée dans les messages et la correction n'a pas été rejouée : la colonne de vérification l'indique. Les secondes sont des écarts constatés à la lecture, restés ouverts."))
    anom = [
        ["Plantage au chargement de la page des élèves", "Non précisée", "Commit du 11 octobre « Corriger le plantage au chargement de la page élèves »", "Non rejoué"],
        ["Montant dû affiché pour une inscription exonérée ; options mal cochées", "Non précisée", "Commits du 10 octobre (inscription exonérée, options scolaires)", "Non rejoué"],
        ["Import des élèves pris en charge par l'État", "Non précisée", "Commits du 10 octobre ; migration <code>20261010153000</code>", "Non rejoué"],
        ["Statistiques d'inscription fausses selon l'année académique", "Non précisée", "Commits du 11 octobre (filtre de période, pagination, statistiques)", "Non rejoué"],
        ["Politiques RLS du portail parent : dépendances circulaires", "Dépendances entre politiques, d'après le message du commit", "Commits du 8 octobre ; migrations <code>fix_parent_portal_rls_all_domains</code>, <code>fix_parent_base_access</code>", "Non rejoué"],
        ["Appel enseignant confondu avec rattrapage administratif", "Non précisée", "Commits du 8 octobre", "Non rejoué"],
        ["Noms de permission des politiques récentes non définis dans la dernière version versionnée de <code>has_permission</code>", "Définition de fonction non mise à jour (supposée)", "Aucune correction constatée", "À vérifier sur la base déployée"],
        ["Erreurs TypeScript et ESLint ignorées au build", "Options <code>ignoreBuildErrors</code> et <code>ignoreDuringBuilds</code>", "Aucune correction constatée", "Ouvert"],
        ["Feuille de route indiquant un middleware de protection des routes qui n'existe pas", "Case cochée à tort dans <code>IMPLEMENTATION-ECOLE.md</code>", "Aucune correction constatée", "Ouvert"],
        ["<code>jest</code> et <code>electron</code> absents de <code>package.json</code> alors que des scripts les appellent", "Dépendances non déclarées", "Aucune correction constatée", "Ouvert"],
        ["<code>pnpm-lock.yaml</code> désynchronisé de <code>package.json</code>", "Fichier de verrouillage non régénéré", "Aucune correction constatée", "Ouvert"],
    ]
    o.append(tab("anom", "Anomalies relevées et état de leur vérification", table(["Symptôme", "Cause (confirmée ou supposée)", "Correction", "Vérification"], anom, ["34%", "24%", "27%", "15%"], small=True)))
    o.append(h3("8.3. État des fonctionnalités"))
    o.append(p(f"Le {ref_tab('etat')} qualifie chaque fonctionnalité selon quatre niveaux. <em>Opérationnelle vérifiée</em> suppose un parcours précis exécuté avec un résultat consigné. Des vérifications manuelles et techniques ont bien été effectuées pendant le développement, mais les preuves disponibles ne permettent pas de classer tous les parcours métier dans cette catégorie. Les scénarios de la grille ci-dessous sont indiqués comme non rejoués ou non documentés lorsqu'aucun résultat spécifique n'est conservé. <em>Partielle</em> désigne une fonction dont le code ou la documentation indique des éléments manquants. <em>À vérifier</em> désigne une fonction présente dans le code, reliée à la base, dont le fonctionnement n'a pas été constaté. <em>Non implémentée</em> désigne une fonction absente du code."))
    etat = [
        ["Authentification et récupération de mot de passe", "À vérifier", "Service et pages présents ; aucun parcours rejoué"],
        ["Contrôle d'accès par rôle côté navigateur", "À vérifier", "<code>PermissionRoute</code> présent"],
        ["Middleware Next.js de protection des routes", "Non implémentée", "Aucun fichier <code>middleware</code>"],
        ["Élèves, classes, structure académique", "À vérifier", "Reliés à la base ; corrections récentes"],
        ["Inscription, réinscription, transfert", "À vérifier", "Fonctions SQL présentes ; évolutions du 11 octobre"],
        ["Frais, échéanciers, paiements", "À vérifier", "Fonction de paiement transactionnelle ; non rejouée"],
        ["Familles, réductions, organismes payeurs, élèves de l'État", "À vérifier", "Migrations du 11 octobre ; corrections répétées"],
        ["Appel et justificatifs", "À vérifier", "Fonctions SQL présentes ; non rejouées"],
        ["Notes et évaluations", "À vérifier", "Services branchés ; une page encore locale"],
        ["Bulletins", "Partielle", "Page présente côté école ; bulletins côté parent non cochés"],
        ["Pointage du personnel enseignant", "Partielle", "Backend durci ; interface à finaliser selon la documentation ; tests non réalisés"],
        ["Paie, avances, comptabilité générale", "Partielle", "Fonctions SQL présentes ; plusieurs services encore locaux"],
        ["Espace parent", "Partielle", "Base et politiques présentes ; nombreux points non cochés dans la feuille de route"],
        ["Espace enseignant (affichage sur téléphone)", "À vérifier", "Pages reliées à la base ; fiche enseignant côté école encore locale"],
        ["Documents, notifications, messagerie", "À vérifier", "Tables et stockage présents ; page documents mixte"],
        ["Administration de la plateforme", "À vérifier", "Fonctions <code>platform_admin_*</code> présentes"],
        ["Application mobile native (Capacitor)", "Non implémentée", "Dossiers générés ; aucune livraison démontrée"],
        ["Version de bureau (Electron)", "Non implémentée", "Fichiers de préparation seulement"],
    ]
    o.append(tab("etat", "État des fonctionnalités à la date de relevé", table(["Fonctionnalité", "Niveau", "Constat"], etat, ["38%", "17%", "45%"], small=True)))

    # ----- Partie 5
    o.append(h1("Cinquième partie — Bilan", "p5"))
    o.append(chap(9, "Résultats, limites et perspectives", "c9", False))
    o.append(h3("9.1. Ce qui a été réalisé"))
    o.append(p(f"J'ai réalisé une application web multi-espaces de {N_PAGES} pages applicatives, adossée à une base PostgreSQL gérée par Supabase. Le dépôt contient {N_MIG} fichiers SQL versionnés ; l'historique de la base active enregistre 228 migrations. La base compte 87 tables publiques, toutes protégées par RLS, 226 politiques RLS et 232 fonctions SQL. Supabase Auth gère l'authentification et plusieurs opérations sensibles s'appuient sur des fonctions SQL transactionnelles. Les familles, les réductions et les prises en charge par des organismes font partie des domaines développés. L'application est déployée sur Vercel à partir du dépôt GitHub. Sur le plan personnel, ce projet m'a fait parcourir le cycle d'un logiciel de gestion : modélisation, développement par modules, raccordement du backend et durcissement progressif des accès."))
    o.append(h3("9.2. Difficultés"))
    o.append(p("Les difficultés ont surtout porté sur la cohérence des données et des droits. Calculer un reste à payer exact quand se combinent paiements partiels, réductions familiales, exonérations et prises en charge a demandé plusieurs corrections. Garantir qu'un parent ne voie que ses enfants et qu'un utilisateur ne voie que son établissement a également conduit à reprendre les politiques RLS et les fonctions SQL. La migration vers une base partagée s'est faite progressivement ; certaines références à la persistance locale subsistent et doivent être évaluées au niveau de chaque parcours."))
    o.append(h3("9.3. Limites et perspectives"))
    lim = [
        ["Persistance", "Des références au stockage local subsistent dans le code, mais le périmètre exact doit être vérifié module par module ; les anciens décomptes de pages et de services ne sont pas repris comme des mesures actuelles.", "Poursuivre la revue des parcours concernés et migrer les opérations métier restantes vers une persistance partagée lorsqu'elle est encore locale."],
        ["Schéma versionné", "L'historique Supabase comporte 228 migrations, contre 91 fichiers SQL versionnés dans le dépôt ; 12 fonctions Edge sont actives en base et certaines ne sont pas versionnées.", "Réconcilier l'historique appliqué, exporter un état de référence du schéma et versionner le code des fonctions Edge déployées."],
        ["Contrôle d'accès", "L'interface utilise des contrôles de rôle et la base applique RLS ; certaines nomenclatures de permission et fonctions de validation nécessitent encore une vérification métier.", "Tester explicitement l'isolation entre établissements et entre parents ; aligner les nomenclatures et les permissions de validation."],
        ["Tests", "Quatre fichiers de tests Jest et plusieurs scripts manuels sont présents. Des tests manuels et des vérifications ciblées ont été réalisés pendant le développement ; la suite complète n'a pas été reproduite de façon fiable lors de la dernière revue.", "Conserver les résultats datés, rejouer la suite automatisée dans un environnement stable et compléter les tests sur les paiements, les permissions et les parcours parents."],
        ["Qualité de build", "Erreurs de types et d'analyse statique ignorées au build.", "Corriger les erreurs puis réactiver ces contrôles."],
        ["Pointage", "Interface à finaliser ; vérifications prévues non cochées.", "Valider le code, le QR, la clôture et le calcul des heures sur un cas réel."],
        ["Espace parent", "Bulletins, reçus, messagerie, calendrier, profil et tests finaux non démontrés.", "Compléter les points de la feuille de route, puis tester l'accès croisé."],
        ["Mobile et bureau", "Conteneurs préparés mais non livrés.", "Décider du maintien de ces pistes ; sinon retirer les dossiers générés."],
        ["Hygiène du dépôt", "Journaux de build, fichiers de test et fichiers temporaires à la racine.", "Nettoyer le dépôt et vérifier que les fichiers de test ne contiennent aucune donnée réelle."],
    ]
    o.append(tab("lim", "Limites du projet et perspectives", table(["Domaine", "Limite constatée", "Perspective"], lim, ["16%", "44%", "40%"], small=True)))
    o.append(p("Les perspectives sont des pistes de travail et non des fonctions réalisées."))

    # ----- Conclusion
    o.append(sec("Conclusion générale", "concl"))
    o.append(p("Ce projet partait d'une question concrète : comment centraliser la gestion administrative d'un établissement scolaire tout en limitant l'accès de chacun à ce que son rôle justifie. Les éléments livrés y répondent en partie. Les inscriptions, les paiements et leurs échéanciers, les présences, le pointage, les familles et les espaces par rôle existent dans le code, reliés pour la plupart à une base PostgreSQL protégée par des fonctions et des politiques d'accès."))
    o.append(p("Je ne peux pas, en revanche, affirmer davantage que ce que j'ai pu établir. Des vérifications manuelles, des tests ciblés et des contrôles de la base ont été effectués pendant le développement ; tous les parcours métier n'ont toutefois pas été rejoués avec des résultats conservés pour cette version. Des mécanismes de stockage local subsistent dans certains endroits, le pointage et plusieurs parcours de l'espace parent demandent encore une validation complète, et les règles RLS doivent continuer à être testées en situation. Le travail le plus utile à mener maintenant n'est pas d'ajouter des fonctions, mais de tester ce qui existe, de fermer les écarts relevés au chapitre 8 et de terminer la migration des données."))
    o.append(p("Ce projet m'a surtout appris qu'une application de gestion se juge moins à la quantité de ses écrans qu'à la fiabilité de ses montants et au respect des droits de chacun."))

    # ----- Références
    o.append(sec("Références", "refs"))
    refs = [
        ("Next.js", "Vercel", "Documentation de Next.js", "https://nextjs.org/docs"),
        ("React", "Meta Open Source", "Documentation de React", "https://react.dev/"),
        ("TypeScript", "Microsoft", "Documentation de TypeScript", "https://www.typescriptlang.org/docs/"),
        ("Tailwind CSS", "Tailwind Labs", "Documentation de Tailwind CSS", "https://tailwindcss.com/docs"),
        ("Supabase", "Supabase Inc.", "Documentation de Supabase", "https://supabase.com/docs"),
        ("Vercel", "Vercel Inc.", "Documentation de Vercel", "https://vercel.com/docs"),
        ("GitHub", "GitHub Inc.", "Documentation de GitHub", "https://docs.github.com/"),
    ]
    o.append("<ul class='refs'>" + "".join(f"<li>{a}. <em>{c}</em>. {b}. <a href='{u}'>{u}</a> (consulté le 14 octobre 2026).</li>" for a, b, c, u in refs) + "</ul>")
    o.append(h3("Documents internes consultés"))
    o.append(ul([
        "Dépôt GitHub du projet, branche <code>main</code>, commit <code>d7905796b35dc7729c08b62c9aee7df39a523ef4</code> consulté le 28 octobre 2026 : <a href=\"https://github.com/darlyblake/Syst-me-Administratif-Scolaire\">github.com/darlyblake/Syst-me-Administratif-Scolaire</a>.",
        "Application déployée : <a href=\"https://syst-me-administratif-scolaire.vercel.app/\">syst-me-administratif-scolaire.vercel.app</a> (consultée le 14 octobre 2026).",
        "<code>README.md</code>, <code>AGENTS.md</code>, <code>docs/ARCHITECTURE.md</code>, <code>docs/ROADMAP.md</code>, <code>docs/ARCHITECTURE-MODULES.md</code>, <code>docs/INTERFACE-UI-UX.md</code>.",
        "<code>IMPLEMENTATION-ECOLE.md</code>, <code>POINTAGE-IMPLEMENTATION.md</code>, <code>PARENT-TODO.md</code>, <code>TODO.md</code>, <code>AUDIT_SETTINGS.md</code>.",
        f"Les {N_MIG} fichiers SQL du dossier <code>supabase/migrations</code>. Le projet Supabase actif présentait 12 fonctions Edge actives au relevé ; toutes ne sont pas versionnées dans le dépôt.",
        "Code de <code>app/</code>, <code>hooks/</code>, <code>services/</code>, <code>lib/</code>, <code>providers/</code>, <code>components/auth/</code> et <code>tests/</code>."]))

    # ----- Annexes
    o.append(sec("Annexes", "annexes"))
    o.append(h3("Annexe A — Tables créées par les migrations du dépôt"))
    o.append(p(f"Le tableau suivant liste les {len(CREATED)} tables dont la création figure dans un fichier de migration versionné, avec la date de la migration (au format année, mois, jour). La différence avec le schéma déployé reflète les migrations appliquées qui ne sont pas toutes présentes comme fichiers dans ce dépôt ; les fichiers versionnés ne suffisent donc pas, à eux seuls, à reconstruire tout le schéma."))
    rows = [[f"<code>{t}</code>", d[:4] + "-" + d[4:6] + "-" + d[6:8]] for t, d in CREATED.items()]
    half = (len(rows) + 1) // 2
    comb = []
    for i in range(half):
        a = rows[i]; b = rows[i + half] if i + half < len(rows) else ["", ""]
        comb.append([a[0], a[1], b[0], b[1]])
    o.append(table(["Table", "Migration", "Table", "Migration"], comb, ["34%", "16%", "34%", "16%"], small=True))
    o.append(h3("Annexe B — Fonctions SQL appelées par l'interface"))
    o.append(p(f"L'interface appelle {len(RPCS)} fonctions SQL distinctes. Le tableau les regroupe par domaine, avec leur nombre ; la liste complète se retrouve en cherchant <code>.rpc(</code> dans le code."))
    grp_rows = [[g, str(len(v)), ", ".join(f"<code>{x}</code>" for x in v[:6]) + (", …" if len(v) > 6 else "")] for g, v in RPC_GROUPS.items()]
    o.append(table(["Domaine", "Nombre", "Exemples"], grp_rows, ["26%", "9%", "65%"], small=True))
    o.append(h3("Annexe C — Index des diagrammes et de leurs sources"))
    o.append(p("Chaque diagramme du dossier est fourni dans un format modifiable (fichiers Graphviz <code>.dot</code>, Mermaid <code>.mmd</code> ou script Python pour le diagramme de cas d'utilisation), avec un export en SVG et en PNG haute résolution. Les fichiers se trouvent dans le dossier <code>diagrammes/</code> livré avec ce dossier."))
    o.append(h3("Annexe D — Captures d'écran"))
    o.append(p("Les emplacements de captures d'écran sont signalés par un cadre vide numéroté. L'auteur les complète avec des captures de données fictives ou anonymisées, en déposant les fichiers image dans le dossier <code>captures/</code> sous les noms indiqués dans le document d'accompagnement <code>LISTE_CAPTURES_A_AJOUTER.md</code>."))
    return "\n".join(o)

# ------------------------------------------------------------------ assemblage
CSS = open(os.path.join(HERE, "dossier.css"), encoding="utf-8").read()

def toc_html():
    lignes = []
    for niv, ident, txt in HEADS:
        pg = PAGES.get(ident, "")
        lignes.append(f'<li class="niv{niv}"><a href="#{ident}"><span class="t">{esc(txt)}</span><span class="pt"></span><span class="pg">{pg}</span></a></li>')
    return "<ol class='toc'>" + "".join(lignes) + "</ol>"

def list_html(reg, prefix, label):
    out = []
    for k, (n, t) in reg.items():
        pg = PAGES.get(f"{prefix}-{k}", "")
        out.append(f'<li><a href="#{prefix}-{k}"><span class="t">{label}&nbsp;{n} — {esc(t)}</span><span class="pt"></span><span class="pg">{pg}</span></a></li>')
    return "<ol class='toc lof'>" + "".join(out) + "</ol>"

def build():
    _state["pass"] = 1
    FIGS.clear(); TABS.clear()
    contenu()                      # passe 1 : numérotation
    _state["pass"] = 2
    corps = contenu()              # passe 2 : références résolues
    toc = toc_html(); lof = list_html(FIGS, "fig", "Figure"); lot = list_html(TABS, "tab", "Tableau")
    pre = []
    pre.append("""<section class="couverture">
  <div class="haut">
    <p class="univ">Université Numérique du Gabon</p>
    <p class="pole">Pôle Sciences et Techniques de l'Ingénieur (STI)<br>Filière Développement Web et Mobile · Licence 3</p>
  </div>
  <div class="milieu">
    <div class="type">Projet de fin de licence</div>
    <h1 class="titre">Conception et réalisation d'une application de gestion administrative scolaire</h1>
    <div class="filet"></div>
  </div>
  <div class="bas"><table>
    <tr><td>Présenté par</td><td><strong>MOUEMBANZA LOUNDOU Darly Freid</strong></td></tr>
    <tr><td>Encadreur</td><td>__________________________</td></tr>
    <tr><td>Année académique</td><td>2026–2027</td></tr>
  </table></div>
</section>""")
    pre.append('<h2 class="simple front" id="remerciements" style="break-before:auto">Remerciements</h2>')
    pre.append("<p>Je remercie d'abord l'équipe pédagogique de l'Université Numérique du Gabon, et en particulier les enseignants du pôle Sciences et Techniques de l'Ingénieur, dont les cours m'ont donné les bases nécessaires pour mener ce projet.</p><p>Ma reconnaissance va aussi à mon encadreur, pour le temps qu'il m'a consacré et pour ses remarques, qui m'ont obligé à clarifier plusieurs choix.</p><p>Je remercie enfin les personnes qui ont accepté de tester l'application et de me dire franchement ce qui n'était pas clair, ainsi que ma famille et mes proches, qui m'ont soutenu pendant les longues soirées de développement.</p>")
    pre.append('<h2 class="simple front" id="resume">Résumé</h2>')
    pre.append(f"<p>Ce projet consiste à concevoir et à réaliser une application web de gestion administrative scolaire, qui regroupe les dossiers d'élèves, les inscriptions, les frais de scolarité et leurs paiements, les présences, le pointage des enseignants et la consultation par les familles, avec un espace propre à chaque type d'utilisateur.</p><p>L'application est construite avec Next.js 15, React 18, TypeScript et Tailwind CSS 4, déployée sur Vercel, et s'appuie sur Supabase pour l'authentification et les principaux domaines métier raccordés à la base. Des références au stockage local subsistent dans certains modules : leur portée doit être appréciée page et service par page et service, plutôt que généralisée à toute l'application. Pendant le développement, j'ai réalisé des vérifications manuelles et ciblées ; le dépôt contient également quatre fichiers de tests Jest et plusieurs scripts de test manuel. En revanche, la totalité des scénarios de régression n'a pas pu être rejouée de manière fiable lors de la dernière revue. Le pointage et certains parcours de l'espace parent nécessitent encore une validation complète.</p><p class='mots-cles'><strong>Mots-clés :</strong> gestion scolaire, application web, rôles et permissions, Supabase, Next.js, inscriptions et paiements.</p>")
    pre.append('<h2 class="simple front" id="sommaire">Sommaire</h2>' + toc)
    pre.append('<h2 class="simple front" id="lof">Liste des figures</h2>' + lof)
    pre.append('<h2 class="simple front" id="lot">Liste des tableaux</h2>' + lot)
    pre.append('<h2 class="simple front" id="sigles">Liste des sigles et abréviations</h2>' + SIGLES)
    doc = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Conception et réalisation d'une application de gestion administrative scolaire</title>
<style>{CSS}</style></head>
<body>
<div class="barre-impression"><button type="button" onclick="window.print()">Imprimer / Enregistrer en PDF</button></div>
<div class="feuille">
{''.join(pre)}
{corps}
</div>
<script>if(location.hash==='#travail')document.body.classList.add('travail');</script>
</body></html>"""
    open(OUT, "w", encoding="utf-8").write(doc)
    json.dump({"heads": HEADS, "figs": {k: v[0] for k, v in FIGS.items()}, "tabs": {k: v[0] for k, v in TABS.items()}},
              open(os.path.join(HERE, "registre.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("ok", len(FIGS), "figures", len(TABS), "tableaux")

SIGLES = table(["Sigle", "Signification"], [
    ["API", "Interface de programmation applicative"], ["CSS", "Feuilles de style en cascade"], ["CSV", "Valeurs séparées par des virgules (format de fichier tabulaire)"],
    ["ERD", "Diagramme entité-relation (modèle de données)"], ["FCFA", "Franc de la Coopération Financière en Afrique centrale"],
    ["HTML", "Langage à balises qui décrit la structure d'une page web"], ["HTTPS", "Protocole HTTP sécurisé par chiffrement"],
    ["JSON", "Format texte d'échange de données"], ["QR code", "Code-barres à deux dimensions, lisible avec un téléphone"],
    ["RLS", "Sécurité au niveau des lignes (règles d'accès appliquées ligne par ligne dans la base)"], ["RPC", "Appel de procédure à distance ; ici, fonction SQL appelée depuis l'interface"],
    ["SQL", "Langage de requêtes pour bases de données relationnelles"], ["STI", "Sciences et Techniques de l'Ingénieur"],
    ["UML", "Langage de modélisation unifié"], ["UNG", "Université Numérique du Gabon"], ["UI / UX", "Interface utilisateur / expérience utilisateur"]],
    ["22%", "78%"], small=True)

if __name__ == "__main__":
    build()
