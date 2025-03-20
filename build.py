import os
import sys
import re
import yaml
import shutil
import subprocess
from multiprocessing import Pool
from pathlib import Path


# Dependencies
# pip3 install pyyaml

# define directories
SOURCE_DIR = Path("source")     # Quellverzeichnis mit Markdown-Dateien
BUILD_DIR = Path("build")      # Build-Verzeichnis für den Preprocessor
HTML_DIR = Path("html")        # Zielverzeichnis für die generierten HTML-Dateien

# define templates
HTML_TEMPLATE="templates/template.html"  # Pandoc-Template für HTML-Ausgabe
DOCX_TEMPLATE="templates/template.docx"  # Falls du ein Word-Template nutzt
PDF_TEMPLATE="templates/template.tex"  # Falls du ein PDF-Template nutzt

# Pandoc command
PANDOC_CMD = Path("bin/pandoc") if Path("bin/pandoc").exists() else Path("pandoc")



# read yaml and markdown content from file
def parse_yaml(file: Path):
    """Read YAML and markdown content from a file."""

    try:
        content = Path(file).read_text(encoding="utf-8")

        match = re.match(r"---\n(.*?)\n---", content, re.DOTALL)
        if not match:
            return {}, content

        yaml_content = match.group(1)
        rest_content = content[len(match.group(0)):]

        return yaml.safe_load(yaml_content), rest_content

    except yaml.YAMLError as e:
            print(f"⚠️ Warnung: Fehler beim Parsen von YAML in {file}: {e}")
            return {}, content  # Falls ein Fehler auftritt, bleibt der Markdown-Text erhalten



def update_yaml(file: Path, new_yaml: dict):
    """Change the YAML header of a file."""
    original_yaml, content = parse_yaml(file)

    if original_yaml:
        original_yaml.update(new_yaml)
        new_yaml_text = yaml.dump(original_yaml, sort_keys=False, default_flow_style=False, allow_unicode=True)

        new_content = f"---\n{new_yaml_text}---\n{content}"
    else:
        new_content = content

    file.write_text(new_content, encoding="utf-8")




def handle_markdown_file(source_file: Path, source: Path, target: Path, navigation=None, breadcrumbs=None):
    """ Processes a single Markdown file """

    # check if file exists and ends with .md
    if not source_file.exists() or not Path(source_file).suffix == ".md":
        print(f"⚠️ Warnung: Markdown-Datei nicht gefunden: {source_file}")
        return None

    print(f"{source_file}")

    # copy file to target
    target_file = target / Path(source_file).relative_to(source)

    shutil.copy(source_file, target_file)

    # update yaml with navigation and breadcrumbs
    yaml_data, content = parse_yaml(target_file)

    if navigation:
        yaml_data["navigation"] = navigation
    if breadcrumbs:
        yaml_data["breadcrumbs"] = breadcrumbs

    update_yaml(target_file, yaml_data)



def handle_markdown_dir(directory: Path, source: Path, target: Path, breadcrumbs = []):
    """ Processes a directory recursively """

    # check if directory exists
    if not directory.exists():
        print(f"⚠️ Warnung: {directory} existiert nicht.")
        return None

    # check if an index.md exists in directory
    index_file = directory / "index.md"

    if not index_file.is_file():
        return None

    # read yaml data from index.md
    yaml_data, content = parse_yaml(index_file)


    # Process breadcrumbs
    if "title" in yaml_data:
        breadcrumbs.append({"title": yaml_data["title"], "url": index_file})

    # Create a deep copy of breadcrumbs for relative paths
    relative_breadcrumbs = []
    for crumb in breadcrumbs:
        rel_path = os.path.relpath(crumb["url"], directory)
        relative_breadcrumbs.append({"title": crumb["title"], "url": rel_path})


    # Process navigation
    navigation =  yaml_data.get("navigation", [])
    if not isinstance(navigation, list):
        print(f"⚠️ Warnung: Ungültige Navigation in {index_file}")
        navigation = []

    # read titles from markdown files
    for item in navigation:

        if "url" not in item:
            print("⚠️ Warnung: Navigation item is missing url.", item)
            continue

        if "title" not in item:
            item_url = Path(item["url"])
            item_path = directory / item_url

            yaml_item_data, content = parse_yaml(item_path)

            if "title" in yaml_item_data:
                item["title"] = yaml_item_data["title"]
            else:
                item["title"] = item_url

    # create target directory
    target_dir = target / directory.relative_to(source)

    if not target_dir.exists():
        Path(target_dir).mkdir(parents=True, exist_ok=True)


    # recursively process subdirectories and files
    for item in yaml_data["navigation"]:
        item_url = Path(item["url"])

        # item is in a subdirectory of source
        item_dir = directory / Path(item_url).parent
        if item_dir.exists() and item_dir != directory:
            handle_markdown_dir(item_dir, source, target, breadcrumbs)
            continue

        # item is a file
        item_file = directory / item_url
        if item_file.exists():
            handle_markdown_file(item_file, source, target, navigation, relative_breadcrumbs)

    # remove breadcrumb for this directory
    if breadcrumbs:
        breadcrumbs.pop()



