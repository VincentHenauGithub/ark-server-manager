import threading
import time

class Manager:
    def __init__(self, process, name: str = ""):
        self.thread = None
        self.stop_event = None
        self.name = name
        self.process = process

    def _print(self, message):
        current_time = time.strftime("%H:%M:%S", time.localtime())
        print(f"[{current_time}][{self.name}] {message}")

    def start(self, interval: int):
        self._print(f"Starting {self.name}")
        def run():
            while not self.stop_event.is_set():
                try:
                    self.process(interval)
                    for _ in range(interval):
                        if self.stop_event.is_set():
                            break
                        time.sleep(1)
                except Exception as e:
                    self._print(f"Error, stopping thread: {e}")
                    self.stop_event.set()

        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=run)
        self.thread.start()

    def stop(self):
        if self.thread is not None:
            self.stop_event.set()
            self.thread.join()
            self.thread = None

    def is_alive(self):
        return self.thread is not None and self.thread.is_alive()