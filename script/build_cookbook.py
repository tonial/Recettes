import enum
import os
import shutil
from operator import itemgetter

import jinja2
import yaml


CATEGORIES = [
    "Apéro",
    "Plats Froids",
    "Plats Chauds",
    "Boulangerie",
    "Desserts",
    "Goûters",
]


class MetaEnum(enum.Enum):
    preparationtime = "Préparation"
    waitingtime = "Repos"
    bakingtime = "Cuisson"
    portion = "Portions"


ROOT_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
RECIPES_DIR = os.path.join(ROOT_DIR, "recipes")
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")
# IMGS_DIR = os.path.join(ROOT_DIR, "img")
SITE_DIR = os.path.join(ROOT_DIR, "_site")


def init_ingredients_group_dict():
    return {"list": []}


def process_recipe(RECIPE_TEMPLATE, data):
    recipe_name, _ = os.path.splitext(recipe_file)
    with open(os.path.join(RECIPES_DIR, recipe_file)) as f:
        data = yaml.safe_load(f.read())

    assert data["category"] in CATEGORIES, f"Invalid category {data['category']}"

    # Replace meta key with label
    data["meta"] = {MetaEnum[key].value: value for (key, value) in data["meta"].items()}

    # parse ingredients
    parsed_ingredients = []
    group = init_ingredients_group_dict()
    for ingredient in data["ingredients"]:
        if "|" in ingredient:
            # Close previous group
            if "title" in group:
                parsed_ingredients.append(group)
                group = init_ingredients_group_dict()

            group["title"] = ingredient[1:]  # without the starting |
        else:
            group["list"].append(ingredient)
    parsed_ingredients.append(group)
    data["ingredients"] = parsed_ingredients

    # data["graph"] = os.path.join(pic_path, data["graph"])

    filename = f"{recipe_name}.html"
    with open(os.path.join(SITE_DIR, filename), "w") as f:
        f.write(RECIPE_TEMPLATE.render(**data))

    return data["category"], {"name": data["name"], "filename": filename}


def process_index(recipes):
    for cat in CATEGORIES:
        recipes[cat] = sorted(recipes[cat], key=itemgetter("name"))
    with open(os.path.join(SITE_DIR, "index.html"), "w") as f:
        f.write(INDEX_TEMPLATE.render({"recipes": recipes}))


if __name__ == "__main__":
    os.makedirs(SITE_DIR, exist_ok=True)

    renderer = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATES_DIR))
    RECIPE_TEMPLATE = renderer.get_template("recipe.html")
    INDEX_TEMPLATE = renderer.get_template("index.html")

    # copy stylesheet
    shutil.copy2(
        os.path.join(TEMPLATES_DIR, "theme.css"),
        os.path.join(SITE_DIR, "theme.css"),
    )

    # Parsing recipes files
    print("Parsing recipes files...")
    files = [f for f in os.listdir(RECIPES_DIR) if os.path.isfile(os.path.join(RECIPES_DIR, f))]

    recipes = {cat: [] for cat in CATEGORIES}

    # create individuals recipes files
    for recipe_file in files:
        category, data = process_recipe(RECIPE_TEMPLATE, recipe_file)
        recipes[category].append(data)

    # Generate index
    process_index(recipes)

    print("done")
