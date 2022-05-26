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




# @app.route("/30-day",methods=['POST'])
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
      jbl = []
      for j in json.loads(qData):
         jb = {
            "date":j.get("date"),
            "newCase":j.get("new_cases",0),
            "totalCase":j.get("total_cases",0),
            "newDeath":j.get("new_deaths",0),
            "death":j.get("total_deaths",0),
            "location":j.get("location")
         }
         
         jbl.append(jb)
      reData ={"date":today_date,"result":jbl}
      curr_date = curr_date-timedelta(days=1)  
      if reData.get("result"): 
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

# @app.route("/daily",methods=['POST'])
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

req_enum = ["new-cases","total-cases","new-deaths","total-deaths"]
cluster_name = ["new_case_cluster","total_case_cluster","new_death_cluster","total_death_cluster"]
s_c = ["new_cases","total_cases","new_deaths","total_deaths"]
order_con = ["asc","desc"]

continent = ["World","High income","Europe","Asia","European Union","Upper middle income","North America","Lower middle income","Low income",]
@app.route("/api/cases",methods=['get'])
def Cases2():
   args = request.args
   
   today = date.today()
   yesterday = today-timedelta(days=1) 
   qdate = args.get("date", default=yesterday.isoformat(), type=str)
   order = args.get("order",default="location", type=str)
   by_string = args.get("by",default="desc", type=str)
   curr_date = yesterday
   date_arr = []
   exc_field = ["id","created_at"]
   data_arr = []
   continent = ["World","High income","Europe","Asia","European Union","Upper middle income","North America","Lower middle income","Low income",]
   by = "-"
   if order not in req_enum :
      if order != "location":
         return "order name wrong. try new-cases, total-cases, new-deaths, total-deaths"

   if by_string in order_con:
      if by_string == "asc": 
         by=""
   else:
      return "by wrong. please choose between asc||desc"
   
   if order != "location":
      idx = req_enum.index(order)    
      qData = Daily_report.objects(date=qdate).exclude(*exc_field).order_by(by+s_c[idx]).to_json()

   else:
      qData = Daily_report.objects(date=qdate).exclude(*exc_field).order_by("location").to_json()
   jbl = []
   for j in json.loads(qData):
      if j.get("location") in continent:
         continue
      jb = {
         "date":j.get("date"),
         "newCase":j.get("new_cases",0),
         "totalCase":j.get("total_cases",0),
         "newDeath":j.get("new_deaths",0),
         "death":j.get("total_deaths",0),
         "location":j.get("location")
      }
      jbl.append(jb)
   
   reData ={"date":qdate,"result":jbl}  
   if reData.get("result"): 
      data_arr.append(reData)

   return json.dumps(data_arr)

@app.route("/api/sum-of-cases-range",methods=['get'])
def sumnOfCases():
   args = request.args
   
   today = date.today()
   yesterday = today-timedelta(days=1) 
   f_date = args.get("from", default=(yesterday-timedelta(days=7)).isoformat(), type=str)
   t_date = args.get("to", default=yesterday.isoformat(), type=str)
   arr = []
 
   # locations = Daily_report.objects(date=yesterday.isoformat()).only("location").exclude("id").order_by("location").to_json()
   from_data =json.loads(Daily_report.objects(date=f_date).exclude("id").order_by("location").to_json()) 
   to_data =json.loads(Daily_report.objects(date=t_date).exclude("id").order_by("location").to_json())

   for f in from_data:
      for t in to_data:     
         if t.get("location") in continent:
            continue
         if f["location"]==t["location"]:
            to_date = t.get("total_cases",0)
            from_date = f.get("total_cases",0)
            obj = {"location":f["location"],"sum-case":to_date-from_date}
            arr.append(obj)
            break

   return json.dumps(arr)

