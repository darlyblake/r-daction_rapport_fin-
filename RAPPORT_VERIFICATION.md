# Rapport de vérification

## Sources examinées
Dépôt `darlyblake/Syst-me-Administratif-Scolaire` (main, cloné en lecture seule) : README, docs/, IMPLEMENTATION-ECOLE.md, POINTAGE-IMPLEMENTATION.md, PARENT-TODO.md, TODO.md, AUDIT_SETTINGS.md, code (app, hooks, services, lib, providers, components/auth), 85 migrations, 5 fonctions Edge, package.json, next.config.js, vercel.json, capacitor.config.ts, historique git. Adresse déployée : une requête le 14/10/2026.

## Tests réellement exécutés
- Aucun test Jest : `npm ci`, `npm install` et `pnpm install --frozen-lockfile` ont échoué (lockfile désynchronisé ; bug npm). `jest` et `electron` ne sont pas déclarés dans package.json.
- Aucun parcours applicatif rejoué (pas de compte de test).
- Seul constat : l'URL déployée renvoie la page d'accueil « NOVA ».

## État par module (analyse statique)
Voir tableau « État des fonctionnalités » du dossier. Pointage : backend durci, interface présente, vérifications non cochées → Partielle. Espace parent : nombreux points non cochés → Partielle. Source de données : 71 pages Supabase, 13 locales, 7 mixtes, 34 sans référence directe (heuristique).

## Points non vérifiables
Issues et déploiements GitHub (API inaccessible) ; correspondance entre version en ligne et HEAD ; contenu réel de la base (87 tables, RLS, définition active de `has_permission`) ; fonctions Edge non versionnées (get-parent-children, manage-teacher-account, approve-establishment-request) ; comportement hors ligne ; affichage sur téléphone.

## Écarts relevés dans le dépôt
Politiques 20261011 utilisant `settings.*`/`payments.read` absents de la dernière `has_permission` versionnée ; `ignoreBuildErrors` et `ignoreDuringBuilds` ; case « middleware » cochée à tort ; lockfile désynchronisé ; `review_attendance_justification` ouvert à tout membre non parent ; deux nomenclatures de permissions ; schéma de base non versionné ; journaux et fichiers de test à la racine (dont `enseignants-test.json` avec un champ de mot de passe : valeurs non reproduites ni vérifiées).

## Contrôles du PDF final
Recherche de formules interdites : aucune. Références de figures et tableaux : toutes résolues (27 figures, 11 tableaux). Aucune clé, e-mail ou mot de passe dans le texte. Pagination stable (65 pages). Revue visuelle par planches : pas de débordement, quelques tableaux coupés entre pages avec en-tête répété.
## Limites conservées
Voir chapitre 9 et tableau « Limites du projet et perspectives ».
