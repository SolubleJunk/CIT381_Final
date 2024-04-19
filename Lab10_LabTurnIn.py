# CIT 381 - Spring 23-24
# Author: Dennis Briggs
# Created: 4/17/24
# Lab 10 - Using Internet Data
# Irrigation Decision using AccuWeather Data


# Import needed modules
import json
import time
import urllib.request
import I2C_LCD_driver
from gpiozero import LED

# Function that takes a zip and api key and returns the location ID

def getLocationID(zipcode, apiKey):
    apiurl = 'http://dataservice.accuweather.com/locations/v1/postalcodes/US/search?apikey=%s&q=%s' % (apiKey, zipcode)
    print("Getting Location ID with url: " + apiurl)
    with urllib.request.urlopen(apiurl) as url:
        data = json.loads(url.read().decode())
    return data[0]['Key']
    

# Function that takes the location ID and returns current conditions as a python list for later parsing
def getCurrentCond(locID, apiKey):
    apiurl = 'http://dataservice.accuweather.com/currentconditions/v1/%s?apikey=%s&details=true' % (locID, apiKey)
    print("Getting current conditions with url: " + apiurl)
    with urllib.request.urlopen(apiurl) as url:
        data = json.loads(url.read().decode())
    return data

# Function that takes the location ID and the API and returns the LAST 24 HOURS conditions as a
# Python list for later parsing.

def getLastTwentyFour(locID, apiKey):
    apiurl = 'http://dataservice.accuweather.com/currentconditions/v1/%s/historical/24?apikey=%s&details=true' % (locID, apiKey)
    print("Getting last 24 hours conditions with url: " + apiurl)
    with urllib.request.urlopen(apiurl) as url:
        data = json.loads(url.read().decode())
    return data

# Function that takes location ID and the API key and returns the FIVE-DAY-FORCAST

def getForecast(locID, apiKey):
    
    apiurl = 'http://dataservice.accuweather.com/forecasts/v1/daily/5day/%s?apikey=%s&details=true' % (locID, apiKey)
    print("Getting getting 5 day forecast with url: " + apiurl)
    with urllib.request.urlopen(apiurl) as url:
        data = json.loads(url.read().decode())
    return data

# Testing for rain volume in the last 24 hours
# Choosing hour sounded more logical than hour 0, otherwise the time window would be two days?
def hasBeenRain(data):
    if(float(data[23]['PrecipitationSummary']['Past24Hours']['Imperial']['Value']) > 0.15):
        return True
    else:
        return False

# Testing for is it raining now
def isItRaining(data):
    if(data[0]['HasPrecipitation']):
        return True
    else:
        return False

# Testing for rain chance (during the day?)
def isItRainingTomorrow(data):
    if(float(data['DailyForecasts'][1]['Day']['PrecipitationProbability']) > 70):
        return True
    else:
        return False
            
# Run the irrigation valves
def runIrrigation():
    global relay
    relay.on()
    sleep(900)
    relay.off()
    
def main():
    # Define the LCD screen
    thelcd = I2C_LCD_driver.lcd()

    # Define Irrigation Valve Relay
    relay = LED(19)
    relay.off()

    # Required Variables
    locationID = 'LocationToBeUpdated'
    homezip = '45215'
    apiKeyString = '38smoJ6LAzLfDDZ3HdHbeBn6ilickJKn'

    locationID = getLocationID(homezip, apiKeyString)

    currentConData = getCurrentCond(locationID, apiKeyString)
    lastTwentyFour = getLastTwentyFour(locationID, apiKeyString)
    currentForecast = getForecast(locationID, apiKeyString)

    # Has there been significant precipitation in the last 24?
    if(hasBeenRain(lastTwentyFour)):
        print('It has already rained enough in the last 24 hours.')
        
    # Is it raining now?
    elif(isItRaining(currentConData)):
        print('It is raining right now.')
        
    # Is it going to rain tomorrow?
    elif(isItRainingTomorrow(currentForecast)):
        print('It is going to rain tomorrow.')

    # All test cases failing means we need to irrigate
    else:
        print('All scenarios to avoid irrigation cleared, enabling irrigation system.')
        runIrrigation()

    # Display current weather conditions
    if(isItRaining(currentConData)):
        raining = 'Yes'
    else:
        raining = 'No'
        
    if(isItRainingTomorrow(currentForecast)):
        chanceOfRain = 'Yes'
    else:
        chanceOfRain = 'No'
    
    thelcd.lcd_clear()
    thelcd.lcd_display_string("Rain now: %s" % str(raining),1)
    thelcd.lcd_display_string("Rain Tomorr: %s" % chanceOfRain, 2)

    
main()    

    
