import os
from typing import Type
import json
from requests import get
from flask import Flask, make_response ,request
from flask_mongoengine import MongoEngine
from datetime import date, datetime,timedelta
from flask_cors import CORS



project_root = os.path.dirname(__file__)
app = Flask(__name__)
CORS(app)

database_name = "vovid-gb"
DB_URI = "mongodb+srv://chanon:132231@cluster0.broqy.mongodb.net/vovid-gb?authSource=admin&replicaSet=Cluster0-shard-0&readPreference=primary&appname=MongoDB%20Compass&ssl=true"
app.config["MONGODB_HOST"] = DB_URI
db = MongoEngine()
db.init_app(app)




@app.route("/30-day",methods=['POST'])
def timeline():
   url = "https://covid19.ddc.moph.go.th/api/Cases/timeline-cases-by-provinces"
   response = get(url)
   jsonText = json.loads(response.text)
   jsonText.reverse()
   arr = []
   for i in range(78*7):
      content = jsonText[i]
      report  = Daily_report(
         date = content["txn_date"],
         newCase = content["new_case"],
         totalCase = content["total_case"],
         newDeath = content["new_death"],
         death = content["total_death"],
         location = content["province"]
      )
      # arr.append(content["province"])
      # print(content["province"]+" have " + str(arr.count(content["province"])))
      report.save()
   # print(type(response))
   return make_response()





@app.route("/api/weekly-cases2",methods=['get'])
def todayCases():
   today = date.today()
   curr_date = today
   date_arr = []
   exc_field = ["id","created_at"]
  
   while len(date_arr)<7:
      today_date = curr_date.isoformat()
      print("today date is "+today_date)
      date_arr.append(today_date)
      curr_date = curr_date-timedelta(days=1)
   
   responseData = Daily_report.objects(date__in=date_arr).exclude(*exc_field).to_json()
   return responseData

@app.route("/api/weekly-cases",methods=['get'])
def todayCases2():
   today = date.today()
   curr_date = today
   date_arr = []
   exc_field = ["id","created_at"]
   data_arr = []
  
   while len(date_arr)<7:
      today_date = curr_date.isoformat()
      date_arr.append(today_date)      
      qData = Daily_report.objects(date=today_date).exclude(*exc_field).order_by("location").to_json()
      reData ={"date":today_date,"result":json.loads(qData)}
      curr_date = curr_date-timedelta(days=1)   
      data_arr.append(reData)

   return json.dumps(data_arr)

@app.route("/api/month-cases",methods=['get'])
def monthCases():
   today = date.today()

   today_date = today.isoformat()

   print("today date is "+today_date)
   responseData = Daily_report.objects(date=today_date).to_json()
   print(type(responseData))
   return responseData

def ss():
   print("cron job activate")

@app.route("/daily",methods=['POST'])
def dailyFunc():
   url = "https://raw.github.com/owid/covid-19-data/master/public/data/latest/owid-covid-latest.json"
   response = get(url)
   xJson = json.loads(response.text)
   JsonKey = [
      "location",
      "new_cases",
      "total_cases",
      "new_deaths",
      "total_deaths",
      "last_updateed_date"
   ]
   reList = []
   checked = False
   for key,value in xJson.items():
      print(key) 
      print(value["location"])
      if not checked:
         
         if Daily_report.objects(date=value["last_updated_date"]):           
            return "bobo"
         checked = True
      report = Daily_report(
         date = value["last_updated_date"],
         new_cases=value["new_cases"],
         total_cases=value["total_cases"],
         new_deaths=value["new_deaths"],
         total_deaths=value["total_deaths"],
         location= value["location"]
      )
      # print(type(report))
      report.save()
   return json.dumps(reList)


class Daily_report(db.Document):

   date = db.StringField()
   new_cases = db.IntField()
   total_cases = db.IntField()
   new_deaths = db.IntField()
   total_deaths = db.IntField()
   location = db.StringField()
   created_at = db.DateTimeField(default=datetime.now)

   def toJson(self):
      return {
         "date":self.date,
         "death":self.death,
         "deathNew":self.deathNew
      }


if __name__ == "__main__":
   app.run()
   CORS(app)
