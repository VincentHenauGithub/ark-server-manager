import threading
import time

class Manager:
    def __init__(self, process, name: str = ""):
        self.thread = None
        self.stop_event = None
        self.name = name
        self.process = process

    def start(self, interval: int):
        print(f"Starting {self.name}")
        def run():
            while not self.stop_event.is_set():
                try:
                    self.process(interval)
                    for _ in range(interval):
                        if self.stop_event.is_set():
                            break
                        time.sleep(1)
                except Exception as e:
                    print(f"Error in player {self.name}, stopping thread: {e}")
                    self.stop_event.set()

        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=run)
        self.thread.start()

    def stop(self):
        if self.thread is not None:
            self.stop_event.set()
            self.thread.join()
            self.thread = None