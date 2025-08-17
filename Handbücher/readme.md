# Master GUI mit PySide6

Eine flexible, modulare und intuitive GUI für Windows zur Verwaltung und Automatisierung von Skripten, Dateien und Links. Erstellt mit PySide6 und Python.

---

## Projektübersicht

Die Master GUI bietet:

* Flexible Verwaltung von Buttons (Anlegen, Bearbeiten, Verschieben)
* Ausführung von Python-Skripten mit Fortschrittsanzeige
* Direkte Links zu Dateien, Ordnern oder Webseiten
* Zentrale Verwaltung laufender Aufgaben im Task-Dashboard
* Anpassbares Theming und Hintergrundbilder
* Einfache Paketierung als Windows-EXE

---

## Technische Voraussetzungen

* **Python 3.11+**
* **PySide6**

---

## Installation

**1. Projekt klonen:**

```bash
git clone <repo-url>
cd master_gui2
```

**2. Virtuelle Umgebung erstellen (empfohlen):**

```bash
python -m venv venv
source venv/bin/activate # Linux/Mac
venv\Scripts\activate    # Windows
```

**3. Abhängigkeiten installieren:**

```bash
pip install -r requirements.txt
```

---

## Anwendung starten

Starte die Anwendung direkt:

```bash
python main.py
```

---

## Funktionen im Überblick

### Button-Verwaltung

* Buttons erstellen, löschen und bearbeiten
* Positionierung per Drag & Drop
* Speicherung aller Einstellungen in `config.json`

### Aktionen

* **SCRIPT:** Python-Skripte ausführen
* **LINK:** Webseiten oder Dateien öffnen
* **FILE:** Dateien im Standardprogramm öffnen
* **FOLDER:** Ordner im Explorer öffnen
* **MENU:** Buttons gruppieren und hierarchisch navigieren

### Task-Dashboard

* Übersicht aller laufenden und abgeschlossenen Jobs
* Fortschrittsbalken und Log-Anzeige
* Skript-Abbruch direkt aus der GUI möglich

### Theming

* Unterstützung für Stylesheets (QSS)
* Dynamische Hintergründe

---

## Paketierung als EXE

**Erstelle eine ausführbare Windows-Datei mit PyInstaller:**

```bash
pip install pyinstaller
pyinstaller --noconsole main.py
```

Die ausführbare Datei liegt danach unter `dist/main/main.exe`.

---

## Tests

Ausführen von Smoke-Tests mit pytest:

```bash
pytest tests/
```

---

## Verzeichnisstruktur

```
master_gui2/
├── assets/                # Icons und Hintergründe
├── core/                  # Kernlogik
├── gui_tools/             # Zusatztools
├── logs/                  # Logdateien
├── tests/                 # Testskripte
├── ui/                    # Benutzeroberfläche
├── util/                  # Hilfsfunktionen
├── config.json            # Konfigurationsdatei
├── main.py                # Anwendung starten
└── requirements.txt       # Abhängigkeiten
```

---

## Für Entwickler: Skripte für die GUI anpassen

Damit Python-Skripte optimal mit der Master-GUI interagieren, beachte bitte folgende Hinweise:

### Fortschrittsanzeige

Die GUI erkennt automatisch Fortschritte, wenn dein Skript Zeilen mit einer Prozentangabe am Ende ausgibt:

```python
print("Starte Verarbeitung [0%]")
# Zwischenschritte
print("Verarbeite Datei X [42%]")
# oder
print("Verarbeitung abgeschlossen: 100%")
```

### Fehlerbehandlung und Exit-Codes

* Erfolgreicher Abschluss: `exit(0)` oder normales Ende.
* Fehler: Nutze `exit(1)` oder werfe eine Exception; die GUI zeigt dann automatisch einen Fehler an.

### Logging

Alle Ausgaben (`stdout` und `stderr`) werden automatisch nach `logs/<job_id>.log` geschrieben. Nutze also `print(...)` für relevante Meldungen.

### Skript-Abbruch

Aktuell gibt es noch keine automatische Abbruchumgebung. Prüfe idealerweise regelmäßig auf ein externes Signal (geplant):

```python
import os

if os.environ.get("ABORT_REQUESTED") == "1":
    print("Abbruch erkannt – beende …")
    exit(1)
```

### Unit Tests erstellen

Lege idealerweise für jedes Skript Unit Tests an:

```python
# test_mein_script.py
def test_meine_logik():
    result = meine_funktion("testdaten.csv")
    assert result == erwartete_ausgabe
```

---

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz veröffentlicht – weitere Details findest du in der Datei `LICENSE`.

---

## Hilfe und Support

Bei Fragen, Problemen oder Vorschlägen bitte ein GitHub-Issue erstellen oder direkt den Entwickler kontaktieren.

---

Viel Spaß und Erfolg bei der Nutzung deiner Master GUI! 🚀
