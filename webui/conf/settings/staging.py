from .unstable import Settings as UnstableSettings


class Settings(UnstableSettings):
    """ staging settings
    """
    def run(self, settings):
        super(Settings, self).run(settings)

        settings.TRIPLE_DATABASE['HOST'] = 'controller.s.dandelion.eu'  # fix ?

        ALLOWED_HOSTS = ['controller.s.venturi.fbk.eu']

        RAVEN_CONFIG = {
            'dsn': 'http://729d3f1a92144b9f9b99fe1f309de089:'
                   '1ef5f2663f504280a652b0c68858c66a@sentry.venturi.fbk.eu/6'
        }

        settings.update(locals())
