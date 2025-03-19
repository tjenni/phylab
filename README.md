# PhyLab

## Einleitung

Dieses Projekt ermöglicht die Erstellung und Verwaltung gemeinsamer digitaler Unterlagen **Markdown**. Die Inhalte werden mit Pandoc aus Markdown-Dateien in verschiedenen Formaten wie HTML, PDF und DOCX konvertiert. Der Fokus liegt auf einer einfachen, aber flexiblen Struktur für Lehrmaterialien. 

## Inhaltsverzeichnis

- [Verzeichnisstruktur](#verzeichnisstruktur)
- [Markdown-Syntax](#markdown-syntax)
- [Voraussetzungen](#voraussetzungen)
- [Installation](#installation)
- [Workflow für Teilnehmer](#workflow-für-teilnehmer)
- [Erstellung eines Releases](#erstellung-eines-releases)
- [Lizenz](#lizenz)

## Verzeichnisstruktur

Die Struktur des Projekts ist folgendermassen aufgebaut:

```
/
├ bin/          (Skripte wie Lua-Filter, usw.)
├ html/         (Generierte Ausgabe)
├ build/        (Temporäres Build-Verzeichnis)
├ source/       (Markdown Quelldateien und zugehörige Ressourcen)
    ├ assets/              (Resourcen Bilder, Videos, ...)
    ├ mechanik/            (Kapitel)
        ├ assets/             (Resourcen Bilder, Videos, ...)
        ├ index.md            (Startseite für das Kapitel)
        ├ dichte.md           (Unterkapitel)
        ├ kinematik/          (Unterunterkapitel)
            ├ assets/            (Resourcen Bilder, Videos, ...)
            ├ index.md           (Startseite für das UnterunterKapitel)
        ├ dichte.md
            ├ ...
        ├ ...
    ├ waermelehre/         (Kapitel)
        ├ assets/             (Resourcen Bilder, Videos, ...)
        ├ index.md            (Einstieg)
        ├ celsius.md          (Unterkapitel)
        ├ ...
    ├ ...
    ├ index.md             (Startseite)
├ templates/    (Vorlagen für HTML, DOCX und PDF)
├ LICENSE.md    (Projektlizenz)
├ README.md     (Dieses Dokument)
├ build.py      (Skript zum Generieren der HTML-Seite)
```

Der Ordner `source` enthält die Markdown-Quelldateien und ihre zugehörigen Ressourcen wie Bilder und Videos. Die Verzeichnisstruktur kann beliebig tief verschachtelt werden. Entscheidend ist, dass sich auf jeder Ebene eine `index.md`-Datei als Einstiegspunkt befindet und ein `assets`-Ordner für Medieninhalte vorhanden ist. 

## Markdown-Syntax

Die Inhalte werden in **Markdown** geschrieben. Neben den Standard-Elementen wie Überschriften, Listen und Tabellen werden spezielle Syntaxelemente für Hinweise und Formeln unterstützt:

### Hinweise (Admonitions)

Folgende Blöcke stehen zur Verfügung:

```markdown
::: info
**Information:**
Hier steht ein wichtiger Hinweis.
:::
```

```markdown
::: warning
**Achtung:**
Hier steht eine Warnung.
:::
```

```markdown
::: solution
**Lösung:**
Hier steht eine Lösung, die ausklappbar ist.
:::
```

### Formeln

Formeln werden in **LaTeX-Syntax** geschrieben und mit `$...$` für Inline-Formeln oder `$$...$$` für Block-Formeln dargestellt.

```markdown
Die Formel für die Energie ist $E = mc^2$.
```

```markdown
$$F = G rac{m_1 m_2}{r^2}$$
```

## Voraussetzungen

Das Projekt benötigt folgende Software:

- **Python 3** (mit `pyyaml`)
- **Pandoc** ([https://pandoc.org/](https://pandoc.org/))
- **Git** (für die Zusammenarbeit)

### Installation unter macOS

Auf macOS ist Python 3 bereits installiert. Pandoc ist im `bin`-Verzeichnis vorhanden. Einzig das Modul `pyyaml` muss installiert werden. 

```sh
pip3 install pyyaml
```

### Installation unter Linux 

```sh
sudo apt update
sudo apt install git pandoc python3 python3-pip
pip install pyyaml
```

### Installation unter Windows

#### Installation von Git

Lade Git für Windows von der offiziellen Seite herunter und installiere es:
[https://git-scm.com/downloads](https://git-scm.com/downloads)

Während der Installation kannst du die Standardoptionen übernehmen. Falls du die **Git Bash** nutzen möchtest, stelle sicher, dass sie als Standard-Terminal ausgewählt ist.

#### Installation von Python 3

Lade die neueste Version von Python von der offiziellen Seite herunter:
[https://www.python.org/downloads/windows/](https://www.python.org/downloads/windows/)

Achte darauf, dass du während der Installation die Option **"Add Python to PATH"** aktivierst, damit Python über die Kommandozeile aufgerufen werden kann.

#### Installation der Abhängigkeiten

Nach der Installation von Python öffne die **Eingabeaufforderung (CMD)** oder die **Git Bash** und installiere die benötigten Python-Module mit folgendem Befehl:

```sh
pip install pyyaml
```

## Workflow für Editoren

1. Repository klonen

   ```sh
   git clone https://github.com/tjenni/phylab
   cd phylab
   ```

2. **Branch anlegen**

   ```sh
   git checkout -b feature-sektion
   ```

3. Änderungen machen

   ```sh
   python3 build.py
   ```

4. Änderungen committen

   ```sh
   git add .
   git commit -m "Neue Inhalte hinzugefügt"
   ```

5. **Änderungen auf GitHub hochladen**

   ```sh
   git push origin feature-sektion
   ```

## Lizenz

Dieses Projekt steht unter der **CC BY-NC-SA 4.0-Lizenz**. Siehe `LICENSE`-Datei
für weitere Details.
