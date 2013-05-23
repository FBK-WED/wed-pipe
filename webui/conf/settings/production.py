from .unstable import Settings as UnstableSettings


class Settings(UnstableSettings):
    """ production settings
    """
    def run(self, settings):
        super(Settings, self).run(settings)

        settings.TRIPLE_DATABASE['HOST'] = 'controller.dandelion.eu'  # fix ?

        ALLOWED_HOSTS = ['controller.venturi.fbk.eu']

        settings.update(locals())
