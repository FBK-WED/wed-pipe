from contextlib import contextmanager


@contextmanager
def say(text):
    from fabric.colors import green

    print text + '...'
    yield
    print green('OK')
