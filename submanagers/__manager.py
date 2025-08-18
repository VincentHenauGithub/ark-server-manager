import os
import shutil
import time
from .errorcatch import ErrorCatch

OLD_LOG_DIR = f"logs\\_old"
LOG_FILE_NAME = f"logs\\{time.strftime('%Y-%m-%d_%H-%M-%S')}.log"

class Manager:
    def __init__(self, process, name: str = "", interval: int = 60):
        self.thread = None
        self.stop_event = None
        self.name = name
        self._process = process
        self.save_tracker = None
        self.start_time = time.time()
        self.next_run = 0
        self.interval = interval
        self._stash_old_logs()
        with open(LOG_FILE_NAME, "w") as f:
            f.write(f"Log started at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.start_time))}\n")

    def _stash_old_logs(self):
        LOG_FILE = LOG_FILE_NAME.split("\\")[-1]
        if not os.path.exists(OLD_LOG_DIR):
            os.makedirs(OLD_LOG_DIR)
        for file in os.listdir("logs"):
            if file.endswith(".log") and file != LOG_FILE:
                print(f"Moving old log file {file} to {OLD_LOG_DIR}")
                shutil.move(os.path.join("logs", file), OLD_LOG_DIR)

    def _log(self, message: str):
        with open(LOG_FILE_NAME, "a") as log_file:
            log_file.write(f"{message}\n")

    def __current_time(self):
        return int(time.time() - self.start_time)

    def _print(self, message, log=True):
        if isinstance(message, str):
            lines = message.split("\n")
        else:
            lines = [message]
        for line in lines:
            current_time = time.strftime("%H:%M:%S", time.localtime())
            message = f"[{current_time}][{self.name}] {line}"
            print(message)
            if log:
                self._log(message)

    def set_interval(self, interval: int):
        self.interval = interval
        self.next_run = self.__current_time() + interval

    def process(self):
        if self.__current_time() < self.next_run:
            return
        
        self._print(f"Processing {self.name}...", False)
        self.next_run = self.__current_time() + self.interval

        try:
            self._process(self.interval)
        except Exception as e:
            self._print(f"Error during process: {e}")
            if not ErrorCatch.CATCH_ERRORS:
                raise e

    # def start(self, interval: int):
    #     self._print(f"Starting {self.name}")
    #     def run():
    #         while not self.stop_event.is_set():
    #             try:
    #                 self.process(interval)
    #                 for _ in range(interval):
    #                     if self.stop_event.is_set():
    #                         break
    #                     time.sleep(1)
    #             except Exception as e:
    #                 self._print(f"Error, stopping thread: {e}")
    #                 self.stop_event.set()

    #     self.stop_event = threading.Event()
    #     self.thread = threading.Thread(target=run)
    #     self.thread.start()

    # def dispose(self):
    #     self.stop()
    #     self._print(f"Disposed {self.name}")

    # def stop(self):
    #     if self.thread is not None:
    #         self.stop_event.set()
    #         self.thread.join()
    #         self.thread = None

    # def is_alive(self):
    #     return self.thread is not None and self.thread.is_alive()