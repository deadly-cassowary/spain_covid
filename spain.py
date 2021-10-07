import datetime as dt
import requests
from pandas_ods_reader import read_ods
import pandas as pd
import os
import glob
import csv
import matplotlib.pyplot as plt


# Params
START_DATE = "2021-05-01"
END_DATE = "2021-10-05"
DATE_FORMAT = "%Y-%m-%d"

I_WANT_TO_DOWNLOAD_RAW_VACCINE_FILES = True
I_WANT_TO_EXTRACT_TOTAL_VACCINES_RATE = True
I_WANT_TO_DOWNLOAD_RAW_CASES_FILE = True
I_WANT_TO_PLOT_VACCINES_VS_CASES_LINEAR = True

SPAIN_FOLDER = ""


# Constants
VACCINES_FILE_NAME = "Informe_Comunicacion_{0}.ods"
VACCINES_WEBSITE = "https://www.mscbs.gob.es/profesionales/saludPublica/ccayes/alertasActual/nCov/documentos/"
VACCINES_SHEET_NAME = "Etarios_con_pauta_completa"
VACCINES_ROW = "Total España"
VACCINES_COL = "% pauta completa sobre Población a Vacunar INE"

CASES_WEBSITE = "https://cnecovid.isciii.es/covid19/resources/"

OUTPUT_COL_DATE = "Date"
OUTPUT_COL_VACCINATED = "Vaccinated"
OUTPUT_VACCINATION_FILE = "vaccination_rate_by_date.csv"

CASES_FILE = "casos_diag_ccaadecl.csv"
CASES_COL_DATE = "fecha"
CASES_COL_CASES = "num_casos"


# Download vaccination files from from_date to to_date on daily basis
def download_vaccination_files(from_date, to_date):
    date_offset = dt.timedelta(days=1)
    while from_date <= to_date:
        try:
            file_name = VACCINES_FILE_NAME.format(from_date.strftime("%Y%m%d"))
            downloaded_obj = requests.get(VACCINES_WEBSITE+file_name, allow_redirects=True)
            with open(SPAIN_FOLDER+file_name, "wb") as file:
                file.write(downloaded_obj.content)
        except Exception as ex:
            print("Exception downloading vaccination file for %s: %s" % (from_date.strftime(DATE_FORMAT), str(ex)))
        from_date = from_date + date_offset


# Processes the vaccination files and generates a csv file with the total vaccination rate per day
def process_vaccionation_files():
    values = [[OUTPUT_COL_DATE, OUTPUT_COL_VACCINATED]]
    for filename in glob.glob(os.path.join(SPAIN_FOLDER, VACCINES_FILE_NAME.format('*'))):
        try:
            df = read_ods(filename, VACCINES_SHEET_NAME)
            # I know the below is crap but just wanted something fast
            file_date = filename.replace(SPAIN_FOLDER, "").replace("Informe_Comunicacion_", "").replace(".ods", "")
            total_vaccinated = df[VACCINES_COL].iloc[-1]
            values.append([file_date, total_vaccinated])
        except Exception as ex:
            continue
    try:
        with open(SPAIN_FOLDER+OUTPUT_VACCINATION_FILE, "w", newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(values)
    except IOError:
        print("I/O Error")


# Downloads cases file
def download_cases_file():
    try:
        downloaded_obj = requests.get(CASES_WEBSITE + CASES_FILE, allow_redirects=True)
        with open(SPAIN_FOLDER + CASES_FILE, "wb") as file:
            file.write(downloaded_obj.content)
    except Exception as ex:
        print("Exception downloading cases file: %s" % (str(ex)))


# Uses vaccination csv file and cases file to plot linear progression
def plot_vaccines_vs_cases_linear():
    fig, ax1 = plt.subplots()
    ax1.title.set_text('Spain Cases VS % Vaccination')

    # Vaccines
    df_vaccines = pd.read_csv(SPAIN_FOLDER + OUTPUT_VACCINATION_FILE)
    df_vaccines["DATE_TIME"] = pd.to_datetime(df_vaccines[OUTPUT_COL_DATE], format="%Y%m%d")
    df_vaccines.plot(x="DATE_TIME", y=OUTPUT_COL_VACCINATED, color='red', ax=ax1)

    # Cases (file was manually downloaded)
    ax2 = ax1.twinx()
    df_cases = pd.read_csv(SPAIN_FOLDER + CASES_FILE)
    df_cases["DATE_TIME"] = pd.to_datetime(df_cases[CASES_COL_DATE], format="%Y-%m-%d")
    filter_from_date = df_cases["DATE_TIME"] >= df_vaccines["DATE_TIME"][0]
    df_cases = df_cases[filter_from_date]
    df_cases.groupby(["DATE_TIME"]).sum()[CASES_COL_CASES].plot(ax=ax2, label="Cases")

    plt.legend(loc="upper left", bbox_to_anchor=(0, 0.9))
    plt.show()


if __name__ == "__main__":
    print("Hola")
    start_date = dt.datetime.strptime(START_DATE, DATE_FORMAT)
    end_date = dt.datetime.strptime(END_DATE, DATE_FORMAT)

    if I_WANT_TO_DOWNLOAD_RAW_VACCINE_FILES:
        download_vaccination_files(start_date, end_date)
        print("Vaccination raw files downloaded")

    if I_WANT_TO_EXTRACT_TOTAL_VACCINES_RATE:
        process_vaccionation_files()
        print("Vaccination raw files processed")

    if I_WANT_TO_DOWNLOAD_RAW_CASES_FILE:
        download_cases_file()
        print("Cases raw file downloaded")

    if I_WANT_TO_PLOT_VACCINES_VS_CASES_LINEAR:
        plot_vaccines_vs_cases_linear()

    print("Adios")
