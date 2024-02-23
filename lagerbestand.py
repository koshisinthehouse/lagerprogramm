from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QMessageBox, QHBoxLayout, QLabel, QLineEdit

from PySide6.QtCore import Slot

from PySide6.QtGui import QBrush, QColor

from datetime import datetime, timedelta

import os

import sys
from numpy import int64

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
        self.ensure_stock_data_file_exists()
 
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

        # Erstelle ein neues QHBoxLayout für die Elemente in einer Zeile
        inputRowLayout = QHBoxLayout()

        # Label für "SKU"
        skuLabel = QLabel("SKU")
        inputRowLayout.addWidget(skuLabel)

        # Textfeld für SKU
        self.skuTextField = QLineEdit()
        self.skuTextField.setObjectName("skuTextField")  # Namensgebung für das Textfeld, falls benötigt
        inputRowLayout.addWidget(self.skuTextField)

        # Label für "Bestand"
        stockLabel = QLabel("Bestand")
        inputRowLayout.addWidget(stockLabel)

        # Textfeld für Bestand
        self.stockTextField = QLineEdit()
        self.stockTextField.setObjectName("stockTextField")  # Namensgebung für das Textfeld, falls benötigt
        inputRowLayout.addWidget(self.stockTextField)

        # Button für Bestand aktualisieren
        self.actionButton = QPushButton("Bestand aktualisieren")
        self.actionButton.clicked.connect(self.updateEbayAmount)  # Aktualisiere Bestand
        inputRowLayout.addWidget(self.actionButton)

        # Button für Suche SKU
        self.actionButton = QPushButton("SKU suche")
        self.actionButton.clicked.connect(self.sucheSKU)  # Suche Zeile mit SKU Nummer
        inputRowLayout.addWidget(self.actionButton)


        # Füge das horizontale Layout dem bestehenden vertikalen Layout hinzu
        layout.addLayout(inputRowLayout) 

        # QTableWidget-Konfiguration
        self.tableWidget = QTableWidget()
        layout.addWidget(self.tableWidget)
        mainWidget.setLayout(layout)

    def sucheSKU(self):
        print("")


    def updateEbayAmountAll(self):

        merged_df = self.erstelleAktuellesDatenframe();
        stock_df = self.getStockDataDF()

        # Berechnen der Bestandsdifferenz und Aktualisieren der stock_data.csv
        for index, row in merged_df.iterrows():
            sku = row['SKU']
            new_stock = row['Ebay Bestand'] + row['Stock-Differenz']
            if sku in stock_df['SKU'].values:
                current_stock = stock_df.loc[stock_df['SKU'] == sku, 'Stock'].iloc[0]
                if current_stock != new_stock:
                    stock_df.loc[stock_df['SKU'] == sku, 'Stock'] = new_stock
            elif new_stock > 0:
                # SKU existiert noch nicht in stock_df, füge sie hinzu
                stock_df = stock_df._append({'SKU': sku, 'Stock': new_stock}, ignore_index=True)

        # Speichere den aktualisierten DataFrame in der CSV-Datei.
        stock_df.to_csv(self.getStockDataCSVPath(), index=False)

        self.display_csv_data()

    def getStockDataCSVPath(self):
        return os.path.join(self.getAppDirectory(), 'stock_data.csv');

    def getStockDataDF(self):
        self.ensure_stock_data_file_exists()
        df = pd.read_csv(self.getStockDataCSVPath())
        df['SKU'] = df['SKU'].astype(str)
        return df

    def updateEbayAmount(self):
        sku = str(self.skuTextField.text().strip())
        try:
            stock = int(self.stockTextField.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Ungültiger Bestand", "Der Bestand muss eine ganze Zahl sein.")
            return

        df = self.getStockDataDF()

        # Überprüfe, ob die SKU bereits im DataFrame vorhanden ist.
        if sku in df['SKU'].values:
            # Aktualisiere den Bestand für die existierende SKU.
            df.loc[df['SKU'] == sku, 'Stock'] = stock
        else:
            # Füge einen neuen Datensatz hinzu, wenn die SKU nicht vorhanden ist.
            new_row = pd.DataFrame({'SKU': [sku], 'Stock': [stock]})
            df = pd.concat([df, new_row], ignore_index=True)

        # Entferne Duplikate basierend auf der 'SKU' Spalte, behalte den letzten Eintrag.
        df = df.drop_duplicates(subset='SKU', keep='last')

        # Stelle sicher, dass der 'Stock' als Ganzzahl gespeichert wird.
        df['Stock'] = df['Stock'].astype(int)

        # Speichere den aktualisierten DataFrame in der CSV-Datei.
        df.to_csv(self.getStockDataCSVPath(), index=False)
        
        QMessageBox.information(self, "Bestand aktualisiert", "Der Bestand wurde erfolgreich aktualisiert.")

        self.display_csv_data()
        

    def ensure_stock_data_file_exists(self):
        """Stellt sicher, dass die stock_data.csv-Datei existiert. Erstellt eine leere Datei, falls nicht vorhanden."""
        stock_data_path = os.path.join(self.getAppDirectory(), 'stock_data.csv')
        if not os.path.exists(stock_data_path):
            # Erstelle eine leere DataFrame mit den erforderlichen Spalten
            df = pd.DataFrame(columns=['SKU', 'Stock'])
            # Speichere die leere DataFrame als CSV-Datei
            df.to_csv(stock_data_path, index=False)
            print(f"Die Datei {stock_data_path} wurde erstellt.")

    def openAppDirectory(self):
        appDirectory = self.getAppDirectory();
        print("OPEN DIRECTORY: " + appDirectory);
        subprocess.run(["open",appDirectory])
 
    def getAppDirectory(self):
        appName = 'lagerbestand'
        user_home = os.path.expanduser('~')
        appDirectory = os.path.join(user_home,'Library','Application Support',appName)
        if not os.path.exists(appDirectory):
            os.makedirs(appDirectory)
        return appDirectory
 
    def find_last_two_csv_files(self):
        csv_files = [f for f in os.listdir(self.getAppDirectory()) if f.endswith('.csv') and f != 'stock_data.csv']
        sorted_files = []
        for filename in csv_files:
            try:
                # Versuche, das Datum aus dem Dateinamen zu extrahieren
                date = datetime.strptime(filename, "%d-%m-%Y.csv")
                sorted_files.append((date, filename))
            except ValueError:
                # Ignoriere Dateien, die nicht dem erwarteten Format entsprechen
                continue
        # Sortiere die Dateien nach Datum
        sorted_files.sort(reverse=True)
        # Gib die Namen der letzten beiden Dateien zurück
        return [filename for _, filename in sorted_files[:2]]
    
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
            self.updateEbayAmountAll()
            QMessageBox.information(self, "Information", "CSV-Datei erfolgreich heruntergeladen. Bestand aktualisiert")
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
 

    def erstelleAktuellesDatenframe(self) -> pd.DataFrame:

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

        # Lade die Bestandsdaten aus der stock_data.csv
        stock_data_path = os.path.join(self.getAppDirectory(), 'stock_data.csv')
        if os.path.exists(stock_data_path):
            stock_df = pd.read_csv(stock_data_path)
             # Konvertiere die 'SKU'-Spalte explizit in String, um Typkonflikte zu vermeiden
            stock_df['SKU'] = stock_df['SKU'].astype(str)
            stock_df['Stock'] = stock_df['Stock'].astype(int64)
        else:
            QMessageBox.warning(self, "Warnung", "Stock-Daten-Datei nicht gefunden.")
            return

        # Setze 'SKU' als Index
        #df_today.set_index('SKU', inplace=True)
        #df_yesterday.set_index('SKU', inplace=True)
 
        # Merge die DataFrames basierend auf 'SKU'
        merged_df = pd.merge(df_today[['SKU', 'Avaliable', 'Stock']], df_yesterday[['SKU', 'Avaliable', 'Stock']], on='SKU', suffixes=(f' ({label_today})', f' ({label_yesterday})'))


        # Berechne die Differenz der 'Stock'-Werte
        merged_df['Stock-Differenz'] = merged_df[f'Stock ({label_today})'] - merged_df[f'Stock ({label_yesterday})']
 

        # Füge die Bestand-Daten zur merged_df hinzu und fülle fehlende Werte mit 0 auf
        merged_df = pd.merge(merged_df, stock_df[['SKU', 'Stock']], on='SKU', how='left').fillna(0)
        merged_df.rename(columns={'Stock': 'Ebay Bestand'}, inplace=True)
        # Konvertiere 'Aktueller Bestand' explizit in int, um Dezimalstellen zu entfernen
        merged_df['Ebay Bestand'] = merged_df['Ebay Bestand'].astype(int)
        return merged_df
    
    def display_csv_data(self):

        merged_df = self.erstelleAktuellesDatenframe();
        stock_df = self.getStockDataDF()

        filtered_df = merged_df[merged_df['SKU'].isin(stock_df['SKU'])]

        # Setze die Tabelle auf
        self.tableWidget.clear()
        self.tableWidget.setRowCount(len(filtered_df.index))
        self.tableWidget.setColumnCount(len(filtered_df.columns))
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
        headers = [f'{col}' for col in filtered_df.columns]
        self.tableWidget.setHorizontalHeaderLabels(headers)
 
        # Fülle die Tabelle
        for row, (index, row_data) in enumerate(filtered_df.iterrows()):
            self.tableWidget.setItem(row, 0, QTableWidgetItem(index))  # SKU
            for col, data in enumerate(row_data):
                self.tableWidget.setItem(row, col, QTableWidgetItem(str(data)))
       
        # Annahme, dass Sie die Tabelle hier bereits gefüllt haben
        stock_diff_column_index = self.tableWidget.columnCount() - 2  # Angenommen, Stock-Differenz ist die letzte Spalte
 
        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(row, stock_diff_column_index)
            if item:  # Überprüfen Sie, ob das Item existiert
                stock_diff_value = float(item.text())  # Konvertieren Sie den Wert in float
                color = None
                if stock_diff_value < 0 or stock_diff_value > 0:
                    color = QBrush(QColor(0, 0, 139))
                    foregroundColor = QBrush(QColor(255, 255, 255))
               
                if color:
                    for col in range(self.tableWidget.columnCount()):
                        self.tableWidget.item(row, col).setBackground(color)
                        self.tableWidget.item(row, col).setForeground(foregroundColor)
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
 
