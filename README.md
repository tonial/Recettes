# Recettes

Ce repo contient les sources pour générer nos recettes en version HTML.
Le livre de recettes est accessible [ici](https://tonial.github.io/Recettes/).

## Ajouter une recette

Les recettes sont au format Markdown dans le dossier `recipes/`. Il suffit de copier le fichier `recipes/_template.md` pour avoir un fichier au bon format.

Voici quelques règles :
- Les métadonnées (catégorie, temps, portions, tags, source) sont dans l'en-tête YAML, entre les deux lignes `---`.
- La catégorie doit être un des éléments présent dans la liste `CATEGORIES` du script `build_cookbook.py`.
- Le nom de la recette est le titre `# ...`.
- Les sections sont `## Ingrédients` (liste à puces), `## Préparation` (liste numérotée) et `## Conseils` (liste à puces, facultative).
- Les ingrédients peuvent être divisés en sous listes avec des sous-titres `### ...` (voir la recette `blueberry_muffins.md` pour un exemple).

## Fonctionnement

À chaque push sur la branche `main` le workflow GitHub `publish` se lance et exécute le script `build_cookbook.py` qui génère les fichiers HTML et les uploads sur GitHub Pages.

La génération des fichiers est faite à l'aide de template HTLM et de la librairie jinja2.