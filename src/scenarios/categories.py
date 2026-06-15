"""Definiții scenarii de test — 4 categorii pentru capitolul experimental."""

from typing import Dict, List, Set

SCENARIOS: Dict[str, dict] = {
    "persoane": {
        "title": "Detectarea persoanelor",
        "section": "5.7.1",
        "description": "Pietoni și persoane în mediul urban / interior",
        "classes": ["person"],
        "folder": "persoane",
    },
    "vehicule": {
        "title": "Detectarea vehiculelor",
        "section": "5.7.2",
        "description": "Autoturisme, autobuze, camioane, motociclete, biciclete",
        "classes": ["bicycle", "car", "motorcycle", "bus", "truck"],
        "folder": "vehicule",
    },
    "animale": {
        "title": "Detectarea animalelor",
        "section": "5.7.3",
        "description": "Câini și pisici ca obstacole mobile",
        "classes": ["dog", "cat"],
        "folder": "animale",
    },
    "semne": {
        "title": "Detectarea semnelor de circulație",
        "section": "5.7.4",
        "description": "Semne STOP și semafoare",
        "classes": ["stop sign", "traffic light"],
        "folder": "semne",
    },
}

# Alias-uri pentru nume clasă (YOLO/COCO poate folosi underscore)
CLASS_ALIASES = {
    "stop_sign": "stop sign",
    "traffic_light": "traffic light",
}


def normalize_class_name(name: str) -> str:
    n = name.lower().strip()
    return CLASS_ALIASES.get(n, n)


def get_scenario_classes(scenario_key: str) -> Set[str]:
    if scenario_key not in SCENARIOS:
        raise KeyError(f"Scenariu necunoscut: {scenario_key}")
    return {normalize_class_name(c) for c in SCENARIOS[scenario_key]["classes"]}


def filter_detections_for_scenario(detections, scenario_key: str):
    """Păstrează doar detecțiile relevante scenariului."""
    allowed = get_scenario_classes(scenario_key)
    return [d for d in detections if normalize_class_name(d.class_name) in allowed]


def filter_obstacles_for_scenario(obstacles, scenario_key: str):
    allowed = get_scenario_classes(scenario_key)
    return [
        o for o in obstacles
        if normalize_class_name(o.detection.class_name) in allowed
    ]
