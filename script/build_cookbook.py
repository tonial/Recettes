import enum
import glob
import os
import re
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


SECTIONS = {
    "Ingrédients": "ingredients",
    "Préparation": "steps",
    "Conseils": "hints",
}

LIST_ITEM_RE = re.compile(r"^(?:[-*+]|\d+[.)])\s+(.*)$")


def parse_list(lines):
    """Return the items of a markdown list (bullet or numbered), joining continuation lines."""
    items = []
    for line in lines:
        if match := LIST_ITEM_RE.match(line):
            items.append(match.group(1).strip())
        elif line.strip():
            if not items:
                raise ValueError(f"Unexpected text outside of a list: {line!r}")
            items[-1] += " " + line.strip()
    return items


def parse_recipe(text):
    """Parse a markdown recipe: YAML front matter, `# Name` title and `## Section` lists."""
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not match:
        raise ValueError("Missing YAML front matter")
    data = yaml.safe_load(match.group(1)) or {}
    data["meta"] = {key: data.pop(key.name, "") for key in MetaEnum}

    sections = {}
    current = None
    for line in match.group(2).splitlines():
        if line.startswith("# "):
            data["name"] = line[2:].strip()
            current = None
        elif line.startswith("## "):
            title = line[3:].strip()
            if title not in SECTIONS:
                raise ValueError(f"Unknown section {title!r} (expected one of {list(SECTIONS)})")
            current = sections.setdefault(SECTIONS[title], [])
        elif current is not None:
            current.append(line)
        elif line.strip():
            raise ValueError(f"Unexpected text outside of a section: {line!r}")

    if "name" not in data:
        raise ValueError("Missing `# Name` title")

    # Ingredients may be divided into groups using `### Group title` sub-headings
    groups = [{"lines": []}]
    for line in sections.get("ingredients", []):
        if line.startswith("### "):
            groups.append({"title": line[4:].strip(), "lines": []})
        else:
            groups[-1]["lines"].append(line)
    data["ingredients"] = [
        {**({"title": group["title"]} if "title" in group else {}), "list": parse_list(group["lines"])}
        for group in groups
        if "title" in group or parse_list(group["lines"])
    ]

    data["steps"] = parse_list(sections.get("steps", []))
    data["hints"] = parse_list(sections.get("hints", []))
    return data


class CookBookGenerator:
    def __init__(self):
        root_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
        self.recipes_dir = os.path.join(root_dir, "recipes")
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
        with open(recipe_file, encoding="utf-8") as f:
            try:
                data = parse_recipe(f.read())
            except ValueError as e:
                raise ValueError(f"{recipe_file}: {e}") from e

        self.validate_recipe(data)

        # Replace meta key with label
        data["meta"] = {key.value: data["meta"][key] for key in MetaEnum}

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
        files = glob.glob(os.path.join(self.recipes_dir, "[!_]*.md"))
        for recipe_file in files:
            self.process_recipe(recipe_file)
        self.process_index()

        print("Done")


if __name__ == "__main__":
    CookBookGenerator().build()
