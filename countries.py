import requests as req


try:
    URL='https://restcountries.com/v2/all'

    data=req.request('GET' ,URL, verify=False)
    json_data=data.json()

    countries=[json_data[i]['name'] for i in range(len(json_data))]
except Exception as exception:
    print("Cannot read from api")