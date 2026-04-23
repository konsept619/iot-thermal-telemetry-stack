import machine
import utime
import dht
from machine import I2C, Pin, ADC, PWM
from pico_i2c_lcd import I2cLcd

# --- LCD ---
I2C_ADDR = 0x27
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)

# --- DHT11 ---
sensor = dht.DHT11(Pin(2))
light_sensor = ADC(Pin(27))

# --- PWM and fan ---
fan = PWM(Pin(16))
fan.freq(1000)

TEMP_MIN = 24.0
TEMP_MAX = 28.0

print("Measuring...")
lcd.putstr("Initialization...")
utime.sleep(2)
lcd.clear()

try:
    while True:
        try:
            sensor.measure()
            temp = sensor.temperature
            hum = sensor.humidity
            
            light_raw = light_sensor.read_u16()
            light_percent = round((light_raw / 65535) * 100, 1)
            
            # PWM thresholds
            if temp <= TEMP_MIN:
                duty = 0
            elif temp >= TEMP_MAX:
                duty = 65535
            else:
                duty = int(((temp - TEMP_MIN)/(TEMP_MAX - TEMP_MIN)) * 65535)
            
            fan.duty_u16(duty)
            power_fan = round((duty / 65535) * 100, 1)

            # Providing data for connector
            print(f"{temp},{hum},{light_percent},{power_fan}")

            # Displaying data on LCD
            lcd.clear()
            lcd.move_to(0, 0)
            lcd.putstr(f"T:{temp}C H:{hum}%")
            lcd.move_to(0, 1)
            lcd.putstr(f"Went:{power_fan}%")

        except OSError as e:
            print("Sensor reading error!")
            lcd.clear()
            lcd.move_to(0, 0)
            lcd.putstr("Sensor error")

        
        utime.sleep(5)

except KeyboardInterrupt:
    # Executes after CTRL+C
    print("\nThe program was stopped by the user.")

finally:
    # Executes always
    print("Shutting down a system and stopping the motor...")
    fan.duty_u16(0)     # Stop PWM
    fan.deinit()        # Clear pin
    lcd.clear()
    lcd.putstr("System OFF")
