from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QMessageBox

from PySide6.QtCore import Slot

from PySide6.QtGui import QBrush, QColor

from datetime import datetime, timedelta

import os

import sys

import requests

import pandas as pd

import subprocess

 

class CSVLoaderApp(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("Lagerbestand")

        self.csv_url = "https://exhaust.pl/produts_stock/export.csv"

        self.last_downloaded_file = None  # Hält den Pfad der zuletzt heruntergeladenen Datei

        self.resize(1024, 768)  # Fenstergröße initial auf 1280x1024 Pixel setzen

 

        mainWidget = QWidget()

        self.setCentralWidget(mainWidget)

        layout = QVBoxLayout()

 

        # Button zum Herunterladen der CSV-Datei

        self.downloadButton = QPushButton("CSV herunterladen")

        self.downloadButton.clicked.connect(self.download_and_save_csv)

        layout.addWidget(self.downloadButton)

 

        # Button zum Laden und Anzeigen der Daten aus der CSV-Datei

        self.loadButton = QPushButton("Daten anzeigen")

        self.loadButton.clicked.connect(self.display_csv_data)

        layout.addWidget(self.loadButton)

 

        # Button zum Anzeigen des Ordners

        self.appDirectoryButton = QPushButton("Ordner anzeigen")

        self.appDirectoryButton.clicked.connect(self.openAppDirectory)

        layout.addWidget(self.appDirectoryButton)

 

        # QTableWidget-Konfiguration

        self.tableWidget = QTableWidget()

        layout.addWidget(self.tableWidget)

        mainWidget.setLayout(layout)

   

    def openAppDirectory(self):

        appDirectory = self.getAppDirectory();

        print("APP DIRECTORY IS. " + appDirectory);

        subprocess.run(["open",appDirectory])

 

    def getAppDirectory(self):

        appName = 'lagerbestand'

        user_home = os.path.expanduser('~')

        appDirectory = os.path.join(user_home,'Library','Application Support',appName)

        if not os.path.exists(appDirectory):

            os.makedirs(appDirectory)

        print("APP DIRECTORY IS. "+ appDirectory);

        return appDirectory

 

    def find_last_two_csv_files(self):

        # Liste alle CSV-Dateien im aktuellen Verzeichnis auf

        csv_files = [f for f in os.listdir(self.getAppDirectory()) if f.endswith('.csv')]

        # Sortiere die Dateien basierend auf dem Datum im Dateinamen

        csv_files.sort(key=lambda date: datetime.strptime(date, "%d-%m-%Y.csv"), reverse=True)

        # Gib die letzten beiden Dateien zurück, falls verfügbar

        return csv_files[:2] if len(csv_files) >= 2 else csv_files

 

    def download_and_save_csv(self):

        try:

            response = requests.get(self.csv_url)

            response.raise_for_status()

            current_date = datetime.now().strftime("%d-%m-%Y")

            app_directory = self.getAppDirectory()

            filename = f"{current_date}.csv"

            filepath = os.path.join(app_directory,filename)

            print("Datei gespeichert unter:"+filepath)

            with open(filepath, 'w', encoding='utf-8') as file:

                file.write(response.text)

            self.last_downloaded_file = filepath  # Speichere den Pfad der heruntergeladenen Datei

            QMessageBox.information(self, "Information", "CSV-Datei erfolgreich heruntergeladen.")

            return filepath

        except requests.RequestException as e:

            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der CSV-Datei: {e}")

            return None

 

    def generate_filenames_for_last_two_days(self):

        today = datetime.now()

        one_day_delta = timedelta(days=1)

        # Dateinamen für heute und gestern

        filename_today = (today).strftime("%d-%m-%Y") + ".csv"

        filename_yesterday = (today - one_day_delta).strftime("%d-%m-%Y") + ".csv"

        return filename_today, filename_yesterday

 

    def display_csv_data(self):

        last_two_files = self.find_last_two_csv_files()

 

        if len(last_two_files) < 2:

            QMessageBox.warning(self, "Warnung", "Nicht genügend CSV-Dateien gefunden.")

            return

 

        # Entferne die Dateiendung '.csv' für die Anzeige in den Spaltenbeschriftungen

        label_today = last_two_files[0].replace(".csv", "")

        label_yesterday = last_two_files[1].replace(".csv", "")

 

        # Lese die letzten beiden CSV-Dateien ein

        filepathOne = os.path.join(self.getAppDirectory(),last_two_files[0])

        filepathTwo = os.path.join(self.getAppDirectory(),last_two_files[1])

        df_today = pd.read_csv(filepathOne, sep=',')

        df_yesterday = pd.read_csv(filepathTwo, sep=',')

       

        # Entferne Duplikate in der SKU-Spalte

        df_today.drop_duplicates(subset=['SKU'], inplace=True)

        df_yesterday.drop_duplicates(subset=['SKU'], inplace=True)

 

        # Setze 'SKU' als Index

        #df_today.set_index('SKU', inplace=True)

        #df_yesterday.set_index('SKU', inplace=True)

 

        # Merge die DataFrames basierend auf 'SKU'

        merged_df = pd.merge(df_today[['SKU','Avaliable', 'Stock']], df_yesterday[['SKU','Avaliable', 'Stock']], left_index=True, right_index=True, suffixes=(f' ({label_today})', f' ({label_yesterday})'))

 

        # Berechne die Differenz der 'Stock'-Werte

        merged_df['Stock-Differenz'] = merged_df[f'Stock ({label_today})'] - merged_df[f'Stock ({label_yesterday})']

 

        # Setze die Tabelle auf

        self.tableWidget.clear()

        self.tableWidget.setRowCount(len(merged_df.index))

        self.tableWidget.setColumnCount(len(merged_df.columns))

        columnWidth=130;

        self.tableWidget.setColumnWidth(0, columnWidth)

        self.tableWidget.setColumnWidth(1, columnWidth)

        self.tableWidget.setColumnWidth(2, columnWidth)

        self.tableWidget.setColumnWidth(3, columnWidth)

        self.tableWidget.setColumnWidth(4, columnWidth)

        self.tableWidget.setColumnWidth(5, columnWidth)

        self.tableWidget.setColumnWidth(6, columnWidth)

        self.tableWidget.setColumnWidth(7, columnWidth)

        # Aktualisiere die Spaltenbeschriftungen mit den dynamisch generierten Labels

        headers = [f'{col}' for col in merged_df.columns]

        self.tableWidget.setHorizontalHeaderLabels(headers)

 

        # Fülle die Tabelle

        for row, (index, row_data) in enumerate(merged_df.iterrows()):

            self.tableWidget.setItem(row, 0, QTableWidgetItem(index))  # SKU

            for col, data in enumerate(row_data):

                self.tableWidget.setItem(row, col, QTableWidgetItem(str(data)))

       

        # Annahme, dass Sie die Tabelle hier bereits gefüllt haben

        stock_diff_column_index = self.tableWidget.columnCount() - 1  # Angenommen, Stock-Differenz ist die letzte Spalte

 

        for row in range(self.tableWidget.rowCount()):

            item = self.tableWidget.item(row, stock_diff_column_index)

            if item:  # Überprüfen Sie, ob das Item existiert

                stock_diff_value = float(item.text())  # Konvertieren Sie den Wert in float

                color = None

                if stock_diff_value < 0:

                    color = QBrush(QColor(255, 0, 0))  # Rot

                elif stock_diff_value > 0:

                    color = QBrush(QColor(0, 255, 0))  # Grün

               

                if color:

                    for col in range(self.tableWidget.columnCount()):

                        self.tableWidget.item(row, col).setBackground(color)

            else:

                # Dieser Block wird ausgeführt, wenn kein QTableWidgetItem für die Zelle existiert.

                # Sie können hier ein neues Item erstellen oder eine Warnung ausgeben.

                print(f"Warnung: Kein Item in Zeile {row}, Spalte {stock_diff_column_index} gefunden.")

 

if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = CSVLoaderApp()

    window.show()

    window.display_csv_data()

    sys.exit(app.exec())

 