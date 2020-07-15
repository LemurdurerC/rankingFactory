# coding: utf-8
from riotwatcher import LolWatcher, ApiError
import pandas as pd
import sys as sys
import math
import numpy as np
import psycopg2
from sqlalchemy import create_engine
from datetime import datetime
import time
import os
try:
    import configparser as cp
except ImportError:
    import ConfigParser as cp

start_time = time.time()




class Ranking:

    def __init__(self,api_key,region,classement,nomLog):
      self.api_key = api_key
      self.my_region = region
      self.classement = classement
      self.nomLog = nomLog
      self.path = "/home/pi/factory/"+self.classement+"/logs/log.txt"

    def getPseudo(self):
         connection = psycopg2.connect(user="pi",
                                      password="BLANK",
                                      host="192.168.1.36",
                                      port="5432",
                                      database=self.classement)
         cursor = connection.cursor()
         postgreSQL_select_Query = "select * from players"
         cursor.execute(postgreSQL_select_Query)
         result = cursor.fetchall()
         players = []
         for p in result:
             players.append(p[0])
         return players
         
    def traitement(self,var):
        try:
            watcher = LolWatcher(self.api_key)
            me = watcher.summoner.by_name(self.my_region, var)
            my_ranked_stats = watcher.league.by_summoner(self.my_region, me['id'])
            if not my_ranked_stats:
                raise Exception
            if (my_ranked_stats[0]["queueType"] == "RANKED_FLEX_SR"):
                kromy = 1
            else:
                kromy = 0
            pseudo = my_ranked_stats[kromy]["summonerName"]
            win =my_ranked_stats[kromy]["wins"]
            loose =my_ranked_stats[kromy]["losses"]
            division =my_ranked_stats[kromy]["tier"]
            palier = my_ranked_stats[kromy]["rank"]
            if division == "IRON":
                valueRef = 8
            elif division == "BRONZE":
                valueRef = 7
            elif division == "SILVER":
                valueRef = 6
            elif division == "GOLD":
                valueRef = 5
            elif division == "PLATINUM":
                valueRef = 4
            elif division == "DIAMOND":
                valueRef = 3
            elif division == "MASTER":
                valueRef = 2
            elif division == "GRAND MASTER":
                valueRef = 1
            elif division == "CHALLENGER":
                valueRef = 0
            lp=my_ranked_stats[kromy]["leaguePoints"]
            winrate=round(win/(win+loose)*100)
            df = pd.DataFrame({'pseudo' : [pseudo], 'win' : [win], 'loose' : [loose],'division' : [division],'palier':[palier],'winrate' :[winrate],'valueRef':[valueRef],'lp':[lp]})
            file = open(self.path, "a", encoding='utf-8')
            date = datetime.now()
            file.write(str(date)+ " OK FOR " +var.rstrip() + "\n")
            file.close()
            return df;
        except ApiError as err:
                date = datetime.now()
                if err.response.status_code == 429:
                    file = open(self.path, "a", encoding='utf-8')
                    file.write(str(date) + " ERROR 429 WITH " +var.rstrip() + "\n")
                    file.close()
                elif err.response.status_code == 404:
                    date = datetime.now()
                    print('Summoner with that ridiculous name not found.')
                    file = open(self.path, "a", encoding='utf-8')
                    file.write(str(date)+" ERROR 404 WITH " +var.rstrip() + "\n")
                    file.close()
        except Exception as e:
                date = datetime.now()
                print(e)
                file = open(self.path, "a", encoding='utf-8')
                file.write(str(date)+" ERROR : EXCEPTION E" + var.rstrip() + "\n")
                file.close()
      
        
    """def cleanErrors(self):
        pseudoToDelete=[]
        try:
            with open("/home/pi/Desktop/apilol/python/logs/"+self.classement+"/log.txt", "r", encoding='utf-8') as f:
                for line in f.readlines():
                    self.pseudoToDelete.append(line.rstrip())
                os.remove("log.txt")
                rows_deleted = 0
        except Exception as err:
                return
        for p in pseudoToDelete:
            try:
                 self.logTrace(False,p,0)
                 connection = self.getCon()
                 cur = connection.cursor()
                 sql_delete_query = '''DELETE FROM players where pseudo = %s'''
                 cur.execute(sql_delete_query, (p.rstrip(), ))
                 rows_deleted = cur.rowcount
                 connection.commit()
                 cur.close()
              
            except (Exception, psycopg2.DatabaseError) as error:
                 print(error)
        print(rows_deleted) 
        """
    def getCon():
        connection = psycopg2.connect(user="pi",
                                      password="BLANK",
                                      host="192.168.1.36",
                                      port="5432",
                                      database=self.classement)
        return connection
            
    
          
    def launch(self):
        watcher = LolWatcher(self.api_key)
        df=0
        columns_names="pseudo","win","loose","division","palier","winrate","valueRef","lp"
        dfall= pd.DataFrame(columns=columns_names)
        players = self.getPseudo()
        for p in players:
             
             print("Searching for " + str(p) + "....")
             df = self.traitement(p.rstrip())
             dfall = dfall.append(df)
             time.sleep(2)
       
        engine = create_engine("postgresql://pi:BLANK@192.168.1.36:5432/"+self.classement)
        result = dfall.to_sql(self.classement, engine, schema = 'public', if_exists ='replace',index=True)
        #self.cleanErrors()
        print('Programme rÃ©ussi')                   
        print("Temps d execution : %s secondes ---" % (time.time() - start_time))            
          
if __name__ == "__main__":  
    for arg in sys.argv:
        classement = arg
    today = datetime.today()
    nomLog = today.strftime("%b-%d-%Y")         
    ranking = Ranking('RGAPI-3e9199b4-36a9-479d-8560-0081f5e9bd19','euw1',classement,nomLog)
    ranking.launch()  
    
    





