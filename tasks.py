from infra.logging_config import setup_logging
from robocorp.tasks import task
setup_logging()

from app.run import RunClass
from infra.driver import driver
import config

@task
def run_task():
    driver_class = driver()
    driver1 = driver_class.set_webdriver()
    ny_search = RunClass(driver1, config.query, config.subject)
    ny_search.run_search()
