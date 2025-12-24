import time

def actuate_dl(status):
    t = time.localtime()
    state = "ON" if status else "OFF"
    print(f"\nTimestamp: {time.strftime('%H:%M:%S', t)} | DL (Door Light): {state}\n")