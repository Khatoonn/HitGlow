"""Suivi de progression dans un combo (pure logique, pas d'IO/pygame).

Suit l'ordre des etapes uniquement (pas de fenetre de timing — voir la
spec) : une etape "trackable" avance des que ses inputs requis passent de
non-satisfaits a satisfaits (front montant, pour eviter qu'un input tenu
plusieurs frames ne fasse sauter plusieurs etapes d'un coup). Une etape non
trackable (nom de stance, condition...) doit etre validee manuellement par
l'utilisateur (il sait qu'il vient de la faire) via advance_manual()."""


class ComboTracker:
    def __init__(self, steps):
        self.steps = steps
        self.index = 0
        self._was_satisfied = False

    def current_step(self):
        return self.steps[self.index] if self.index < len(self.steps) else None

    def is_complete(self):
        return self.index >= len(self.steps)

    def update(self, pressed_names):
        """pressed_names : ensemble des noms d'input HitGlow actuellement
        enfonces (ex: {"RIGHT", "2"}). Retourne True si l'etape courante
        vient d'etre validee par cet appel."""
        step = self.current_step()
        if step is None or not step["trackable"]:
            self._was_satisfied = False
            return False

        satisfied = step["inputs"] <= pressed_names
        advanced = satisfied and not self._was_satisfied
        if advanced:
            self.index += 1
            next_step = self.current_step()
            if next_step is not None and next_step["trackable"]:
                # Le meme appui (ex: bouton tenu) peut deja satisfaire
                # l'etape suivante : ne pas la valider immediatement, il
                # faudra un relachement puis un nouvel appui.
                self._was_satisfied = next_step["inputs"] <= pressed_names
            else:
                self._was_satisfied = False
        else:
            self._was_satisfied = satisfied
        return advanced

    def advance_manual(self):
        """Valide manuellement l'etape courante (utilise pour les etapes
        non trackable, que le joueur execute lui-meme)."""
        if self.index < len(self.steps):
            self.index += 1
        self._was_satisfied = False

    def reset(self):
        self.index = 0
        self._was_satisfied = False
