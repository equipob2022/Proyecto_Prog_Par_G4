from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from bs4 import BeautifulSoup

from selenium.webdriver.firefox.service import Service as FireFoxService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService

from webdriver_manager.microsoft import EdgeChromiumDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.firefox.options import Options as FireFoxOption
from selenium.webdriver.chrome.options import Options as ChromeOption
from selenium.webdriver.edge.options import Options as EdgeOption

import time
import json
import threading as th

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/trabajos", methods=["POST"])
def searchJob():
    lock = th.Lock()

    # Remplazo de tildes y ñ
    trans = str.maketrans("áéíóúüñ", "aeiouun")
    jobName = request.form["nombreTrabajo"].translate(trans).lower().replace(" ", "-")
    placeName = request.form["nombreUbicacion"].lower().replace(" ", "-")

    lista_empleos = []

    options = FireFoxOption()
    options.headless = True

    def Bumeran():
        _browser = webdriver.Firefox(
            service=FireFoxService(GeckoDriverManager().install()),
            options=options,
        )

        # URLs
        url = "https://www.bumeran.com.pe"

        if placeName == "todo-el-país":
            key = f"/empleos-busqueda-{jobName}.html"
        elif placeName == "cusco":
            key = f"/en-cuzco/empleos-busqueda-{jobName}.html"
        else:
            key = f"/en-{placeName}/empleos-busqueda-{jobName}.html"

        urlBusqueda = url + key

        # Ingreso a la pagina
        _browser.get(urlBusqueda)

        time.sleep(0.5)

        # Página
        page = BeautifulSoup(_browser.page_source, "html.parser")

        # Empleos
        jobs = page.find_all("div", {"class": "sc-fYAFcb"})

        # Guardar Empleos
        for job in jobs:
            link = url + job.find("a").get("href")
            cargo = job.find("h2").text
            empresa = job.find_all("h3")[0].text
            fecha_publicacion = job.find_all("h3")[2].text
            lugar = job.find_all("h3")[3].text
            modo = job.find_all("h3")[4].text

            lock.acquire()
            lista_empleos.append(
                {
                    "pagina": "Bumeran",
                    "enlace": link,
                    "cargo": cargo,
                    "empresa": empresa,
                    "publicacion": fecha_publicacion,
                    "ubicacion": lugar,
                    "modo": modo,
                }
            )
            lock.release()

        _browser.close()

    def CompuTrabajo():
        _browser = webdriver.Firefox(
            service=FireFoxService(GeckoDriverManager().install()),
            options=options,
        )

        # URLs
        url = "https://pe.computrabajo.com"

        if placeName == "todo-el-país":
            key = f"/trabajo-de-{jobName}"
        else:
            key = f"/trabajo-de-{jobName}-en-{placeName}"

        urlBusqueda = url + key

        # Ingreso a la pagina
        _browser.get(urlBusqueda)

        # Página
        page = BeautifulSoup(_browser.page_source, "html.parser")

        # Empleos
        jobs = page.find_all("article", {"class": "box_offer"})

        # Guardar Empleos
        for job in jobs:
            v = True
            link = url + job.find("a", {"class": "js-o-link fc_base"}).get("href")
            cargo = job.find("a", {"class": "js-o-link fc_base"}).text.strip()
            try:
                empresa = job.find(
                    "a", {"class": "fc_base hover it-blank"}
                ).text.strip()
            except:
                empresa = job.find("p", {"class": "fs16 fc_base mt5 mb5"}).text.strip()
                empresa = empresa[: empresa.find("\n")]

                if placeName != "Todo-el-país":
                    lugar = placeName.replace("-", " ")
                    lugar = lugar.capitalize()
                else:
                    lugar = "Sin Información"

                v = False
            if v:
                try:
                    lugar = (
                        job.find("p", {"class": "fs16 fc_base mt5 mb5"})
                        .contents[-1]
                        .text.strip()
                    )
                except:
                    lugar = "Sin Información"
            fecha_publicacion = job.find("p", {"class": "fs13 fc_aux"}).text.strip()

            lock.acquire()
            lista_empleos.append(
                {
                    "pagina": "CompuTrabajo",
                    "enlace": link,
                    "cargo": cargo,
                    "empresa": empresa,
                    "publicacion": fecha_publicacion,
                    "ubicacion": lugar,
                }
            )
            lock.release()

        _browser.close()

    hilo1 = th.Thread(target=CompuTrabajo)
    hilo2 = th.Thread(target=Bumeran)

    hilo1.start()
    hilo2.start()

    hilo1.join()
    hilo2.join()

    # return jsonify(lista_empleos)
    return render_template("trabajos.html", lista_empleos=lista_empleos)

    # buscar = Main(request.form["nombreTrabajo"])

    # hilo1 = th.Thread(target=buscar.computrabajo)
    # hilo2 = th.Thread(target=buscar.bumeran)

    # hilo1.start()
    # hilo2.start()

    # hilo1.join()
    # hilo2.join()

    # with open("data/data.json", "r", encoding="utf8") as file:
    #     file_data = json.load(file)

    # return jsonify(file_data)
    # # return render_template("trabajos.html",file_data)


@app.route("/trabajos", methods=["GET"])
def getJob():
    return render_template("trabajos.html")


if __name__ == "__main__":
    app.run(debug=True)
