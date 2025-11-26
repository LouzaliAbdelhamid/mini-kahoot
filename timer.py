from firebase import timer_ref
import time

def run_timer(seconds):
    for i in range(seconds, -1, -1):
        timer_ref.set({"time_left": i})
        time.sleep(1)
