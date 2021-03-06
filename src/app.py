from sense_hat import SenseHat
import logging
from flask import Flask, render_template
from flask_ask import Ask, statement, question, session
import os
import multiprocessing

# Setting up the SenseHAT
sense = SenseHat()
sense.clear()

# Setting up Alexa
app = Flask(__name__)
ask = Ask(app, "/")

# Wether or not show results on the display
SHOW_DISPLAY = True if os.getenv('DISPLAY', '1') == '1' else False

def get_CPU_temperature():
    """Get CPU temperature
    Code from: https://www.raspberrypi.org/forums/viewtopic.php?p=875577&sid=c6042b50b58cff9f606b56115e5be3d8#p875577
    """
    res = os.popen('vcgencmd measure_temp').readline()
    return float(res.replace("temp=","").replace("'C\n",""))

def get_adjusted_temperature():
    """SenseHAT measures too high temperature because it's close to the RPi SoC,
    use this approximation to get closer to the real value even if the reading is off
    """
    cpu_temperature = get_CPU_temperature()
    ambient_temperature = sense.get_temperature_from_pressure()
    adjusted_temperature = ambient_temperature - ( (cpu_temperature - ambient_temperature) / 1.5 )
    return adjusted_temperature

def display_text(text):
    sense.show_message(text)

# Alexa Services
@ask.launch
def get_hello():
    card_title = ('RPi with SenseHAT')
    hello_msg = render_template('hello')
    # prompt = render_template('prompt')
    # return question(hello_msg).reprompt(prompt).simple_card(card_title, hello_msg)
    return statement(hello_msg).simple_card(card_title, hello_msg)

# ## QuestionIntent, notes here, does not work yet
# # Intent
# {
# /*"intent": "QuestionIntent",
# "slots": [{
#           "name": "topic",
#           "type": "SENSOR"
#           }]
# }
#
# # Custom slots
# temperature
# pressure
# humidity
#
# # Sample utternance:
# QuestionIntent {topic}
#
# @ask.intent('QuestionIntent')
# def answer_question(target):
#     if target == 'temperature':
#         get_temperature()
#     elif target == 'humidity':
#         get_humidity()
#     elif target == 'pressure':
#         get_pressure()
#     else:
#         prompt = render_template('prompt')
#         return statement(prompt)

@ask.intent('EnvironmentIntent')
def get_environment():
    temperature = round(get_adjusted_temperature(), 1)
    humidity = int(sense.get_humidity())
    pressure = round(sense.get_pressure(), 1)
    environment_msg = render_template('environment', temperature=temperature, humidity=humidity, pressure=pressure)
    card_title = 'RPi with SenseHAT'
    environment_card = render_template('environment_card', temperature=temperature, humidity=humidity, pressure=pressure)

    if SHOW_DISPLAY:
        environment_display = render_template('environment_display', temperature=temperature, humidity=humidity, pressure=pressure)
        d = multiprocessing.Process(target=display_text, kwargs={'text': environment_display})
        d.daemon = True
        d.start()

    return statement(environment_msg).simple_card(card_title, environment_card)

@ask.intent('TemperatureIntent')
def get_temperature():
    temperature = round(get_adjusted_temperature(), 1)
    temperature_msg = render_template('temperature', temperature=temperature)
    card_title = 'RPi with SenseHAT'
    temperature_card = render_template('temperature_card', temperature=temperature)

    if SHOW_DISPLAY:
        temperature_display = render_template('temperature_display', temperature=temperature)
        d = multiprocessing.Process(target=display_text, kwargs={'text': temperature_display})
        d.daemon = True
        d.start()

    return statement(temperature_msg).simple_card(card_title, temperature_card)

@ask.intent('HumidityIntent')
def get_humidity():
    humidity = int(sense.get_humidity())
    humidity_msg = render_template('humidity', humidity=humidity)
    card_title = 'RPi with SenseHAT'
    humidity_card = render_template('humidity_card', humidity=humidity)

    if SHOW_DISPLAY:
        humidity_display = render_template('humidity_display', humidity=humidity)
        d = multiprocessing.Process(target=display_text, kwargs={'text': humidity_display})
        d.daemon = True
        d.start()

    return statement(humidity_msg).simple_card(card_title, humidity_card)

@ask.intent('PressureIntent')
def get_pressure():
    pressure = round(sense.get_pressure(), 1)
    pressure_msg = render_template('pressure', pressure=pressure)
    card_title = 'RPi with SenseHAT'
    pressure_card = render_template('pressure_card', pressure=pressure)

    if SHOW_DISPLAY:
        pressure_display = render_template('pressure_display', pressure=pressure)
        d = multiprocessing.Process(target=display_text, kwargs={'text': pressure_display})
        d.daemon = True
        d.start()

    return statement(pressure_msg).simple_card(card_title, pressure_card)

if __name__ == '__main__':
    # Set up SenseHAT display rotation
    allowed_angles = ['0', '90', '180', '270']
    display_rotate = os.getenv('ROTATE', '0')
    if display_rotate not in allowed_angles:
        display_rotate = '0'
    sense.set_rotation(int(display_rotate))

    # Load DEBUG variable from the environment
    debug = True if os.getenv('DEBUG', '0') == '1' else False
    loglevel = logging.DEBUG if debug else logging.INFO
    logging.getLogger("flask_ask").setLevel(loglevel)
    app.run(host='0.0.0.0', port=80, debug=debug)
