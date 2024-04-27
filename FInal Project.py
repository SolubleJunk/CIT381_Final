###########################
# Final Project - Group 5
# Notes: Irrigation Project
#
# Primary Features:
# Monthly Report Sending
# Manual Report Prompting via Button
# Intelligent Watering based on weather
# Monitoring Moisture Level with Sensor -- If Sensor Levels is too low force a watering session
# Manual Override to Prompt Watering Regardless
# On/Off switch for System System
# LCD Screen for visual display of On/Off and Moisture Level
#
# Colby Ward, Christina Umberg, Nick Carter, Dennis Briggs
###########################

###########################
# Required Library Imports
# 
###########################
import smtplib, ssl
from email.message import EmailMessage
import json
import time
import urllib.request
import I2C_LCD_driver
from gpiozero import LED, Button
import board
import busio
from adafruit_seesaw.seesaw import Seesaw
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Device Object Instantiation
# Easy Devices
on_off_button = Button(12, pull_up=True)
manualOverride = Button(16, pull_up=True)
manual_send_email_button = Button(20, pull_up=True)
relay1 = LED(6, active_high=False)
relay2 = LED(24, active_high=False)

# LCD Setup - Should be address 27
thelcd = I2C_LCD_driver.lcd()

# Moisture Setup - Should be address 36
i2c_bus = busio.I2C(board.SCL, board.SDA)
ss = Seesaw(i2c_bus, addr=0x36)

###########################
# Hard Coded Variables
# 
###########################

zip = "41073"
armedState = True
manual_override_active = False
manual_override_start_time = 0

# Variables for email subject and recipient
subject = "Irrigation Alert"
recipient_email = "wardc6cit381@gmail.com"

# Variable to track irrigation status
is_irrigating = False


###########################
# Defined Functions
# 
###########################

# E-mail Sending to User
def send_email(html_content, subject, recipient_email):
        port = 587  # For starttls
        smtp_server = "smtp.gmail.com"
        sender_email = "wardc6cit381@gmail.com"  # Enter your address
        password = "ynle hrzg rgqu bvfo"
        # Build the email message
        msg = MIMEMultipart("alternative")
        # Attach HTML content to the email
        msg.attach(MIMEText(html_content, 'html'))

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

# Return html content for email with up to date irrigation and moisture status
def html_for_email(is_irrigating, moisture):
    if is_irrigating == True:
        irrigation_status = "irrigating"
    else:
        irrigation_status = "not irrigating"
    html_content=f"""
    <html>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <body style=" min-height: 50vh; background-color: #F0F0F0; border-radius: 10px;">
        <table align="center" vertical-align: middle">
            <tr>
                <td align="center">
                    <table width="400" height="300" border="5" style="background-color: #FFFFFF; margin-top: 22px; border-radius: 35px; border-color:#9E9E9E; border-style:solid;">
                        <tr>
                            <td  style="padding: 20px; text-align: center; color: #1A4D2E; border-style: hidden;">
                                <h1 style="color: #1A4D2E;">Irrigation Alert</h1>
                                <p style="color: #1A4D2E;">  Your system is currently <b>{irrigation_status}</b></p>
                                <p style="color: #1A4D2E;"> Soil Moisture: <b>{moisture}</b></p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    return html_content

# Button Press Event for On/Off
def button_press():
        global armedState
        if armedState:
                armedState = False
                print("The system is now off")
                relay1.off()
                relay2.off()
                thelcd.lcd_clear()
        else:
                armedState = True
                print("The system is now on")

# Manual Override to Force Irrigation
def manual_override():
    if armedState:  # Check if the system is armed
        global manual_override_active, manual_override_start_time
        print("Manual Override enabled: Watering for 30 minutes")
        relay1.on()
        relay2.on()
        html_content = html_for_email(is_irrigating, moisture)
        send_email(html_content, subject, recipient_email)
        manual_override_active = True
        manual_override_start_time = time.time()
    else:
        print("Cannot activate manual override: system is not on")

# Manual Prompt for E-mail Send
def manual_send_email():
    send_email(html_content, subject, recipient_email)

# Retrive Location_ID based on Zip of User
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

# Retrieve AccuWeather Current Conditions
def get_current_conditions(location_id):
    # build url with user's location ID
    apiURL = "http://dataservice.accuweather.com/currentconditions/v1/%s?apikey=zC5MGuMmgTlHcA6tenI14U9Ehe0DmtEI&details=true" % location_id
    # read and decode json into a variable
    with urllib.request.urlopen(apiURL) as url:
        data = json.loads(url.read().decode())
    # return the json
    return data

# Retrieve AccuWeather Historical Information
def get_historical_data(location_id):
    # build url with user's location ID
    apiURL = "http://dataservice.accuweather.com/currentconditions/v1/%s/historical/24?apikey=zC5MGuMmgTlHcA6tenI14U9Ehe0DmtEI&details=true" % location_id
    # read and decode json into a variable
    with urllib.request.urlopen(apiURL) as url:
        data = json.loads(url.read().decode())
    # return the json
    return data

# Retrieve AccuWeather Forecast Information
def get_forecast(location_id):
    #build url with user's location ID
    apiURL = "http://dataservice.accuweather.com/forecasts/v1/daily/5day/%s?apikey=zC5MGuMmgTlHcA6tenI14U9Ehe0DmtEI&details=true" % location_id
    # read and decode json into a variable
    with urllib.request.urlopen(apiURL) as url:
        data = json.loads(url.read().decode())
    # return the json
    return data

###########################
# Retrieve Information from AccuWeather
# 
###########################

# call function for getting location ID and store returned value in a variable
#location_id = get_location_id(zip)

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

###########################
# Static Variables For Test Cases
# 
###########################

#Set of test variables so that the program will always irrigate
precip_24_hours = 0.01

is_it_raining = False

will_it_rain_chance = 30

will_it_rain_amount = 0.01


###########################
# Main Function
# 
###########################

# Event Driven Object Creation
# if the on/off button is pressed turn on/off the system
on_off_button.when_pressed = button_press
# if the manual override button is pressed override the current state of the loop and irrigate for X amount of time
manualOverride.when_pressed = manual_override
# if the send email button is pressed send an email with current information about the system
manual_send_email_button.when_pressed = manual_send_email

while True:
    if manual_override_active and time.time() - manual_override_start_time >= 40:
        manual_override_active = False

    if manual_override_active:
        time.sleep(1)
        continue

    relay1.off()
    relay2.off()
    is_irrigating = False
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
                relay1.on()
                relay2.on()
                is_irrigating = True # update irrigation status
                html_content = html_for_email(is_irrigating, moisture) #get html content for email
                send_email(html_content, subject, recipient_email) #send email
        else:
            print("No irrigation needed: Suffiecient soil moisture")
            #is_irrigating = False
        #display the current status of the sytem on the LCD screen
        thelcd.lcd_display_string("Status: ON", 1)
        thelcd.lcd_display_string("Moisture: " + str(moisture), 2)
        # Delay the loop so it doesnt call the API too often (I had it set lower for testing purposes)
        time.sleep(30)
    else:
        print("The system is currently turned off")
        thelcd.lcd_display_string("Status: OFF", 1)

        thelcd.lcd_display_string("Moisture: " + str(moisture), 2)
        time.sleep(10)

