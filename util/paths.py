from pathlib import Path

def project_root() -> Path:
    """
    Liefert den absoluten Pfad zum Projekt-Stammverzeichnis.
    """
    # __file__ ist util/paths.py → zwei Ebenen höher ist project_root
    return Path(__file__).resolve().parent.parent

def relative(*path_segments: str) -> Path:
    """
    Baut einen Pfad relativ zum Projekt-Stamm auf.
    Beispiel: relative("assets", "icons", "logo.png")
    """
    return project_root().joinpath(*path_segments)
