import math
import time

from pico2d import (
    load_image,
    SDL_KEYDOWN, SDL_KEYUP,
    SDLK_SPACE, SDLK_LEFT, SDLK_RIGHT, SDLK_a,
)
from transitions import Machine


class AutoRun:
    """Behavior owned by the automatic running state."""

    def __init__(self, boy):
        self.boy = boy
        self.started_at = 0.0

    def enter(self):
        self.started_at = time.monotonic()
        self.boy.frame = 0

    def update(self):
        self.boy.frame = (self.boy.frame + 1) % 8
        self.boy.x += self.boy.AUTO_RUN_SPEED * self.boy.face_dir

        left_boundary = self.boy.AUTO_RUN_HALF_WIDTH
        right_boundary = self.boy.CANVAS_WIDTH - self.boy.AUTO_RUN_HALF_WIDTH

        if self.boy.x <= left_boundary:
            self.boy.x = left_boundary
            self.boy.face_dir = 1
        elif self.boy.x >= right_boundary:
            self.boy.x = right_boundary
            self.boy.face_dir = -1

    def draw(self):
        row_y = self.boy.SPRITE_SIZE if self.boy.face_dir == 1 else 0
        self.boy.image.clip_draw(
            self.boy.frame * self.boy.SPRITE_SIZE,
            row_y,
            self.boy.SPRITE_SIZE,
            self.boy.SPRITE_SIZE,
            self.boy.x,
            self.boy.y,
            self.boy.AUTO_RUN_SIZE,
            self.boy.AUTO_RUN_SIZE
        )


class Boy:
    CANVAS_WIDTH = 800
    SPRITE_SIZE = 100
    CHARACTER_HALF_WIDTH = SPRITE_SIZE // 2
    RUN_SPEED = 5
    AUTO_RUN_SPEED = RUN_SPEED * 2
    AUTO_RUN_SCALE = 1.5
    AUTO_RUN_SIZE = int(SPRITE_SIZE * AUTO_RUN_SCALE)
    AUTO_RUN_HALF_WIDTH = AUTO_RUN_SIZE // 2

    BREATH_CYCLE_SECONDS = 2.5
    BREATH_SCALE = 0.04
    BREATH_BOB = 1.5

    states = [
        {'name': 'IDLE', 'on_enter': 'enter_idle'},
        {'name': 'RUN', 'on_enter': 'enter_run'},
        {'name': 'SLEEP', 'on_enter': 'enter_sleep'},
        {'name': 'AUTO_RUN', 'on_enter': 'enter_auto_run'},
    ]

    transitions = [
        {'trigger': 'fall_asleep', 'source': 'IDLE', 'dest': 'SLEEP'},
        {'trigger': 'wake_up', 'source': 'SLEEP', 'dest': 'IDLE'},
        {'trigger': 'start_run', 'source': ['IDLE', 'SLEEP'], 'dest': 'RUN'},
        {'trigger': 'stop_run', 'source': 'RUN', 'dest': 'IDLE'},
        {'trigger': 'start_auto_run', 'source': 'IDLE', 'dest': 'AUTO_RUN'},
        {'trigger': 'auto_run_timeout', 'source': 'AUTO_RUN', 'dest': 'IDLE'},
        {'trigger': 'cancel_auto_run', 'source': 'AUTO_RUN', 'dest': 'RUN'},
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
        self.auto_run = AutoRun(self)

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
        elif self.is_AUTO_RUN():
            self.auto_run.update()

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
            if event.key == SDLK_a and self.is_IDLE():
                self.start_auto_run()
            elif event.key == SDLK_SPACE and self.is_SLEEP():
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

    def enter_auto_run(self):
        self.auto_run.enter()

    def draw(self):
        if self.is_IDLE():
            self.draw_idle()
        elif self.is_RUN():
            self.draw_run()
        elif self.is_AUTO_RUN():
            self.auto_run.draw()
        elif self.is_SLEEP():
            self.draw_sleep()

    def draw_idle(self):
        row_y = 3 * self.SPRITE_SIZE if self.face_dir == 1 else 2 * self.SPRITE_SIZE
        self.image.clip_draw(
            self.frame * self.SPRITE_SIZE,
            row_y,
            self.SPRITE_SIZE,
            self.SPRITE_SIZE,
            self.x,
            self.y
        )

    def draw_run(self):
        row_y = self.SPRITE_SIZE if self.face_dir == 1 else 0
        self.image.clip_draw(
            self.frame * self.SPRITE_SIZE,
            row_y,
            self.SPRITE_SIZE,
            self.SPRITE_SIZE,
            self.x, self.y
        )

    def draw_sleep(self):
        row_y = 3 * self.SPRITE_SIZE if self.face_dir == 1 else 2 * self.SPRITE_SIZE
        angle = math.pi / 2 if self.face_dir == 1 else -math.pi / 2

        sleep_time = time.monotonic() - self.sleep_started_at
        breath_phase = sleep_time * 2.0 * math.pi / self.BREATH_CYCLE_SECONDS
        breath = math.sin(breath_phase)
        breath_width = self.SPRITE_SIZE * (1.0 + self.BREATH_SCALE * breath)
        breath_y = self.y - 25 + self.BREATH_BOB * breath

        self.image.clip_composite_draw(
            0, row_y, self.SPRITE_SIZE, self.SPRITE_SIZE,
            angle, '', self.x, breath_y,
            breath_width, self.SPRITE_SIZE
        )
