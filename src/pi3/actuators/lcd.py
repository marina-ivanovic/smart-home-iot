#!/usr/bin/env python3

import threading


from time import sleep, strftime
from datetime import datetime
import threading
import json
import paho.mqtt.publish as publish
from env import HOSTNAME, PORT

batch = []
publish_data_counter = 0
publish_data_limit = 1 # Change the batch size as needed
counter_lock = threading.Lock()

def publisher_task(event, batch):
    global publish_data_counter, publish_data_limit
    while True:
        event.wait()
        with counter_lock:
            local_batch = batch.copy()
            publish_data_counter = 0
            batch.clear()
        publish.multiple(local_batch, hostname=HOSTNAME, port=PORT)
        print(f'published {publish_data_limit} DMS values')
        event.clear()

publish_event = threading.Event()
publisher_thread = threading.Thread(target=publisher_task, args=(publish_event, batch,))
publisher_thread.daemon = True
publisher_thread.start()

def lcd_callback(value, name, publish_event, settings):
    global publish_data_counter, publish_data_limit

    payload = {
        "measurement": "LcdText",
        "simulated": settings['simulated'],
        "runs_on": settings["runs_on"],
        "name": settings["name"],
        "value": value
    }

    with counter_lock:
        batch.append(('LcdText', json.dumps(payload), 0, True))
        publish_data_counter += 1

        if publish_data_counter >= publish_data_limit:
            publish_event.set()

def run_lcd(settings, threads, stop_event, name, looping_callback, dht1_humidity, dht1_temperature, dht2_humidity, dht2_temperature, dht3_humidity, dht3_temperature):
    if settings['simulated']:
        print(f"LCD showing: DHT1; T: {dht1_temperature}, Hum: {dht1_humidity}")
        whole_message = f"DHT1; T: {dht1_temperature}, Hum: {dht1_humidity}"
        lcd_callback(whole_message, settings['name'], publish_event, settings)
        sleep(3)
        print(f"LCD showing: DHT2; T: {dht2_temperature}, Hum: {dht2_humidity}")
        whole_message = f"DHT2; T: {dht2_temperature}, Hum: {dht2_humidity}"
        lcd_callback(whole_message, settings['name'], publish_event, settings)
        sleep(3)
        print(f"LCD showing: DHT3; T: {dht3_temperature}, Hum: {dht3_humidity}")
        whole_message = f"DHT3; T: {dht3_temperature}, Hum: {dht3_humidity}"
        lcd_callback(whole_message, settings['name'], publish_event, settings)
        sleep(3)
        
        looping_callback()
    else:
        from .PCF8574 import PCF8574_GPIO
        from .Adafruit_LCD1602 import Adafruit_CharLCD

        def loop(stop_event, settings):
            mcp.output(3,1)     # turn on LCD backlight
            lcd.begin(16,2)     # set number of LCD lines and columns      
            
            lcd.clear()
            lcd.setCursor(0,0)  # set cursor position
            message1 = 'DHT1; T: ' + dht1_temperature
            lcd.message( message1 +'\n' )# display CPU temperature
            message2 = 'Hum: ' + dht1_humidity
            lcd.message( message2 )   # display the time
            whole_message = message1 + ', ' + message2
            lcd_callback(whole_message, settings['name'], publish_event, settings)
            sleep(3)

            lcd.clear()
            lcd.setCursor(0,0)  # set cursor position
            message1 = 'DHT2; T: ' + dht2_temperature
            lcd.message( message1 +'\n' )# display CPU temperature
            message2 = 'Hum: ' + dht2_humidity
            lcd.message( message2 )   # display the time
            whole_message = message1 + ', ' + message2
            lcd_callback(whole_message, settings['name'], publish_event, settings)
            sleep(3)

            lcd.clear()
            lcd.setCursor(0,0)  # set cursor position
            message1 = 'DHT3; T: ' + dht3_temperature
            lcd.message( message1 +'\n' )# display CPU temperature
            message2 = 'Hum: ' + dht3_humidity
            lcd.message( message2 )   # display the time
            whole_message = message1 + ', ' + message2
            lcd_callback(whole_message, settings['name'], publish_event, settings)
            sleep(3)
                
        def destroy():
            lcd.clear()
            
        PCF8574_address = 0x27  # I2C address of the PCF8574 chip.
        PCF8574A_address = 0x3F  # I2C address of the PCF8574A chip.
        # Create PCF8574 GPIO adapter.
        try:
            mcp = PCF8574_GPIO(PCF8574_address)
        except:
            try:
                mcp = PCF8574_GPIO(PCF8574A_address)
            except:
                print ('I2C Address Error !')
                exit(1)

        # Create LCD, passing in MCP GPIO adapter.
        lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4,5,6,7], GPIO=mcp)
        loop(stop_event, settings)
        looping_callback()

