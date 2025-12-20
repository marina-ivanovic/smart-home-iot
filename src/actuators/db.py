import time

def actuate_db(status):
    t = time.localtime()
    state = "BEEP!" if status else "silence"
    print(f"\nTimestamp: {time.strftime('%H:%M:%S', t)} | DB (Door Buzzer): {state}\n")