@app.route("/api/sum-of-cases",methods=['get'])
def sumnOfCases2():
   args = request.args
   
   today = date.today()
   yesterday = today-timedelta(days=1) 
   r_date = args.get("range", default=7, type=int)
   start_date = args.get("date",default=yesterday.isoformat(),type=str)
   # t_date = args.get("to", default=yesterday.isoformat(), type=str)
   curr_date = date.fromisoformat(start_date) 
   arr = []
   
   # print(f_date)
   # print(t_date)  
   for i in range(r_date):
      locations_list = json.loads(Daily_report.objects(date=curr_date.isoformat()).only("location","new_cases").exclude("id").order_by("location").to_json())
      
      sum_of_cases = 0

      if locations_list:
         sum_of_cases = sum(i.get("new_cases",0) for i in locations_list)

      obj = {"date":curr_date.isoformat(),"sum_of_cases":sum_of_cases}  
      arr.append(obj)
      curr_date = curr_date-timedelta(days = 1)


   return json.dumps(arr)

@app.route("/api/sum-of-deaths",methods=['get'])
def sumnOfDeath():
   args = request.args
   
   today = date.today()
   yesterday = today-timedelta(days=1) 
   r_date = args.get("range", default=7, type=int)
   start_date = args.get("date",default=yesterday.isoformat(),type=str)
   # t_date = args.get("to", default=yesterday.isoformat(), type=str)
   curr_date = date.fromisoformat(start_date) 
   arr = []
   
   # print(f_date)
   # print(t_date)  
   for i in range(r_date):
      locations_list = json.loads(Daily_report.objects(date=curr_date.isoformat()).only("location","new_deaths").exclude("id").order_by("location").to_json())
      
      sum_of_deaths = 0

      if locations_list:
         sum_of_deaths = sum(i.get("new_deaths",0) for i in locations_list)

      obj = {"date":curr_date.isoformat(),"sum_of_death":sum_of_deaths}  
      arr.append(obj)
      curr_date = curr_date-timedelta(days = 1)


   return json.dumps(arr)

@app.route("/api/sum-of",methods=['get'])
def sumnOf():
   args = request.args
   
   today = date.today()
   yesterday = today-timedelta(days=1) 
   r_date = args.get("range", default=7, type=int)
   start_date = args.get("date",default=yesterday.isoformat(),type=str)
   # t_date = args.get("to", default=yesterday.isoformat(), type=str)
   curr_date = date.fromisoformat(start_date) 
   arr = []
   
   # print(f_date)
   # print(t_date)  
   for i in range(r_date):
      locations_list = json.loads(Daily_report.objects(date=curr_date.isoformat(),location="World").only("location","new_deaths","new_cases","total_deaths","total_cases").exclude("id").to_json())
      
      new_deaths = 0
      new_cases = 0
      total_death = 0
      total_cases = 0

      

      if locations_list:
         new_deaths = locations_list[0]["new_deaths"]
         new_cases = locations_list[0]["new_cases"]
         total_death = locations_list[0]["total_deaths"]
         total_cases = locations_list[0]["total_cases"]

      obj = {"date":curr_date.isoformat(),
         "new_deaths":new_deaths,
         "new_cases":new_cases,
         "total_deaths":total_death,
         "total_cases":total_cases
      }  
      arr.append(obj)
      curr_date = curr_date-timedelta(days = 1)


   return json.dumps(arr)

@app.route("/api/daily-data",methods=['get'])
def daily_data():
   args = request.args
   
   today = date.today()
   yesterday = today-timedelta(days=1) 
   r_date = args.get("date", default=yesterday.isoformat(), type=str)
   # t_date = args.get("to", default=yesterday.isoformat(), type=str)
   arr = []
   
   # print(f_date)
   # print(t_date)  

   locations_list = json.loads(Daily_report.objects(date=r_date,location="World").only("location","new_deaths","new_cases","total_deaths","total_cases").exclude("id").order_by("location").to_json())
   
   new_deaths = 0
   new_cases = 0
   total_death = 0
   total_cases = 0

   if locations_list:
      new_deaths = locations_list[0]["new_deaths"]
      new_cases = locations_list[0]["new_cases"]
      total_death = locations_list[0]["total_deaths"]
      total_cases = locations_list[0]["total_cases"]

   obj = {"date":r_date,
   "new_deaths":new_deaths,
   "new_cases":new_cases,
   "total_deaths":total_death,
   "total_cases":total_cases
   }  
   return json.dumps(obj)


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
