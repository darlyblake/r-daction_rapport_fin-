# Rapport de vérification

## Sources examinées
Dépôt `darlyblake/Syst-me-Administratif-Scolaire` (main, cloné en lecture seule) : README, docs/, IMPLEMENTATION-ECOLE.md, POINTAGE-IMPLEMENTATION.md, PARENT-TODO.md, TODO.md, AUDIT_SETTINGS.md, code (app, hooks, services, lib, providers, components/auth), 91 migrations, 5 fonctions Edge, package.json, next.config.js, vercel.json, capacitor.config.ts, historique git. Adresse déployée : une requête le 14/10/2026.

## Tests et vérifications
- Le dépôt contient quatre fichiers de tests Jest de services et plusieurs scripts de tests manuels (authentification, emplois du temps, modales, persistance et conflits).
- Des vérifications de compilation et de déploiement ont été effectuées pendant le développement sur certaines versions. Lors de cette revue précise, la suite Jest n'a pas pu être relancée de façon fiable, l'installation des dépendances ayant échoué dans l'environnement d'audit.
- Cette impossibilité de reproduction pendant la revue ne signifie pas qu'aucun test n'a jamais été réalisé. Les résultats de chaque scénario doivent être documentés séparément lorsqu'une preuve datée est disponible.
- La page d'accueil « NOVA » était accessible lors de la consultation indiquée dans le rapport ; cela ne prouve pas à lui seul le bon fonctionnement de tous les modules.

## État par module (analyse statique)
Voir tableau « État des fonctionnalités » du dossier. Pointage : backend durci, interface présente, vérifications non cochées → Partielle. Espace parent : nombreux points non cochés → Partielle. La répartition par références directes est une heuristique qui peut devenir obsolète au fil des commits. Ne pas reprendre les anciens nombres de pages locales sans refaire l'analyse de la version exacte examinée.

## Points non vérifiables
Issues et déploiements GitHub (API inaccessible) ; correspondance entre version en ligne et HEAD ; contenu réel de la base (87 tables, RLS, définition active de `has_permission`) ; fonctions Edge non versionnées (get-parent-children, manage-teacher-account, approve-establishment-request) ; comportement hors ligne ; affichage sur téléphone.

## Écarts relevés dans le dépôt
Politiques 20261011 utilisant `settings.*`/`payments.read` absents de la dernière `has_permission` versionnée ; `ignoreBuildErrors` et `ignoreDuringBuilds` ; case « middleware » cochée à tort ; lockfile désynchronisé ; `review_attendance_justification` ouvert à tout membre non parent ; deux nomenclatures de permissions ; schéma de base non versionné ; journaux et fichiers de test à la racine (dont `enseignants-test.json` avec un champ de mot de passe : valeurs non reproduites ni vérifiées).

## État des livrables après correction
Le HTML et le script source ont été corrigés pour mieux refléter l'état du dépôt et distinguer les tests réalisés pendant le développement des scénarios non rejoués lors de cette revue. Le PDF présent dans le dépôt correspond encore à la version antérieure : il doit être régénéré à partir du HTML corrigé avant d'être remis au jury. Les anciennes conclusions de pagination et de revue visuelle ne sont donc pas considérées comme une validation du nouveau PDF.
## Limites conservées
Voir chapitre 9 et tableau « Limites du projet et perspectives ».