def clear_and_create_dir(directory: Path):
    """Delete the entire directory and create it again"""
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True, exist_ok=True)



include_cache = {}
def resolve_includes(file: Path, source: Path, build: Path, remove_yaml_header=False):
    """ Resolve all !include statements """

    if file in include_cache:
        return include_cache[file]

    if not file.exists():
        print(f"⚠️ Warnung: Datei nicht gefunden: {file}")
        include_cache[file] = None
        return f"[Fehlendes Include: {file}]\n"

    if remove_yaml_header:
        yaml, content = parse_yaml(file)
    else:
        content = file.read_text(encoding="utf-8")

    resolved_content = []
    for line in content.splitlines():
        match = re.match(r'^\s*!include\s+(["\']?)([^"\']+)\1\s*$', line.strip())

        if match:

            # file can be in build or source
            rel_path = os.path.relpath(file.parent, build)

            include_file = source / rel_path / match.group(2)

            if include_file.exists():
                print("include:", include_file)

                # Vor dem Include: Quellverzeichnis einfügen
                resolved_content.append(f"<!--- base_path: {include_file.parent} -->")

                # Inhalt der Include-Datei einfügen
                resolved_content.append(resolve_includes(include_file, source, build, True))

                # Nach dem Include: Zielverzeichnis einfügen
                resolved_content.append(f"<!--- base_path: {file.parent} -->")

            else:
                print(f"⚠️ Warnung: Datei nicht gefunden: {include_file}")
                resolved_content.append(f"\n[Fehlendes Include: {include_file}]\n")
        else:
            resolved_content.append(line)

    resolved_string = "\n".join(resolved_content)

    # Cache the resolved string
    include_cache[file] = resolved_string

    return resolved_string



def handle_includes(source: Path, build: Path):
    """Verarbeitet alle Markdown-Dateien im Build-Verzeichnis und löst `!include`-Anweisungen auf."""
    for md_file in Path(build).rglob("*.md"):
        print(f"{md_file}")
        resolved_content = resolve_includes(md_file, source, build)
        md_file.write_text(resolved_content, encoding="utf-8")


def copy_embedded_assets(source: Path, build: Path):
    """ Kopiert alle referenzierten Bilder unter Berücksichtigung von base_path in das Build-Verzeichnis """

    processed_assets = set()

    for md_file in Path(build).rglob("*.md"):
        content = Path(md_file).read_text(encoding="utf-8").splitlines()

        # Standard base_path ist das Verzeichnis der Markdown-Datei
        current_base_path = source / md_file.parent.relative_to(build)

        resolved_content = []
        for line in content:
            # Prüfe auf base_path Anweisung
            match_base_path = re.match(r'<!---\s*base_path:\s*(.*?)\s*-->', line)
            if match_base_path:
                current_base_path = Path(match_base_path.group(1))
                print(f"base_path gesetzt auf: {current_base_path}")
                continue

            # Prüfe auf Bildreferenzen
            match_asset = re.match(r'!\[(.*?)\]\((.*?)\)', line)
            if match_asset:
                asset_file_rel = match_asset.group(2)
                asset_path = Path(asset_file_rel)

                # Bestimme den Quell- und Zielpfad basierend auf base_path
                target_file = md_file.parent / asset_path
                source_file = current_base_path / asset_path

                if source_file in processed_assets:
                    continue

                if source_file.exists():
                    target_file.parent.mkdir(parents=True, exist_ok=True)

                    try:
                        shutil.copy(source_file, target_file)
                        processed_assets.add(source_file)
                        print(f"Kopiert: {source_file}")
                    except (FileNotFoundError, PermissionError) as e:
                        print(f"⚠️ Warnung: Fehler beim Kopieren: {source_file} ({e})")

                else:
                    print(f"⚠️ Warnung: Datei nicht gefunden: {source_file}")



