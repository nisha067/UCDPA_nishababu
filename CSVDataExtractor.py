import logging
import pandas as pd
import requests
import json
from pandas import json_normalize
import numpy as np
import configparser
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

Log_Format = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(filename = "logfile.log",
                    filemode = "w",
                    format = Log_Format,
                    level = logging.DEBUG)
logger = logging.getLogger()

# selecting the list of columns from the real world Traffic data set that I downloaded from Kaggle. I am going to use the selected columns in our project demo. More details can be found on the project Report. FYI, Source:
col_Selected = ["Date Of Stop","Time Of Stop","Description","Location","Accident","Belts","Personal Injury","Property Damage","Fatal","Commercial License","HAZMAT","Commercial Vehicle","Alcohol","Work Zone","State","VehicleType","Year","Make","Model","Color","Violation Type","Gender","Driver City"]
#col_Selected = ["Date Of Stop","VehicleType","Make","Model"]

# Import the selected columns from CSV file to a panda dataframe
df = pd.read_csv("Traffic_Violations.csv", usecols=col_Selected)
# Group the values by type of vehicle and slice the data base don the top value returned in the grouping
groupByVehicle = df.groupby("VehicleType").size()
topVehicletype = groupByVehicle.index[0]
# Slice the records that matches only top vehicle Type and ignore rest of the records
slicedSourceDf = df[df['VehicleType'] == topVehicletype]
logger.debug(slicedSourceDf["Make"]+" "+ slicedSourceDf["Model"])

# In my use case, I am going to validate the make (company Name) of the vehicle with a third party REST API #https://private-anon-cd3277b5ba-carsapi1.apiary-mock.com/cars GET API call.
# Since this is a third party API there may be a time when the system may brought down and may not be available for the usage. To tackle this situation i am storing the data as a one time copy in a JSON file "CarsDetails.JSON".  This will only be referred when the response from REST API is not 200. This way our sysstem will avoid downtime due to unavailability of third party API's.
api_url = "https://private-anon-cd3277b5ba-carsapi1.apiary-mock.com/cars"
response = requests.get(api_url)
if (response.status_code == 200):
    logger.info("Request to Cars API call is success!")
    logger.debug(response.json())
    carsLookupDF = json_normalize(response.json())
    # Code here will only run if the request is successful
else :
    logger.info("Request to Cars API call failed, so loading the static data locally stored with project as of 12/Jan/2022 ")
    carsLookupDF = pd.read_json('CarsDetails.JSON')


# Create a manual list for company Names that are not returned from REST API but still valid as per our knowledge.
config = configparser.RawConfigParser()
config.read('application.properties')
strMissingCompanies = config.get('appData' , 'missingCompanyNames')
listMissingCompanies = strMissingCompanies.split(",")
print(listMissingCompanies)

# convert both dataframe values to lower case for comparison with car list
lowerCarsLookupDF = carsLookupDF.applymap(lambda y:y.lower() if type(y) == str else y)
lowerSliceDF = slicedSourceDf.applymap(lambda x:x.lower() if type(x) == str else x)
logger.debug(lowerCarsLookupDF["make"])

#Iterate the vehicle compoany names received in the inout file and validae it with the Car iki list pulled from API call. Frame a new valid and invalid Company dataframes for further use.
print("Size of lowerSliceDF: "+str(lowerSliceDF.size))
validCompanyList = []
inValidCompanyList = []
for company in lowerSliceDF["Make"]:
    if company in lowerCarsLookupDF.values:
        logger.info("Value Exist for: "+company)
        validCompanyList.append(company)
    elif company in listMissingCompanies:
        logger.info("Value exist in manually prepared company List for: "+company)
        validCompanyList.append(company)
    else:
        logger.info("Company value not exist in : " + company)
        inValidCompanyList.append(company)

def filterDataframe(dataFrame, inputValue, filterColumn):
    listValue = list(dict.fromkeys(inputValue))
    listValue.sort()
    filteredDF = dataFrame[dataFrame[filterColumn].isin(listValue)]
    return filteredDF

validRecordsDF = filterDataframe(lowerSliceDF, validCompanyList, "Make")
ignoredRecordsDF = filterDataframe(lowerSliceDF, inValidCompanyList, "Make")

print("Valid Company Names that matches with the Traffic Violation List: "+str(validCompanyList))
print("Traffic records exist with Invalid Company Names that are not matching with our references: "+str(inValidCompanyList))
print("Number of cases Registered with valid vehicles: "+str(validRecordsDF.size))
print("Number of cases Registered with vehicles that are not identifiable: "+str(ignoredRecordsDF.size))


# Top 5 Car Companies that involves in frequent accident cases
sns.set(style="darkgrid")
colors = sns.color_palette('pastel')[0:5]

ax = sns.countplot(x="Make", data=validRecordsDF, order=validRecordsDF['Make'].value_counts().iloc[:5].index).set_title('Top 5 company vehicles involved in traffic violation cases')
plt.show()

#create pie chart based on Gender category
validRecordsDF.groupby(['Gender']).count().plot(kind='pie',subplots=True, y='Accident', autopct='%1.0f%%', colors = ['red', 'green', 'yellow'], title='Accident volume categorized by Gender')
plt.show()

# Top 5 Locations where the accident regularly happens
ax = sns.countplot(x="Location", data=validRecordsDF, order=validRecordsDF['Location'].value_counts().iloc[:5].index).set_title('Top 5 locations where frequent cases registered')
plt.show()

response_dict = json.loads(response.text)
logger.info(slicedSourceDf)
logger.error(slicedSourceDf)
logger.debug(slicedSourceDf)