# -*- coding: utf-8 -*-
from dateBLANK import dateBLANK
import os
import sys as sys
import math
import numpy as np
import psycopg2
from sqlalchemy import create_engine
from dateBLANK import dateBLANK
import BLANK
import os
import pandas as pd
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import shutil
import platform


def clear():
  os.system('clear')


def getCon(database_name="postgres"):
    conn = psycopg2.connect(user="pi",
    password="159159",
    host="192.168.1.36",
    port="5432",
    database=database_name
    )
    return conn;


def getRankings():
    conn = getCon()
    cursor = conn.cursor()
    cursor.execute("SELECT datname from pg_database where datistemplate=false;")
    ranking_names = []
    for i in cursor.fetchall():
        i = str(i)
        ranking_names.append(i.split("'")[1])
    return ranking_names


def addPlayers(classement):
    conn = getCon(classement)
    cursor = conn.cursor()
    conn.autocommit = True
    print(
    "Veuillez mettre la liste des joueurs dans un fichier texte dans le repertoire joueurs de votre classement et inserer le nom du fichier texte")
    nomFichier = input()
    try:
        with open(classement + "/joueurs/" + nomFichier + ".txt", "r", encoding='utf-8') as f:
            for line in f.readlines():
                sqlInsertRow2 = "INSERT INTO players values('" + line.rstrip() + "')";
                cursor.execute(sqlInsertRow2)
    except Exception as e:
        print("Erreur ajout des joueurs")
        return 

def addCron(classement):
    print("Lancement quotidien, veuillez taper l'horaire de lancement sous ce format HH:MM exemple 19:10")
    str = input()
    heure = str.split(":")[0]
    minute = str.split(":")[1]
    with open('/var/spool/cron/crontabs/pi', 'a')as f:
        f.write("\n" + minute + " " + heure + " * * * python3 Desktop/apilol/k.py " + classement);
    f.close();
    print("Lancement planifie")


def getRankingList(classement):
    conn = getCon(classement)
    cursor = conn.cursor()
    clear()
    try:
        cursor.execute("SELECT * from " + classement + ";")
        columns_names = "index", "pseudo", "win", "loose", "division", "palier", "winrate", "valueRef", "lp"
        list = []

        for i in cursor.fetchall():
            list.append(i)
        df = pd.DataFrame(data=list, columns=columns_names)
        if df.empty == True:
            print("Ce classement est vide")
            return
        print(df)
        print("Pour consulter en version web allez sur kodaline/fun/" + classement)

    except Exception as e:
        print("Classement vide")

        return



def getLastLog(classement):
    # Regarder dans les répertoires logs du classement correspondant
    # Parcourir toutes les logs et prendre les noms pour les mettres dans des dataframe, trier les dataframe en fonction des date d'entrées puis ressorir la date la plus ancienne
    try:
        mon_fichier = open(classement + "/logs.txt", "r")
        contenu = mon_fichier.read()
        print(contenu)
    except Exception as e:
        print("Logs inexistante")
        return 
        
        
def deleteDatabase(classement):
    conn = getCon()
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    try:
        cur.execute(sql.SQL("DROP DATABASE {}").format(
        sql.Identifier(classement))
        )
        print("BDD supprime")
    except Exception as e:
        print(e)
        print("Erreur de la suppression de " + classement)
        return 0
    conn.close()
    return 0


def deleteDirectory(classement):
    path = r"./"+classement
    path2 = r"/home/pi/www/"+classement
    
    try: 
        shutil.rmtree(path)
    except OSError as e:
        print(e)
    else:
        print("Repertoire logs et players du classement " +classement+" supprime")
    try:    
        shutil.rmtree(path2)
    except OSError as e:
        print(e)
    else:
        print("Repertoire sur le ftp " +classement+" supprime")
        
def deleteRanking(classement):
    deleteDatabase(classement)
    deleteDirectory(classement)


def createRanking():
    print("Veuillez saisir le nom du classement que vous voulez creer")
    classement = input()
    classement = classement.lower()
    if classement in getRankings():
        print("Ce classement existe deja")
        return
    else:
        createDatabase(classement)
        createTables(classement)
        createInterface(classement)





def createInterface(classement):
    try:
        os.makedirs("/home/pi/www/" + classement)
        os.makedirs(classement + "/logs")
        os.makedirs(classement + "/joueurs")
    except OSError:
        print("Erreur creation des repertoires pour le classement " + classement)
        return 0
    filePath = shutil.copy('/home/pi/www/template/index.php', '/home/pi/www/' + classement)
    fichier = open("/home/pi/www/" + classement + "/config.php", "a")
    fichier.write("<?php\n$nomClassement='" + classement + "';")
    fichier.close()
    filePath = shutil.copy('/home/pi/www/template/model.php', '/home/pi/www/' + classement)
    filePath = shutil.copy('/home/pi/www/template/demande.php', '/home/pi/www/' + classement)


def createDatabase(classement):
    conn = getCon()
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    try:
        cur.execute(sql.SQL("CREATE DATABASE {}").format(
        sql.Identifier(classement))
        )
    except Exception as e:
        print("Erreur creation de la database" + classement)
        return 0



def createTables(classement):
    classement = classement
    try:
        conn = psycopg2.connect(user="pi",
        password="159159",
        host="192.168.1.36",
        port="5432",
        database=classement)
        cur = conn.cursor()
        conn.autocommit = True
        sql = '''CREATE TABLE ''' + classement + '''(
        pseudo text
        )'''
        sql1 = '''CREATE TABLE joueursAttente(
        pseudo text
        )'''
        sql2 = '''CREATE TABLE players(
        pseudo text
        )'''
        cur.execute(sql)
        cur.execute(sql1)
        cur.execute(sql2)
        conn.close()
    except Exception as e:
        print('Erreur sur creation des tables sur ' + classement)
        print(e)
        return 0





def modifyRanking():
    menu_ranking = {"1": addPlayers, "2": addCron, "3": getRankingList, "4": getLastLog, "5": deleteRanking,
    "6": lambda: True}
    leave = False
    while (leave == False):
        ranking_names = getRankings()
        print("Voici la liste des classements existants, veuillez taper le classement que vous voulez traiter")
        print(ranking_names)
        classement = input()
        if classement in ranking_names:
            print("Veuillez choisir l'action a faire avec le classement : " + classement)
            print("1 - Ajouter des joueurs a ce classement")
            print("2 - Ajouter une planification pour la maj de ce classement")
            print("3 - Visualiser le classement")
            print("4 - Visualiser les dernieres logs de ce classement")
            print("5 - Delete database")
            print("6 - Revenir au menu principal")
            choix = input()
            clear()
            if choix in menu_ranking:
                if choix == "6":
                        leave = menu_ranking[choix]()
                else:
                        leave = menu_ranking[choix](classement)
            else:
                print("Veuillez choisir une option valable")





if __name__ == '__main__':

    menu_dic = {"1": modifyRanking, "2": createRanking, "3": lambda: True}

    leave = False
    while (leave == False):
        print("Ranking Generator, veuillez choisir une option")
        print("1 - Acceder a un classement")
        print("2 - Creer un classement")
        print("3 - Quitter")
        print("\n")
        choix = input()
        clear()
        if choix in menu_dic:
            if choix == "3":
                leave = menu_dic[choix]()
            else:
                menu_dic[choix]()
        else:
            print("Veuillez choisir une option valable")

