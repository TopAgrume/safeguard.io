from utils import AccessEnv

from api import app
from schedule_appeal import run_schedule
import multiprocessing

if __name__ == "__main__":
    AccessEnv.on_reset()

    # Création des processus
    api_process = multiprocessing.Process(target=lambda: exec(open("api.py").read()))
    schedule_process = multiprocessing.Process(target=lambda: exec(open("schedule_appeal.py").read()))

    # Démarrage des deux processus
    api_process.start()
    schedule_process.start()

