from gpiozero import LED
from time import sleep

desk = LED(17)

desk.on()
sleep(0.25)
desk.off()