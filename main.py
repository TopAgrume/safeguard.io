from utils import AccessEnv

import multiprocessing

from api import run_api
from schedule_appeal import run_schedule_process

if __name__ == "__main__":
    AccessEnv.on_reset()

    # Création des processus
    api_process_obj = multiprocessing.Process(target=run_api)
    schedule_process_obj = multiprocessing.Process(target=run_schedule_process)

    # Démarrage des deux processus
    api_process_obj.start()
    schedule_process_obj.start()

