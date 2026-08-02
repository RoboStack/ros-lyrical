#!/usr/bin/env python3
"""Replace GitHub tag clones in generated recipes with archive downloads.

ROS release repositories contain hundreds of package tags. Reusing one mutable
Git clone cache for those tags can leave refs without objects, especially on
macOS. GitHub's immutable tag archives avoid that cache failure entirely.
"""

from pathlib import Path
import re

RECIPES = Path("recipes")
SOURCE = re.compile(
    r"^(?P<indent>\s*)git: (?P<url>https://github\.com/[^\s]+?)(?:\.git)?\n"
    r"(?P=indent)tag: (?P<tag>[^\n]+)$",
    re.MULTILINE,
)

converted = 0
for recipe in RECIPES.rglob("recipe.yaml"):
    text = recipe.read_text(encoding="utf-8")

    def replace(match: re.Match[str]) -> str:
        global converted
        converted += 1
        url = match.group("url").removesuffix(".git")
        return (
            f'{match.group("indent")}url: '
            f'{url}/archive/refs/tags/{match.group("tag")}.tar.gz'
        )

    updated = SOURCE.sub(replace, text)
    if updated != text:
        recipe.write_text(updated, encoding="utf-8")

print(f"Converted {converted} GitHub tag sources to archives")