'''
def copy_embedded_assets(source: Path, build: Path):
    """ Copies all referenced images into the build directory """

    processed_assets = set()

    for md_file in Path(build).rglob("*.md"):

        content = Path(md_file).read_text(encoding="utf-8")

        matches = re.findall(r'!\[(.*?)\]\((.*?)\)', content)

        for match in matches:
            asset_file_rel = match[1]

            md_path = md_file.parent
            rel_path = md_path.relative_to(build)

            target_file = md_path / asset_file_rel
            source_file = source / rel_path / asset_file_rel

            if source_file in processed_assets:
                continue

            if source_file.exists():
                target_file.parent.mkdir(parents=True, exist_ok=True)

                try:
                    shutil.copy(source_file, target_file)
                    processed_assets.add(source_file)
                    print(f"{target_file}")
                except (FileNotFoundError, PermissionError) as e:
                    print(f"⚠️ Warnung: Fehler beim Kopieren: {source_file} ({e})")

            else:
                print(f"⚠️ Warnung: Datei nicht gefunden: {source_file}")
'''


def copy_static_assets(build: Path, target: Path):
    """ Kopiert alle Assets (Bilder, Medien) ins Zielverzeichnis """

    copied_assets = set()

    for asset_file in build.rglob("*"):
        if asset_file.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".js", ".html", ".css"}:
            target_file = target / asset_file.relative_to(build)

            if target_file in copied_assets:
                continue  # Vermeide doppeltes Kopieren

            target_file.parent.mkdir(parents=True, exist_ok=True)

            try:
                shutil.copy2(asset_file, target_file)
                copied_assets.add(target_file)
                print(f"{target_file}")
            except (FileNotFoundError, PermissionError) as e:
                print(f"⚠️ Warnung: Fehler beim Kopieren: {asset_file} ({e})")



def execute_pandoc(input_file: Path, parameters):
    """Führt einen Pandoc-Befehl aus und überprüft Fehler."""
    output_file = parameters[-1]  # Letzter Parameter ist "--output <file>"

    command = [PANDOC_CMD, input_file] + parameters
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"⛔ Fehler: Konvertierung fehlgeschlagen für {input_file}:\n{result.stderr.strip()}")
        return False

    if not Path(output_file).exists():
        print(f"⛔ Fehler: Ausgabe-Datei wurde nicht erstellt: {output_file}")
        return False

    print(f"{output_file}")
    return True



def convert_single_file(args):
    """Hilfsfunktion für parallele Konvertierung einer Datei."""
    md_file, output_file, format, format_params = args

    execute_pandoc(md_file, format_params + ["--output", output_file])



def convert_markdown(build, target, format):
    """ Konvertiert alle Markdown-Dateien im Build-Verzeichnis """

    if format not in ["html", "pdf", "docx"]:
        print(f"⛔ Fehler: Ungültiges Format: {format}")
        return False

    if Path(DOCX_TEMPLATE).is_file():
        str_docx_template = str(Path(DOCX_TEMPLATE).resolve())
    else:
        str_docx_template = None

    format_params = {
        "html": ["--lua-filter", "bin/navigation.lua", "--mathjax", "--template", HTML_TEMPLATE],
        "docx": ["--reference-doc", str_docx_template] if str_docx_template else [],
        "pdf": ["--pdf-engine=lualatex", "--template", PDF_TEMPLATE]
    }.get(format, [])

    tasks = []

    for md_file in Path(build).rglob("*.md"):
        output_file = target / md_file.parent.relative_to(build) /  md_file.with_suffix(f".{format}").name

        # create folder if necessary
        output_file.parent.mkdir(parents=True, exist_ok=True)

        tasks.append((md_file, output_file, format, format_params))

    with Pool() as pool:
            pool.map(convert_single_file, tasks)



def check_dependencies():
    """ Prüft, ob alle benötigten Programme installiert sind. """

    if shutil.which(PANDOC_CMD) is None:
        print("⛔ Fehler: Pandoc wurde nicht gefunden!")
        sys.exit(1)

    if shutil.which("lualatex") is None:
        print("⚠️ Warnung: lualatex fehlt, PDF-Erstellung könnte fehlschlagen.")



# Hauptprogramm
if __name__ == "__main__":
    check_dependencies()

    print("\n\nSchritt 1: Kopiere Markdown-Dateien nach", BUILD_DIR)
    clear_and_create_dir(BUILD_DIR)
    handle_markdown_dir(SOURCE_DIR, SOURCE_DIR, BUILD_DIR)

    print("\n\nSchritt 2: Suche nach !includes in", BUILD_DIR)
    handle_includes(SOURCE_DIR, BUILD_DIR)

    print("\n\nSchritt 3: Kopiere Assets nach", BUILD_DIR)
    copy_embedded_assets(SOURCE_DIR, BUILD_DIR)

    print("\n\nSchritt 4: Konvertiere in HTML-Dateien ", HTML_DIR)
    clear_and_create_dir(HTML_DIR)
    convert_markdown(BUILD_DIR, HTML_DIR, "html")

    print("\n\nSchritt 5: Kopiere Assets nach", HTML_DIR)
    copy_static_assets(BUILD_DIR, HTML_DIR)

    print(f"\nErledigt")
