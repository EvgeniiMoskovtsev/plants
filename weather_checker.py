import requests
import json
from loguru import logger
import time

@logger.catch
def get_weather_forecast():
    url = "https://ai-weather-by-meteosource.p.rapidapi.com/hourly"

    querystring = {"lat":"41.7151","lon":"44.8271","timezone":"Asia/Tbilisi","language":"en","units":"metric"}

    headers = {
        "X-RapidAPI-Key": "c004c07e50msh04b4086adc181efp14dd4ajsn2e0472afdb51",
        "X-RapidAPI-Host": "ai-weather-by-meteosource.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    data = response.json()["hourly"]["data"]

    dates_and_temps = [{"date": item["date"], "temperature": item["temperature"]} for item in data]
    
    return dates_and_temps
    
while True:
    logger.info("Get forecast")
    forecast = get_weather_forecast()
    
    logger.info("Save forecast")
    with open("/home/evgenii/plants_final/weather_data.json", "w") as f:
        json.dump(forecast, f, indent=4)
    logger.info("Forecast is saved. Sleep 24 hours")
    time.sleep(86400) # 24 hours

