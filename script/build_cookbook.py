import enum
import glob
import os
import shutil
from operator import itemgetter
from pathlib import Path

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


def init_ingredients_group_dict():
    return {"list": []}


class CookBookGenerator:
    def __init__(self):
        root_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
        self.templates_dir = os.path.join(root_dir, "templates")
        # imgs_dir = os.path.join(ROOT_DIR, "img")
        self.site_dir = os.path.join(root_dir, "_site")

        # Load jinja2 templates
        renderer = jinja2.Environment(loader=jinja2.FileSystemLoader(self.templates_dir))
        self.recipe_template = renderer.get_template("recipe.html")
        self.index_template = renderer.get_template("index.html")

    def validate_recipe(self, data):
        if data["category"] not in CATEGORIES:
            raise ValueError(f"Invalid category {data['category']}")

    def process_recipe(self, recipe_file):
        recipe_name = Path(recipe_file).stem
        with open(recipe_file) as f:
            data = yaml.safe_load(f.read())

        self.validate_recipe(data)

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

        html_file = f"{recipe_name}.html"
        with open(os.path.join(self.site_dir, html_file), "w") as f:
            f.write(self.recipe_template.render(**data))

        self.recipes[data["category"]].append(
            {
                "name": data["name"],
                "filename": html_file,
                "tags": data["tags"] or [],
            }
        )

    def process_index(self):
        for cat in CATEGORIES:
            self.recipes[cat] = sorted(self.recipes[cat], key=itemgetter("name"))
        with open(os.path.join(self.site_dir, "index.html"), "w") as f:
            f.write(self.index_template.render({"recipes": self.recipes}))

    def build(self):
        # Create empty _site folder (and remove old content if there was any)
        shutil.rmtree(self.site_dir, ignore_errors=True)
        os.makedirs(self.site_dir)

        # Copy stylesheet
        shutil.copy2(
            os.path.join(self.templates_dir, "theme.css"),
            os.path.join(self.site_dir, "theme.css"),
        )

        # Process recipes files
        self.recipes = {cat: [] for cat in CATEGORIES}
        files = glob.glob(r"recipes/[!_]*.yaml")
        for recipe_file in files:
            self.process_recipe(recipe_file)
        self.process_index()

        print("Done")


if __name__ == "__main__":
    CookBookGenerator().build()
