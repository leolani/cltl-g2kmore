import logging.config
import time

from cltl.template.dummy_demo import DummyDemoProcessor

logging.config.fileConfig('config/logging.config')

import json
from types import SimpleNamespace

from cltl.combot.infra.config.k8config import K8LocalConfigurationContainer
from cltl.combot.infra.di_container import singleton
from cltl.combot.infra.event.kombu import KombuEventBus
from cltl.combot.infra.event.memory import SynchronousEventBus
from cltl.combot.infra.resource.threaded import ThreadedResourceContainer
from cltl_service.template.service import TemplateService
from kombu.serialization import register

logger = logging.getLogger(__name__)

K8LocalConfigurationContainer.load_configuration()

class ApplicationContainer(ThreadedResourceContainer, K8LocalConfigurationContainer):
    logger.info("Initialized ApplicationContainer")

    @property
    @singleton
    def event_bus(self):
        config = self.config_manager.get_config("cltl.template.events")
        if config.get_boolean("local"):
            return SynchronousEventBus()
        else:
            register('cltl-json',
                     lambda x: json.dumps(x, default=vars),
                     lambda x: json.loads(x, object_hook=lambda d: SimpleNamespace(**d)),
                     content_type='application/json',
                     content_encoding='utf-8')
            return KombuEventBus('cltl-json', self.config_manager)

    @property
    @singleton
    def processor(self):
        config = self.config_manager.get_config("cltl.template")

        return DummyDemoProcessor(config.get("phrase"))

    @property
    @singleton
    def service(self):
        return TemplateService.from_config(self.processor, self.event_bus, self.resource_manager, self.config_manager)


class Application(ApplicationContainer):
    def run(self):
        self.service.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.service.stop()


if __name__ == '__main__':
    Application().run()
