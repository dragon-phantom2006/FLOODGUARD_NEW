LEVELS = {
    1: (
        "TIDE_ALERT",
        "Tide Alert",
        "The bottom switch is active. A tide alert has been detected; stay alert.",
    ),
    2: (
        "YELLOW_LEVEL",
        "Yellow Level",
        "The second switch is active. Monitor the water level and remain prepared.",
    ),
    3: (
        "ORANGE_LEVEL",
        "Orange Level",
        "The third switch is active. Flood conditions are worsening; prepare to move.",
    ),
    4: (
        "RED_LEVEL",
        "Red Level",
        "RED ALERT, Evacuate to a nearest safe location",
    ),
}

NORMAL = (
    "NORMAL",
    "Normal",
    "No flood switch is active. Conditions are currently normal.",
)


def level_for(sensor, water_level):
    """Legacy water-threshold evaluation for devices without switch telemetry."""
    if water_level >= sensor.level4_m:
        return 4
    if water_level >= sensor.level3_m:
        return 3
    if water_level >= sensor.level2_m:
        return 2
    if water_level >= sensor.level1_m:
        return 1
    return 0


def details(level):
    return LEVELS.get(level, NORMAL)
