# Décisions appliquées (audit et finalisation)

Instructions suivies : « PROMPT MAÎTRE » fourni, avec la correction de l'auteur : **STI = Sciences et Techniques de l'Ingénieur** (remplace « Technologies de l'Information » du prompt).

## Décisions
- L'ancien PDF n'est pas une source de vérité ; tout le contenu vient de l'audit du dépôt (branche `main`, dernier commit du 12/10/2026), des 85 migrations et de l'adresse déployée.
- Corrections majeures : il n'existe **pas de middleware Next.js** (contrôle de route côté navigateur par `PermissionRoute`, protection réelle par RPC et RLS) ; l'application est web responsive, pas mobile native ; Capacitor et Electron = préparation seulement.
- Aucune fonctionnalité n'est classée « Opérationnelle vérifiée » : aucun test n'a pu être exécuté. Statuts utilisés : Partielle / À vérifier / Non implémentée. Grille de tests : tout « Non testé », sauf T19 (page d'accueil en ligne reçue) « Partiel ».
- Les 87 tables (RLS partout) sont citées comme relevé de l'auteur ; les migrations versionnées n'en créent que 28 (annexe A).
- Aucune fausse capture : cadres vides numérotés (voir `LISTE_CAPTURES_A_AJOUTER.md`). Aucune donnée réelle, aucun secret.
- Couverture : « Encadreur : ____ » laissé vierge. Un seul résumé, sommaire / listes avec numéros de page calculés par double passe de rendu.
- Anomalies : seules celles issues de l'historique de commits ou de l'examen du code ; vérifications marquées « Non rejoué » ou « À vérifier ».
- Format source modifiable : HTML (`Dossier_projet_gestion_administrative_scolaire_FINAL.html`, généré par `build_dossier.py` + `dossier.css`). Pas de DOCX.

## Régénérer
`python3 build_dossier.py` puis `python3 paginate.py` (HTML, PDF, numéros de pages).
