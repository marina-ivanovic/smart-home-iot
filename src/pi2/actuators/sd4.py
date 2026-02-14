import time

# TM1637-style display ili multipleksovani 7-seg
def actuate_4sd(settings, display_value):
    """
    Display value on 4-digit 7-segment display.
    display_value: string like "12:34" or "00:00"
    """
    if settings['simulated']:
        t = time.localtime()
        print(f"\nTimestamp: {time.strftime('%H:%M:%S', t)} | 4SD Display: {display_value}\n")
    else:
        # Real 7-segment display implementation
        import RPi.GPIO as GPIO
        
        segments = settings['segments']
        digits = settings['digits']
        
        # Number to segment mapping (a,b,c,d,e,f,g)
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
            '9': (1,1,1,1,0,1,1),
            ':': (0,0,0,0,0,0,0)  # colon handled by DP (8th pin)
        }
        
        # Setup GPIO
        for segment in segments:
            GPIO.setup(segment, GPIO.OUT)
            GPIO.output(segment, 0)
        
        for digit in digits:
            GPIO.setup(digit, GPIO.OUT)
            GPIO.output(digit, 1)
        
        # Display multiplexing (brief display to avoid blocking)
        s = display_value.replace(':', '').rjust(4)
        for _ in range(10):  # Quick refresh cycles
            for digit_idx in range(4):
                char = s[digit_idx] if digit_idx < len(s) else ' '
                for seg_idx in range(7):
                    GPIO.output(segments[seg_idx], num[char][seg_idx])
                
                # Handle colon (decimal point on digit 1)
                if ':' in display_value and digit_idx == 1:
                    GPIO.output(segments[7], 1)  # DP on
                else:
                    GPIO.output(segments[7], 0)
                
                GPIO.output(digits[digit_idx], 0)
                time.sleep(0.001)
                GPIO.output(digits[digit_idx], 1)

def blink_4sd(settings):
    """Blink display with 00:00 when timer expires."""
    if settings['simulated']:
        for _ in range(5):
            print("4SD: 00:00")
            time.sleep(0.5)
            print("4SD:     ")
            time.sleep(0.5)
    else:
        # Implement real blinking
        pass
