import pygame


class Puller:
    """Represents a puller character anchor on either side of the rope."""

    BASE_LEAN = 8       # degrees everyone leans back just from bracing
    MAX_EXTRA_LEAN = 22 # extra degrees when this side has pulling momentum

    def __init__(self, x, y, color, label, lean_dir=1):
        """lean_dir: +1 leans back to the left (player side), -1 leans back to the right."""
        self.x = x
        self.y = y
        self.color = color
        self.label = label
        self.lean_dir = lean_dir
        self.lean_angle = 0.0
        self.font = pygame.font.SysFont(None, 24)

    def render(self, surface, momentum=0.0):
        """Draw avatar and label. momentum is -1..1 from THIS puller's point of view
        (positive = this side is winning), and controls how far they lean back."""
        target = self.lean_dir * (self.BASE_LEAN + self.MAX_EXTRA_LEAN * max(momentum, 0.0))
        self.lean_angle += (target - self.lean_angle) * 0.15   # smooth animation

        # Draw the upright figure on a transparent canvas whose centre is the
        # puller's feet, so rotating the canvas tilts them around their feet.
        size = 200
        canvas = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2
        pygame.draw.rect(canvas, self.color, pygame.Rect(cx - 20, cy - 70, 40, 70), border_radius=6)
        pygame.draw.circle(canvas, (240, 210, 180), (cx, cy - 85), 16)

        rotated = pygame.transform.rotate(canvas, self.lean_angle)
        feet = (self.x, self.y + 35)
        surface.blit(rotated, rotated.get_rect(center=feet))

        # Name / control tag
        label_surf = self.font.render(self.label, True, (240, 240, 240))
        surface.blit(label_surf, (self.x - label_surf.get_width() // 2, self.y + 45))