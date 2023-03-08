import folium
from geopy.geocoders import ArcGIS
import base64

WEATHER_CODE={}
WEATHER_CODE.update({0:'sunny.png'})
WEATHER_CODE.update({1:'cloudy.png'})
WEATHER_CODE.update({2:'cloudy.png'})
WEATHER_CODE.update({3:'cloudy.png'})
WEATHER_CODE.update({45:'fog.png'})
WEATHER_CODE.update({48:'fog.png'})
WEATHER_CODE.update({51:'light_rain.png'})
WEATHER_CODE.update({53:'light_rain.png'})
WEATHER_CODE.update({55:'light_rain.png'})
WEATHER_CODE.update({56:'light_rain.png'})
WEATHER_CODE.update({57:'light_rain.png'})
WEATHER_CODE.update({61:'heavy_rain.png'})
WEATHER_CODE.update({63:'heavy_rain.png'})
WEATHER_CODE.update({65:'heavy_rain.png'})
WEATHER_CODE.update({66:'heavy_rain.png'})
WEATHER_CODE.update({67:'heavy_rain.png'})
WEATHER_CODE.update({71:'snow.png'})
WEATHER_CODE.update({73:'snow.png'})
WEATHER_CODE.update({75:'snow.png'})
WEATHER_CODE.update({77:'snow.png'})
WEATHER_CODE.update({80:'light_rain.png'})
WEATHER_CODE.update({81:'light_rain.png'})
WEATHER_CODE.update({82:'light_rain.png'})
WEATHER_CODE.update({85:'snow.png'})
WEATHER_CODE.update({86:'snow.png'})
WEATHER_CODE.update({95:'snow.png'})
WEATHER_CODE.update({96:'snow.png'})
WEATHER_CODE.update({99:'snow.png'})



#Convert address to GPS location
def GPS_location(address):
    loc=ArcGIS()
    location=loc.geocode(address)
    if location!=None:
        lat=location.latitude
        lon=location.longitude
        return [lat,lon]
    else:
        return None



#Draw map and save as html
def DrawMap(country, city, address, name, firstname, code):

    #icon picture
    my_logo=folium.features.CustomIcon(icon_image=f"weather_icons/{WEATHER_CODE[code]}",icon_size=(100,100))

    #Location
    gps_loc=GPS_location(f"{country}, {city}, {address}")
    if gps_loc!=None:

        #html link        
        html="""<a href="https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s&current_weather=true" target="_blank">%s</a>"""
        
        #load map
        map=folium.Map(location=gps_loc,zoom_start=15)

        #Feature group
        city_fg=folium.FeatureGroup(name=f"{name} {firstname}")

        #Show marker
        iFrame=folium.IFrame(html=html %(f"{gps_loc[0]}",f"{gps_loc[1]}",f"{city}"), width=200,height=100)
        city_fg.add_child(folium.Marker(location=gps_loc,icon=my_logo,tooltip=f"{name} {firstname}",popup=folium.Popup(iFrame)))

        #add feature group to map
        map.add_child(city_fg)
 
        #add layer control
        map.add_child(folium.LayerControl())

        #save map
        return  map

