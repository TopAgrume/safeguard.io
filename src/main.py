import multiprocessing

from src.react_chatbot import run_api
from schedule_appeal import run_schedule_process
from queue_process import run_queue_process

if __name__ == "__main__":
    # Création des processus
    api_process_obj = multiprocessing.Process(target=run_api)
    schedule_process_obj = multiprocessing.Process(target=run_schedule_process)
    queue_process_obj = multiprocessing.Process(target=run_queue_process)

    # Démarrage des deux processus
    api_process_obj.start()
    schedule_process_obj.start()
    queue_process_obj.start()

