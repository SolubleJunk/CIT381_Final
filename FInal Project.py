import json
import time
import urllib.request
import I2C_LCD_driver
from gpiozero import LED, Button
import board
import busio
from adafruit_seesaw.seesaw import Seesaw


on_off_button = Button(12, pull_up=True)

manualOverride = Button(16, pull_up=True)

relay =  LED(19)

#should be address 27
thelcd = I2C_LCD_driver.lcd()

# Initialize the I2C connection
i2c_bus = busio.I2C(board.SCL, board.SDA)
#uses address 36
ss = Seesaw(i2c_bus, addr=0x36)

# Get user's ZIP to find location ID
zip = input("Enter you zip code: ")

#function for sending an email
def send_email(recipient_email, subject, body):
        port = 587  # For starttls
        smtp_server = "smtp.gmail.com"
        sender_email = "wardc6cit381@gmail.com"  # Enter your address
        password = "ynle hrzg rgqu bvfo"
        # Build the email message
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = recipient_email

        # Send the email
        context = ssl.create_default_context()
        if port == 587:
                with smtplib.SMTP('smtp.gmail.com', port) as server:
                        server.starttls(context=context)
                        server.login(sender_email, password)
                        server.sendmail(sender_email, recipient_email, msg.as_string())
                        print("the email has been sent")
        elif port == 465:
                with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                        server.login(sender_email, password)
                        server.login(sender_email, password)
                        server.sendmail(sender_email, recipient_email, msg.as_string())
                        print("the email has been sent")
        elif port == 465:
                with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                        server.login(sender_email, password)
                        server.send_message(msg, from_addr=sender_email, to_addrs=recipient_email)
                        print("the email has been sent")
        else:
                print("the port you chose is not supported")

armedState = False
def button_press():
        global armedState
        if armedState:
                armedState = False
                print("The system is now off")
                relay.off()
                thelcd.lcd_clear()
        else:
                armedState = True
                print("The system is now on")

manual_override_active = False
manual_override_start_time = 0
def manual_override():
    if armedState:  # Check if the system is armed
        global manual_override_active, manual_override_start_time
        print("Manual Override enabled: Watering for 30 minutes")
        relay.on()
        manual_override_active = True
        manual_override_start_time = time.time()
    else:
        print("Cannot activate manual override: system is not on")

def get_location_id(zip):
    # Build url with user's zip
    apiURl = "http://dataservice.accuweather.com/locations/v1/postalcodes/US/search?apikey=zC5MGuMmgTlHcA6tenI14U9Ehe0DmtEI&q=%s&details=true" % zip
    # read and decode json into a variable
    with urllib.request.urlopen(apiURl) as url:
        data = json.loads(url.read().decode())
    # pull location ID out of JSON
    location_id = data[0]['Details']['Key']
    # return location ID for future use
    return location_id

# call function for getting location ID and store returned value ina variable
#location_id = get_location_id(zip)


def get_current_conditions(location_id):
    # build url with user's location ID
    apiURL = "http://dataservice.accuweather.com/currentconditions/v1/%s?apikey=zC5MGuMmgTlHcA6tenI14U9Ehe0DmtEI&details=true" % location_id
    # read and decode json into a variable
    with urllib.request.urlopen(apiURL) as url:
        data = json.loads(url.read().decode())
    # return the json
    return data


def get_historical_data(location_id):
    # build url with user's location ID
    apiURL = "http://dataservice.accuweather.com/currentconditions/v1/%s/historical/24?apikey=zC5MGuMmgTlHcA6tenI14U9Ehe0DmtEI&details=true" % location_id
    # read and decode json into a variable
    with urllib.request.urlopen(apiURL) as url:
        data = json.loads(url.read().decode())
    # return the json
    return data


def get_forecast(location_id):
    #build url with user's location ID
    apiURL = "http://dataservice.accuweather.com/forecasts/v1/daily/5day/%s?apikey=zC5MGuMmgTlHcA6tenI14U9Ehe0DmtEI&details=true" % location_id
    # read and decode json into a variable
    with urllib.request.urlopen(apiURL) as url:
        data = json.loads(url.read().decode())
    # return the json
    return data

# call the function  for getting current conditions and store its output in a variable
#current_conditions = get_current_conditions(location_id)
# call the function  for getting historical data and store its output in a variable
#historical_data = get_historical_data(location_id)
# call the function  for getting forecast and store its output in a variable
#forecast = get_forecast(location_id)


# pull specific pieces of data from the JSON that we want to base our irrigation logic on
#precip_24_hours = historical_data[23]['PrecipitationSummary']['Past24Hours']['Imperial']['Value']

#is_it_raining = current_conditions[0]['HasPrecipitation']

#will_it_rain_chance = forecast['DailyForecasts'][1]['Day']['PrecipitationProbability']

#will_it_rain_amount = forecast['DailyForecasts'][1]['Day']['TotalLiquid']['Value']

#Set of test variables so that the program will always irrigate
precip_24_hours = 0.01

is_it_raining = True

will_it_rain_chance = 30

will_it_rain_amount = 0.01


on_off_button.when_pressed = button_press
manualOverride.when_pressed = manual_override
# Main Loop
while True:
    if manual_override_active and time.time() - manual_override_start_time >= 40:
        manual_override_active = False

    if manual_override_active:
        time.sleep(1)
        continue

    relay.off()
    thelcd.lcd_clear()
    #get moisture level from sensor
    moisture = ss.moisture_read()
    if armedState:
        if int(moisture) < 500:
            # check recent precipitation levels
            if float(precip_24_hours) >= 0.15:
                print("No irrigation needed: Historical Rain")
            # check if it is raining
            elif is_it_raining:
                print("No irrigation needed: It is currently raining")
            # check if it will rain tomorrow
            elif int(will_it_rain_chance) >= 70 and float(will_it_rain_amount) >= 0.15:
                print("No irrigation needed: Future rain")
            # If none of the above is true we need to irrigate
            else:
                print("Irrigating")
                relay.on()
                #create and send email with current info
        else:
            print("No irrigation needed: Suffiecient soil moisture")

        #display the current temp on the LCD screen
        #thelcd.lcd_display_string("Current Temp: ", 1)
        #thelcd.lcd_display_string(str(current_conditions[0]['Temperature']['Imperial']['Value']), 2)
        # Delay the loop so it doesnt call the API too often (I had it set lower for testing purposes)
        time.sleep(30)
    else:
        print("The system is currently turned off")
        time.sleep(10)













