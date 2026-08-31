"""Mode calibration : formatte l'etat brut de la manette en texte lisible
pour identifier quel input physique correspond a quel index."""


def format_calibration_lines(hat_value, axis_values, pressed_button_indices):
    lines = [f"HAT: {tuple(hat_value)}"]
    for i, value in enumerate(axis_values):
        lines.append(f"AXIS {i}: {value:+.2f}")
    if pressed_button_indices:
        lines.append(f"BOUTONS: {sorted(pressed_button_indices)}")
    else:
        lines.append("BOUTONS: (aucun)")
    return lines
