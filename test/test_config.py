from symphony.engine import SymphonyConfig
import pytest

class TestConfig:
    def test_creation(self):
        SymphonyConfig.reset()
        config = SymphonyConfig()
        config.update({'username': 'abc', 'experiment_folder': '~/kurreal'})
        assert config.username == 'abc'
        assert config.experiment_folder == '~/kurreal'

    def test_singleton(self):
        SymphonyConfig.reset()
        config = SymphonyConfig()
        config.update({'username': 'abc', 'experiment_folder': '~/kurreal'})
        SymphonyConfig().set_username('def')
        assert config.username == 'def'

    def test_no_double_register(self):
        SymphonyConfig.reset()
        with pytest.raises(ValueError):
            SymphonyConfig().register_handler('username', str)

    def test_register(self):
        class TmuxConfig:
            def __init__(self, di):
                self.max_windows = None
                if 'max_windows' in di:
                    self.max_windows = di['max_windows']

            def set_max_windows(self, x):
                self.max_windows = x

        SymphonyConfig().register_handler('tmux', TmuxConfig)
        SymphonyConfig().update({'tmux': {'max_windows': 5}})

        assert SymphonyConfig().tmux.max_windows == 5