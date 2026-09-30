import random
import pygame
from game.rope import Rope
from game.player import Puller


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.rope = Rope(width, height)
        self.player = Puller(90, height // 2, (50, 120, 220), "PLAYER (A/D)", lean_dir=1)
        self.computer = Puller(width - 90, height // 2, (220, 80, 50), "COMPUTER", lean_dir=-1)

        self.last_key = None
        self.winner = None
        self.game_state = "PLAYING"

        # Computer pacing. Normal values are used until the flag is dragged
        # close to the player's goal, then "panic surge" kicks in.
        self.computer_pull_cooldown = 180
        self.surge_cooldown = 140          # ms between pulls while surging
        self.surge_strength = 1.25         # pull strength multiplier while surging
        self.surge_trigger = 0.5           # surge when flag is past this fraction of the way to the player's goal
        self.computer_surging = False
        self.last_computer_pull = pygame.time.get_ticks()

        # Match timer / sudden death
        self.sudden_death_ms = 45000       # match length before sudden death begins
        self.sudden_death_multiplier = 2   # pull distance multiplier in sudden death
        self.match_start = pygame.time.get_ticks()
        self.elapsed_ms = 0
        self.sudden_death = False

        self.font_big = pygame.font.SysFont(None, 48)
        self.font_small = pygame.font.SysFont(None, 26)

    def handle_event(self, event):
        if self.game_state != "PLAYING":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset()
            return

        # A pull only counts when the key differs from the previous pull, so
        # the player must alternate A and D. No lock flag is needed: KEYDOWN
        # events are discrete, and overlapping key presses (pressing D before
        # A is fully released) can no longer freeze the input.
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_a, pygame.K_d):
            if event.key != self.last_key:
                self.rope.pull_left(1.0 * self.pull_multiplier())
                self.last_key = event.key

    def pull_multiplier(self):
        return self.sudden_death_multiplier if self.sudden_death else 1

    def update(self):
        if self.game_state != "PLAYING":
            return

        now = pygame.time.get_ticks()

        # Match timer: enter sudden death once the time limit passes.
        self.elapsed_ms = now - self.match_start
        if not self.sudden_death and self.elapsed_ms >= self.sudden_death_ms:
            self.sudden_death = True

        # Panic surge: the closer the flag gets to the player's goal line
        # (rope.left_win_x), the harder the computer fights back.
        center_x = self.width // 2
        surge_line = center_x - (center_x - self.rope.left_win_x) * self.surge_trigger
        self.computer_surging = self.rope.marker_x <= surge_line

        cooldown = self.surge_cooldown if self.computer_surging else self.computer_pull_cooldown
        strength = self.surge_strength if self.computer_surging else 1.0
        strength *= self.pull_multiplier()

        if now - self.last_computer_pull >= cooldown:
            computer_variance = random.uniform(0.7, 1.2)
            self.rope.pull_right(computer_variance * strength)
            self.last_computer_pull = now

        result = self.rope.check_winner()
        if result:
            self.winner = result
            self.game_state = "GAME_OVER"

    def reset(self):
        self.rope.reset()
        self.last_key = None
        self.winner = None
        self.game_state = "PLAYING"
        self.computer_surging = False
        self.last_computer_pull = pygame.time.get_ticks()
        self.match_start = pygame.time.get_ticks()
        self.elapsed_ms = 0
        self.sudden_death = False

    def render(self, screen):
        screen.fill((30, 32, 36))

        mud_rect = pygame.Rect(self.width // 2 - 120, self.height // 2 - 80, 240, 160)
        pygame.draw.rect(screen, (45, 38, 30), mud_rect, border_radius=12)

        self.rope.render(screen)
        momentum = self.rope.momentum()          # + = player winning
        self.player.render(screen, momentum)
        self.computer.render(screen, -momentum)

        if self.computer_surging and self.game_state == "PLAYING":
            surge_surf = self.font_small.render("COMPUTER PANIC SURGE!", True, (255, 140, 60))
            screen.blit(surge_surf, (self.width // 2 - surge_surf.get_width() // 2, self.height - 60))

        # Match timer (top of screen). Freezes on Game Over; turns red in sudden death.
        total_seconds = self.elapsed_ms // 1000
        timer_color = (255, 80, 80) if self.sudden_death else (240, 240, 240)
        timer_surf = self.font_big.render(
            f"{total_seconds // 60}:{total_seconds % 60:02d}", True, timer_color
        )
        screen.blit(timer_surf, (self.width // 2 - timer_surf.get_width() // 2, 8))

        if self.sudden_death and self.game_state == "PLAYING":
            # Flash the banner about twice per second.
            if (pygame.time.get_ticks() // 250) % 2 == 0:
                sd_surf = self.font_small.render("SUDDEN DEATH - PULLS DOUBLED!", True, (255, 80, 80))
                screen.blit(sd_surf, (self.width // 2 - sd_surf.get_width() // 2, 80))

        inst_surf = self.font_small.render(
            "Alternate [A] and [D] keys rapidly to pull!", True, (210, 210, 210)
        )
        screen.blit(inst_surf, (self.width // 2 - inst_surf.get_width() // 2, 52))

        if self.game_state == "GAME_OVER":
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            win_text = f"{self.winner} WINS!"
            color = (80, 220, 80) if self.winner == "PLAYER" else (240, 80, 80)
            text_surf = self.font_big.render(win_text, True, color)
            screen.blit(
                text_surf,
                (self.width // 2 - text_surf.get_width() // 2, self.height // 2 - 50)
            )

            restart_surf = self.font_small.render(
                "Press [R] to Play Again", True, (240, 240, 240)
            )
            screen.blit(
                restart_surf,
                (self.width // 2 - restart_surf.get_width() // 2, self.height // 2 + 10)
            )