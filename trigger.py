import RPi.GPIO as GPIO
from time import sleep

DESK_PIN = 17

try:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(DESK_PIN, GPIO.OUT)

    GPIO.output(DESK_PIN, GPIO.HIGH)
    sleep(0.25)
    GPIO.output(DESK_PIN, GPIO.LOW)
finally:
    GPIO.cleanup()
