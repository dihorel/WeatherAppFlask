import requests as req
import string
import random

WEATHER_CODE={}
WEATHER_CODE.update({0:'Clear sky'})
WEATHER_CODE.update({1:'Mainly clear, partly cloudy, and overcast'})
WEATHER_CODE.update({2:'Mainly clear, partly cloudy, and overcast'})
WEATHER_CODE.update({3:'Mainly clear, partly cloudy, and overcast'})
WEATHER_CODE.update({45:'Fog and depositing rime fog'})
WEATHER_CODE.update({48:'Fog and depositing rime fog'})
WEATHER_CODE.update({51:'Drizzle: Light, moderate, and dense intensity'})
WEATHER_CODE.update({53:'Drizzle: Light, moderate, and dense intensity'})
WEATHER_CODE.update({55:'Drizzle: Light, moderate, and dense intensity'})
WEATHER_CODE.update({56:'Freezing Drizzle: Light and dense intensity'})
WEATHER_CODE.update({57:'Freezing Drizzle: Light and dense intensity'})
WEATHER_CODE.update({61:'Rain: Slight, moderate and heavy intensity'})
WEATHER_CODE.update({63:'Rain: Slight, moderate and heavy intensity'})
WEATHER_CODE.update({65:'Rain: Slight, moderate and heavy intensity'})
WEATHER_CODE.update({66:'Freezing Rain: Light and heavy intensity'})
WEATHER_CODE.update({67:'Freezing Rain: Light and heavy intensity'})
WEATHER_CODE.update({71:'Snow fall: Slight, moderate, and heavy intensity'})
WEATHER_CODE.update({73:'Snow fall: Slight, moderate, and heavy intensity'})
WEATHER_CODE.update({75:'Snow fall: Slight, moderate, and heavy intensity'})
WEATHER_CODE.update({77:'Snow grains'})
WEATHER_CODE.update({80:'Rain showers: Slight, moderate, and violent'})
WEATHER_CODE.update({81:'Rain showers: Slight, moderate, and violent'})
WEATHER_CODE.update({82:'Rain showers: Slight, moderate, and violent'})
WEATHER_CODE.update({85:'Snow showers slight and heavy'})
WEATHER_CODE.update({86:'Snow showers slight and heavy'})
WEATHER_CODE.update({95:'Thunderstorm: Slight or moderate'})
WEATHER_CODE.update({96:'Thunderstorm with slight and heavy hail'})
WEATHER_CODE.update({99:'Thunderstorm with slight and heavy hail'})

def extract_coordinates(town,country):

    URL=f'https://geocoding-api.open-meteo.com/v1/search?name={town}'

    data=req.request('GET' ,URL)
    json_data=data.json()
    print(json_data)

    result=list()

    if len(json_data)>1:
        for item in range(len(json_data['results'])):
            if 'country' in json_data['results'][item].keys():
                if json_data['results'][item]['country'].lower()==country.lower():
                    result.append((json_data['results'][item]['latitude'],json_data['results'][item]['longitude'] ))   

        if len(result)>0:
            return result[0]
        else:
            return(-91,-91)

    else:
        return(-91,-91)


def get_actual_weather(latitude,longitude):
    URL=f'https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true'
    data=req.request('GET' ,URL)
    json_data=data.json()
    if 'error' in json_data.keys():       
        return json_data
    else:
        return json_data['current_weather']
    

def return_weather_message(town,country,latitude,longitude,actual_weather):
    message=f'The temperature in {town},{country}({latitude},{longitude}) is {actual_weather["temperature"]} degrees Celsius, wind speed of {actual_weather["windspeed"]} and wind direction {actual_weather["winddirection"]}.{WEATHER_CODE[actual_weather["weathercode"]]}'
    return message



def generate_api_key():
    letters=string.ascii_lowercase
    numbers=string.digits
    letters_numbers=letters+numbers
    code=random.choices(letters_numbers,k=5)
    api_key=''.join(code)
    return api_key