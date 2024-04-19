#Pieced together parts of labs we will likely use

import json
import time
import urllib.request
import I2C_LCD_driver
from gpiozero import LED

#create the necessary objects for turning on/off the LED, relay, and LCD screen
led = LED(17, active_high = False)

relay =  LED(5)

thelcd = I2C_LCD_driver.lcd()

# Get user's ZIP to find location ID
zip = input("Enter you zip code: ")


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
location_id = get_location_id(zip)


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
current_conditions = get_current_conditions(location_id)
# call the function  for getting historical data and store its output in a variable
historical_data = get_historical_data(location_id)
# call the function  for getting forecast and store its output in a variable
forecast = get_forecast(location_id)


# pull specific pieces of data from the JSON that we want to base our irrigation logic on
precip_24_hours = historical_data[23]['PrecipitationSummary']['Past24Hours']['Imperial']['Value']

is_it_raining = current_conditions[0]['HasPrecipitation']

will_it_rain_chance = forecast['DailyForecasts'][1]['Day']['PrecipitationProbability']

will_it_rain_amount = forecast['DailyForecasts'][1]['Day']['TotalLiquid']['Value']

#Set of test variables so that the program will always irrigate
#precip_24_hours = 0.01

#is_it_raining = False

#will_it_rain_chance = 30

#will_it_rain_amount = 0.01


# Main Loop
while True:
    #Turn off or clear all objects at the start of each loop
    led.off()
    relay.off()
    thelcd.lcd_clear()
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
        led.on()
        relay.on()

    #display the current temp on the LCD screen
    thelcd.lcd_display_string("Current Temp: ", 1)
    thelcd.lcd_display_string(str(current_conditions[0]['Temperature']['Imperial']['Value']), 2)
    # Delay the loop so it doesnt call the API too often (I had it set lower for testing purposes)
    time.sleep(30)
