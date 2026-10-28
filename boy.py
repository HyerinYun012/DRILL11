import math
import time

from pico2d import (
    load_image,
    SDL_KEYDOWN, SDL_KEYUP,
    SDLK_SPACE, SDLK_LEFT, SDLK_RIGHT,
)
from transitions import Machine


class Boy:
    CANVAS_WIDTH = 800
    CHARACTER_HALF_WIDTH = 50
    RUN_SPEED = 5

    BREATH_CYCLE_SECONDS = 2.5
    BREATH_SCALE = 0.04
    BREATH_BOB = 1.5

    states = [
        {'name': 'IDLE', 'on_enter': 'enter_idle'},
        {'name': 'RUN', 'on_enter': 'enter_run'},
        {'name': 'SLEEP', 'on_enter': 'enter_sleep'},
    ]

    transitions = [
        {'trigger': 'fall_asleep', 'source': 'IDLE', 'dest': 'SLEEP'},
        {'trigger': 'wake_up', 'source': 'SLEEP', 'dest': 'IDLE'},
        {'trigger': 'start_run', 'source': ['IDLE', 'SLEEP'], 'dest': 'RUN'},
        {'trigger': 'stop_run', 'source': 'RUN', 'dest': 'IDLE'},
    ]

    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.face_dir = 1
        self.left_pressed = False
        self.right_pressed = False
        self.idle_started_at = time.monotonic()
        self.sleep_started_at = 0.0
        self.image = load_image('animation_sheet.png')

        self.state_machine = Machine(
            model=self,
            states=Boy.states,
            transitions=Boy.transitions,
            initial='IDLE',
            auto_transitions=False
        )

    def update(self):
        if self.is_IDLE():
            self.update_idle()
        elif self.is_RUN():
            self.update_run()

    def update_idle(self):
        if time.monotonic() - self.idle_started_at >= 5.0:
            self.fall_asleep()
            return

        self.frame = (self.frame + 1) % 8

    def update_run(self):
        self.frame = (self.frame + 1) % 8
        self.x += self.RUN_SPEED * self.face_dir
        self.x = max(
            self.CHARACTER_HALF_WIDTH,
            min(self.CANVAS_WIDTH - self.CHARACTER_HALF_WIDTH, self.x)
        )

    def handle_event(self, event):
        if event.type == SDL_KEYDOWN:
            if event.key == SDLK_SPACE and self.is_SLEEP():
                self.wake_up()
            elif event.key == SDLK_LEFT:
                self.left_pressed = True
                self.face_dir = -1
                if self.is_IDLE() or self.is_SLEEP():
                    self.start_run()
            elif event.key == SDLK_RIGHT:
                self.right_pressed = True
                self.face_dir = 1
                if self.is_IDLE() or self.is_SLEEP():
                    self.start_run()

        elif event.type == SDL_KEYUP:
            if event.key == SDLK_LEFT:
                self.left_pressed = False
            elif event.key == SDLK_RIGHT:
                self.right_pressed = False

            if self.is_RUN():
                if not self.left_pressed and not self.right_pressed:
                    self.stop_run()
                elif self.left_pressed:
                    self.face_dir = -1
                else:
                    self.face_dir = 1

    def enter_idle(self):
        self.frame = 0
        self.idle_started_at = time.monotonic()

    def enter_run(self):
        self.frame = 0

    def enter_sleep(self):
        self.frame = 0
        self.left_pressed = False
        self.right_pressed = False
        self.sleep_started_at = time.monotonic()

    def draw(self):
        if self.is_IDLE():
            self.draw_idle()
        elif self.is_RUN():
            self.draw_run()
        elif self.is_SLEEP():
            self.draw_sleep()

    def draw_idle(self):
        if self.face_dir == 1:
            self.image.clip_draw(self.frame * 100, 300, 100, 100, self.x, self.y)
        else:
            self.image.clip_draw(self.frame * 100, 200, 100, 100, self.x, self.y)

    def draw_run(self):
        row_y = 100 if self.face_dir == 1 else 0
        self.image.clip_draw(
            self.frame * 100, row_y, 100, 100,
            self.x, self.y
        )

    def draw_sleep(self):
        row_y = 300 if self.face_dir == 1 else 200
        angle = math.pi / 2 if self.face_dir == 1 else -math.pi / 2

        sleep_time = time.monotonic() - self.sleep_started_at
        breath_phase = sleep_time * 2.0 * math.pi / self.BREATH_CYCLE_SECONDS
        breath = math.sin(breath_phase)
        breath_width = 100 * (1.0 + self.BREATH_SCALE * breath)
        breath_y = self.y - 25 + self.BREATH_BOB * breath

        self.image.clip_composite_draw(
            0, row_y, 100, 100,
            angle, '', self.x, breath_y,
            breath_width, 100
        )
