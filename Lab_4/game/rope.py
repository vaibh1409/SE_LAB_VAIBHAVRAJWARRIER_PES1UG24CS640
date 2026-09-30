import math
import pygame


class Rope:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.center_y = screen_height // 2
        self.marker_x = screen_width // 2

        self.left_win_x = 180
        self.right_win_x = screen_width - 180
        self.pull_step = 12

    def pull_left(self, strength=1.0):
        self.marker_x -= int(self.pull_step * strength)

    def pull_right(self, strength=1.0):
        self.marker_x += int(self.pull_step * strength)

    def check_winner(self):
        if self.marker_x <= self.left_win_x:
            return "PLAYER"
        if self.marker_x >= self.right_win_x:
            return "COMPUTER"
        return None

    def reset(self):
        self.marker_x = float(self.screen_width // 2)
        self.velocity = 0.0

    def momentum(self):
        """Who is winning, from -1.0 (computer at its goal) to +1.0 (player at its goal)."""
        half = self.screen_width // 2 - self.left_win_x
        return max(-1.0, min(1.0, (self.screen_width // 2 - self.marker_x) / half))

    def tension(self):
        """0.0 when the flag is centered (rope slack) up to 1.0 near either goal (rope taut)."""
        return abs(self.momentum())

    def _rope_points(self, t_ms, segments=60):
        """Build the rope polyline: sags when slack, vibrates when taut."""
        x0, x1 = 60, self.screen_width - 60
        tension = self.tension()
        sag = 14 * (1.0 - tension) ** 2            # droop fades as the rope tightens
        vibe = 5 * tension                          # vibration grows with tension
        phase = t_ms * 0.03
        points = []
        for i in range(segments + 1):
            u = i / segments                        # 0..1 along the rope
            x = x0 + (x1 - x0) * u
            droop = sag * math.sin(math.pi * u)     # biggest sag in the middle
            wobble = vibe * math.sin(u * 40 + phase) * math.sin(math.pi * u)
            points.append((x, self.center_y + droop + wobble))
        return points

    def render(self, surface):
        tension = self.tension()
        # Rope gets paler / more strained-looking as tension rises.
        rope_color = (
            int(180 + 60 * tension),
            int(140 + 60 * tension),
            int(90 + 40 * tension),
        )
        pygame.draw.lines(
            surface, rope_color, False, self._rope_points(pygame.time.get_ticks()), 10
        )

        pygame.draw.line(
            surface,
            (50, 200, 50),
            (self.left_win_x, self.center_y - 40),
            (self.left_win_x, self.center_y + 40),
            4
        )
        pygame.draw.line(
            surface,
            (200, 50, 50),
            (self.right_win_x, self.center_y - 40),
            (self.right_win_x, self.center_y + 40),
            4
        )

        pygame.draw.line(
            surface,
            (120, 120, 120),
            (self.screen_width // 2, self.center_y - 20),
            (self.screen_width // 2, self.center_y + 20),
            2
        )

        # Flag rides on the rope, so follow the sag at its x position.
        pts = self._rope_points(pygame.time.get_ticks())
        flag_y = min(pts, key=lambda p: abs(p[0] - self.marker_x))[1]
        flag_rect = pygame.Rect(int(self.marker_x) - 12, int(flag_y) - 24, 24, 48)
        pygame.draw.rect(surface, (230, 40, 40), flag_rect, border_radius=4)
        pygame.draw.rect(surface, (255, 255, 255), flag_rect, width=2, border_radius=4)