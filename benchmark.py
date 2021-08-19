import psutil
import random
from threading import Thread

class Benchmark(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.cpu = []
        self.memory = []

    def run(self):

        self.running = True

   #     currentProcess = psutil.Process()

        while self.running:
            self.cpu.append(psutil.cpu_percent(interval=1))
            self.memory.append(psutil.virtual_memory()[2])

    def stop(self):
        self.running = False
        return self.cpu, self.memory
