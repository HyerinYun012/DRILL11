import importlib
import sys
import types
import unittest
from unittest.mock import patch


class FakeImage:
    def __init__(self):
        self.clip_draw_calls = []
        self.clip_composite_draw_calls = []

    def clip_draw(self, *args):
        self.clip_draw_calls.append(args)

    def clip_composite_draw(self, *args):
        self.clip_composite_draw_calls.append(args)


class FakeMachine:
    """Small transitions.Machine substitute used by these unit tests."""

    def __init__(self, model, states, transitions, initial, auto_transitions):
        del auto_transitions
        model.state = initial

        state_callbacks = {
            state['name']: state.get('on_enter')
            for state in states
        }

        for state in states:
            state_name = state['name']
            setattr(
                model,
                f'is_{state_name}',
                lambda name=state_name: model.state == name
            )

        for transition in transitions:
            setattr(
                model,
                transition['trigger'],
                self._make_trigger(model, transition, state_callbacks)
            )

    @staticmethod
    def _make_trigger(model, transition, state_callbacks):
        def trigger():
            sources = transition['source']
            if isinstance(sources, str):
                sources = [sources]

            if model.state not in sources:
                raise RuntimeError(
                    f"Cannot trigger {transition['trigger']} from {model.state}"
                )

            destination = transition['dest']
            model.state = destination

            callback = state_callbacks.get(destination)
            if callback:
                getattr(model, callback)()

            return True

        return trigger


def install_dependency_stubs():
    pico2d = types.ModuleType('pico2d')
    pico2d.SDL_KEYDOWN = 1
    pico2d.SDL_KEYUP = 2
    pico2d.SDLK_SPACE = 'space'
    pico2d.SDLK_LEFT = 'left'
    pico2d.SDLK_RIGHT = 'right'
    pico2d.SDLK_a = 'a'
    pico2d.load_image = lambda _path: FakeImage()

    transitions = types.ModuleType('transitions')
    transitions.Machine = FakeMachine

    sys.modules['pico2d'] = pico2d
    sys.modules['transitions'] = transitions


install_dependency_stubs()
boy = importlib.import_module('boy')


def key_event(event_type, key):
    return types.SimpleNamespace(type=event_type, key=key)


class AutoRunTests(unittest.TestCase):
    def setUp(self):
        self.time_patch = patch.object(boy.time, 'monotonic', return_value=0.0)
        self.clock = self.time_patch.start()
        self.addCleanup(self.time_patch.stop)
        self.character = boy.Boy()

    def enter_auto_run(self, character=None):
        character = character or self.character
        character.handle_event(key_event(boy.SDL_KEYDOWN, boy.SDLK_a))
        self.assertTrue(character.is_AUTO_RUN())
        return character

    def test_a_key_enters_auto_run_from_idle(self):
        self.enter_auto_run()
        self.assertIsInstance(self.character.auto_run, boy.AutoRun)

    def test_a_key_enters_auto_run_while_direction_is_held(self):
        self.character.handle_event(
            key_event(boy.SDL_KEYDOWN, boy.SDLK_RIGHT)
        )
        self.assertTrue(self.character.is_RUN())
        self.assertTrue(self.character.right_pressed)

        self.character.handle_event(key_event(boy.SDL_KEYDOWN, boy.SDLK_a))

        self.assertTrue(self.character.is_AUTO_RUN())
        self.assertEqual(self.character.face_dir, 1)
        self.assertTrue(self.character.right_pressed)

        start_x = self.character.x
        self.clock.return_value = 1.0
        self.character.update()
        self.character.draw()

        self.assertEqual(
            self.character.x - start_x,
            self.character.RUN_SPEED * 3
        )
        self.assertEqual(
            self.character.image.clip_draw_calls[-1][-2:],
            (150, 150)
        )

        self.character.handle_event(
            key_event(boy.SDL_KEYDOWN, boy.SDLK_RIGHT)
        )
        self.assertTrue(self.character.is_AUTO_RUN())

        self.character.handle_event(
            key_event(boy.SDL_KEYUP, boy.SDLK_RIGHT)
        )
        self.assertTrue(self.character.is_AUTO_RUN())
        self.assertFalse(self.character.right_pressed)

    def test_auto_run_moves_at_three_times_the_normal_speed(self):
        self.enter_auto_run()
        start_x = self.character.x
        self.clock.return_value = 1.0

        self.character.update()

        self.assertEqual(
            self.character.x - start_x,
            self.character.RUN_SPEED * 3
        )

    def test_auto_run_draws_at_enlarged_size(self):
        self.enter_auto_run()

        self.character.draw()

        draw_args = self.character.image.clip_draw_calls[-1]
        self.assertEqual(draw_args[-2:], (150, 150))

    def test_auto_run_reverses_at_both_boundaries(self):
        cases = [
            (724, 1, 725, -1),
            (76, -1, 75, 1),
        ]

        for start_x, direction, expected_x, expected_direction in cases:
            with self.subTest(start_x=start_x, direction=direction):
                character = self.enter_auto_run(boy.Boy())
                character.x = start_x
                character.face_dir = direction
                self.clock.return_value = 1.0

                character.update()

                self.assertEqual(character.x, expected_x)
                self.assertEqual(character.face_dir, expected_direction)

    def test_auto_run_returns_to_idle_after_five_seconds(self):
        self.enter_auto_run()
        self.clock.return_value = 5.0

        self.character.update()

        self.assertTrue(self.character.is_IDLE())
        self.assertEqual(self.character.frame, 0)

    def test_left_key_cancels_auto_run_into_left_run(self):
        self.enter_auto_run()

        self.character.handle_event(
            key_event(boy.SDL_KEYDOWN, boy.SDLK_LEFT)
        )

        self.assertTrue(self.character.is_RUN())
        self.assertEqual(self.character.face_dir, -1)
        self.assertTrue(self.character.left_pressed)

        self.character.handle_event(
            key_event(boy.SDL_KEYUP, boy.SDLK_LEFT)
        )
        self.assertTrue(self.character.is_IDLE())

    def test_right_key_cancels_auto_run_into_right_run(self):
        self.enter_auto_run()

        self.character.handle_event(
            key_event(boy.SDL_KEYDOWN, boy.SDLK_RIGHT)
        )

        self.assertTrue(self.character.is_RUN())
        self.assertEqual(self.character.face_dir, 1)
        self.assertTrue(self.character.right_pressed)

    def test_a_key_is_ignored_while_sleeping(self):
        sleeping_character = boy.Boy()
        sleeping_character.fall_asleep()
        sleeping_character.handle_event(
            key_event(boy.SDL_KEYDOWN, boy.SDLK_a)
        )
        self.assertTrue(sleeping_character.is_SLEEP())


if __name__ == '__main__':
    unittest.main()
