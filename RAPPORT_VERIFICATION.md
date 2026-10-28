# Rapport de vérification

## Sources examinées
Dépôt applicatif `darlyblake/Syst-me-Administratif-Scolaire`, branche `main`, commit `d7905796b35dc7729c08b62c9aee7df39a523ef4`, consulté le 28 octobre 2026 : code des pages, hooks, services, composants, fichiers de configuration, tests et 91 fichiers SQL sous `supabase/migrations`. Projet Supabase actif `mogbzexqcatpgfrwzjld` consulté directement pour vérifier le schéma, les politiques RLS, les fonctions SQL, l'historique des migrations et les fonctions Edge déployées. La page de l'application a été consultée lors d'une vérification antérieure le 14 octobre 2026 ; ce constat ne vaut pas contrôle de disponibilité au 28 octobre.

## État de la base Supabase au relevé du 28 octobre 2026
- 87 tables de base dans le schéma `public` ; RLS activée sur les 87.
- 226 politiques RLS et 232 fonctions SQL dans le schéma `public`.
- 228 entrées dans l'historique des migrations appliquées, contre 91 fichiers SQL versionnés dans le dépôt applicatif. Ces nombres décrivent deux ensembles différents. L'écart signifie que l'historique complet du schéma déployé n'est pas entièrement reproductible à partir des seuls fichiers de migration du dépôt.
- 12 fonctions Edge actives dans le projet Supabase. Toutes ne sont pas versionnées dans le dépôt GitHub ; l'état déployé et le code versionné doivent donc être distingués.
- Des enregistrements existent dans plusieurs tables métier (élèves, inscriptions, paiements, présences, créneaux, demandes et publications de documents). Leur présence confirme que la base n'est pas vide, mais ne démontre pas à elle seule que tous les parcours de l'interface fonctionnent de bout en bout.

## Tests et vérifications
- Le dépôt contient quatre fichiers de tests Jest : façade de comptabilité, service des enseignants, normalisation de la messagerie et normalisation des notifications.
- Il contient aussi plusieurs scripts de tests manuels, notamment autour de l'authentification, des emplois du temps, des modales, de la persistance et des conflits.
- Des tests manuels et des vérifications ciblées ont été effectués pendant le développement. Les vérifications enregistrées dans les conversations du projet comprennent notamment des contrôles du schéma et des données Supabase, des contrôles de règles RLS et de créneaux d'emploi du temps, ainsi que des vérifications de compilation/déploiement sur des versions précédentes.
- Lors de la revue précédente, la suite Jest complète n'a pas pu être relancée de manière fiable, car l'installation des dépendances a échoué dans l'environnement utilisé. Cette impossibilité de reproduction ne signifie pas qu'aucun test n'a été réalisé.
- La grille du rapport doit donc distinguer les tests manuels déjà effectués des scénarios dont le résultat précis n'est pas conservé ou qui n'ont pas été rejoués sur la version examinée. La présence de code ou d'un fichier de test ne prouve pas, à elle seule, que le scénario métier a réussi.
- La consultation antérieure de la page d'accueil « NOVA » ne prouve pas le fonctionnement de tous les modules ni l'état actuel de production.

## État par module
Le rapport décrit les fonctions selon trois dimensions : interface présente, raccordement au backend, et validation effective. L'authentification, la gestion des élèves et inscriptions, les paiements, la structure académique, les présences, les documents, le pointage et les espaces parents/enseignants ne doivent pas être regroupés dans une seule conclusion générale. Une table ou une fonction SQL existante ne garantit pas que chaque parcours utilisateur soit finalisé ; inversement, une case non cochée dans un ancien fichier Markdown ne prouve pas que le code n'existe pas.

## Points restant à confirmer
- Rejouer les parcours de bout en bout dans un navigateur avec des comptes de test dédiés, en particulier l'isolation des établissements, l'accès parent-enfant, les paiements et leurs allocations, les justificatifs, les publications de documents, le pointage et les parcours enseignants.
- Confirmer que la version actuellement déployée sur Vercel correspond au commit applicatif examiné et refaire les vérifications sur téléphone.
- Documenter le résultat précis, la date et la version pour chaque scénario déclaré comme testé.
- Compléter la version contrôlée des migrations et des fonctions Edge afin de réduire l'écart entre l'état de Supabase et les fichiers versionnés dans GitHub.

## Écarts et points de vigilance relevés
- Les politiques et les fonctions de permission doivent être relues ensemble, car les nomenclatures employées par certaines migrations ne sont pas toujours alignées avec celles de l'application. Une fonction de justification vérifie l'appartenance à l'établissement et exclut les comptes parents ; il reste à vérifier que les rôles autorisés à valider disposent bien de la permission métier attendue.
- Le dépôt contient des réglages qui permettent au build d'ignorer certaines erreurs TypeScript/ESLint ; ces réglages ne constituent pas une preuve de qualité ni de validation.
- L'historique des migrations en base est plus étendu que les fichiers versionnés. Il faut documenter les migrations appliquées hors du dépôt ou exporter un état de référence.
- Des fichiers de test et de diagnostic à la racine méritent une revue d'hygiène. Le rapport ne reproduit aucune valeur de mot de passe ou donnée sensible découverte dans ces fichiers.

## État des livrables
Le HTML et le script de génération ont été corrigés pour décrire le projet à la première personne, s'appuyer sur les éléments réellement présents et distinguer les tests déjà réalisés des scénarios dont la preuve n'est pas disponible. Le workflow GitHub Actions a généré un nouveau PDF le 28 octobre 2026 (commit `4081787e77d84a09b8ead866509fbe97caba4781`). Le workflow a ensuite été ajusté pour enregistrer ensemble le HTML généré, la pagination et le PDF ; cette dernière exécution doit être confirmée avant la remise finale.

## Limites conservées
Voir le chapitre 9 et le tableau « Limites du projet et perspectives » du rapport.
