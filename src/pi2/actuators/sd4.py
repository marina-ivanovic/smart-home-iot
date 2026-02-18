import time
import threading

def actuate_4sd(settings, display_value, single_pass=False):
    if settings['simulated']:
        if not single_pass:
            t = time.localtime()
            print(f"\nTimestamp: {time.strftime('%H:%M:%S', t)} | 4SD Display: {display_value}\n")
    else:
        import RPi.GPIO as GPIO
        segments = settings['segments']
        digits = settings['digits']
        
        # Map character to segments (a,b,c,d,e,f,g)
        num = {
            ' ': (0,0,0,0,0,0,0),
            '0': (1,1,1,1,1,1,0),
            '1': (0,1,1,0,0,0,0),
            '2': (1,1,0,1,1,0,1),
            '3': (1,1,1,1,0,0,1),
            '4': (0,1,1,0,0,1,1),
            '5': (1,0,1,1,0,1,1),
            '6': (1,0,1,1,1,1,1),
            '7': (1,1,1,0,0,0,0),
            '8': (1,1,1,1,1,1,1),
            '9': (1,1,1,1,0,1,1)
        }

        for s in segments: GPIO.setup(s, GPIO.OUT)
        for d in digits: GPIO.setup(d, GPIO.OUT)

        s_val = display_value.replace(':', '').rjust(4)
        
        loops = 1 if single_pass else 50 # 50 loops ~0.2s refresh
        for _ in range(loops):
            for digit_idx in range(4):
                char = s_val[digit_idx] if digit_idx < len(s_val) else ' '
                
                # Set segments
                for i in range(7):
                    GPIO.output(segments[i], num.get(char, num[' '])[i])
                
                # Handle colon (DP on digit 1)
                if ':' in display_value and digit_idx == 1:
                    GPIO.output(segments[7], 1)
                else:
                    GPIO.output(segments[7], 0)

                GPIO.output(digits[digit_idx], 0) # Select digit
                time.sleep(0.001) 
                GPIO.output(digits[digit_idx], 1) # Deselect digit

def blink_4sd(settings):
    if settings['simulated']:
        for _ in range(5):
            print("4SD: 00:00")
            time.sleep(0.5)
            print("4SD:     ")
            time.sleep(0.5)
    else:
        # Real blinking implementation
        import RPi.GPIO as GPIO
        segments = settings['segments']
        digits = settings['digits']
        
        # Turn off all segments/digits (blank)
        def clear_display():
            for d in digits: GPIO.output(d, 0)
            for s in segments: GPIO.output(s, 0)

        # Blink 5 times
        for _ in range(5):
            # ON phase (show 00:00 briefly repeated to persist vision)
            end_time = time.time() + 0.5
            while time.time() < end_time:
                actuate_4sd(settings, "00:00", single_pass=True)
            
            # OFF phase
            clear_display()
            time.sleep(0.5)
