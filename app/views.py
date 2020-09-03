from app import app
from flask import render_template, request, redirect, jsonify
import joblib
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
import json
import time
import requests
import math
import re

def get_data(license_plate, mileage):
    """Takes license plate number and mileage as input and returns car technical data"""
        return(car_data)


def price_predictor(maker, model, year, sub_type, mileage, engine_size, transmission, drivetrain, fuel, power):
    """Takes car technical data as input and returns the predicted price of the car"""
    rf_path = Path(__file__).parent / "rfr64bit.sav"
    odt_path = Path(__file__).parent / "carsDf.csv"
    rf = joblib.load(rf_path)
    odt = pd.read_csv(odt_path)

    #If electric car uses engine avg size 2.0 so it won't affect to the price. 
    if not engine_size:
        engine_size = 2.0

    odt.loc[:, 'Year'] = year
    odt.loc[:, 'Power'] = int(power)/1.36
    odt.loc[:, 'Mileage'] = int(mileage)*1000
    odt.loc[:, 'Engine Size'] = engine_size
    odt.loc[:, 'Sub type_'+ str(sub_type).lower().strip()] = 1

    if model == "":
        pass
    else:
        odt.loc[:, 'Model_' + str(model).lower().strip()] = 1

    odt.loc[:, 'Transmission_' + str(transmission).lower().strip()] = 1
    odt.loc[:, 'Manufacturer_' + str(maker).lower().strip()] = 1
    odt.loc[:, 'Drivetrain_' + str(drivetrain).lower().strip()] = 1
    odt.loc[:, 'Fuel type_' + str(fuel).lower().strip()] = 1
    odt.loc[:, 'Seller_private seller'] = 1

    price = int((rf.predict(odt)))
    price = int(math.ceil(price / 100.0)) * 100

    #Accurate prediction range is from 1000 - 70000. Leave cars outside that value range out. 
    if price > 70000:
        teksti = ("Autonne arvo on yli 70 000 euroa")
    elif price < 1000:
        teksti = ("Autonne arvo on alle 1000 euroa")
    else:
        teksti = ("Autonne arvo on " + str(price) + " euroa")
    return teksti

@app.route("/")
def index():
    return render_template("public/licenseplate.html")

@app.route("/tietoa")
def about():
    return render_template("public/about.html")

@app.route("/hintalaskuri", methods=["GET", "POST"])
def analysator():
    if request.method == "POST":
        maker = request.form['maker']
        model = request.form['model']
        year = request.form['year']
        sub_type = request.form['sub_type']
        mileage = request.form['mileage']
        engine_size = request.form['engine_size']
        transmission = request.form['transmission']
        drivetrain = request.form['drivetrain']
        fuel = request.form['fuel']
        power = request.form['power']

        try:
            teksti = price_predictor(maker, model, year, sub_type, mileage, engine_size, transmission, drivetrain, fuel, power)
            return jsonify({'teksti' : teksti})
        except:
            teksti = ("Hintaa ei voitu arvioida")
            return jsonify({'teksti' : teksti})

    return render_template("public/analysator.html")


@app.route("/rekisterinumerohaku", methods=["GET", "POST"])
def licenseplate():
    if request.method == "POST":
        rekisterikilpi = request.form['licenseplate']
        mileage = request.form['mileage']

        try:
            car_data = get_data(rekisterikilpi, mileage)

            if car_data == False:
                return jsonify(
                {
                'teksti' : "",
                'maker' : "False"
                })

            else:
                try:
                    teksti = price_predictor(car_data["maker"], car_data["model"], car_data["year"], car_data["sub_type"], car_data["mileage"], car_data["engine_size"], car_data["transmission"], car_data["drivetrain"], car_data["fuel"], car_data["power"])
                except:
                    teksti = ""

                if car_data["fuel"] == "Sähkö":
                    car_data["engine_size"] = "-"

                return jsonify(
                    {'maker' : car_data["maker"],
                    'model' : car_data["model"],
                    'mileage' : mileage,
                    'year' : car_data["year"],
                    'sub_type' : car_data["sub_type"].lower().capitalize(),
                    'engine_size' : car_data["engine_size"],
                    'transmission' : car_data["transmission"],
                    'drivetrain' : car_data["drivetrain"],
                    'fuel' : car_data["fuel"],
                    'power' : car_data["power"],
                    'teksti' : teksti
                    })
        except:
            return jsonify(teksti = "Ei voitu määrittää arvoa. Voit syöttää tiedot käsin hintalaskurilla.")
    return render_template("public/licenseplate.html")
