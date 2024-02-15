from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QMessageBox
from PySide6.QtCore import Slot
from datetime import datetime, timedelta
import os
import sys
import requests
import pandas as pd

class CSVLoaderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lagerbestand")
        self.csv_url = "https://exhaust.pl/produts_stock/export.csv"
        self.last_downloaded_file = None  # Hält den Pfad der zuletzt heruntergeladenen Datei

        mainWidget = QWidget()
        self.setCentralWidget(mainWidget)
        layout = QVBoxLayout()

        # Button zum Herunterladen der CSV-Datei
        self.downloadButton = QPushButton("CSV herunterladen")
        self.downloadButton.clicked.connect(self.download_and_save_csv)
        layout.addWidget(self.downloadButton)

        # Button zum Laden und Anzeigen der Daten aus der CSV-Datei
        self.loadButton = QPushButton("Daten anzeigen")
        self.loadButton.clicked.connect(self.load_current_csv)
        layout.addWidget(self.loadButton)

        # QTableWidget-Konfiguration
        self.tableWidget = QTableWidget()
        layout.addWidget(self.tableWidget)
        mainWidget.setLayout(layout)

    @Slot()
    def load_current_csv(self):
        filepath = self.download_and_save_csv()
        if filepath:  # Prüfe, ob der Download erfolgreich war
            self.display_csv_data()

    def download_and_save_csv(self):
        try:
            response = requests.get(self.csv_url)
            response.raise_for_status()
            current_date = datetime.now().strftime("%d-%m-%Y")
            filename = f"{current_date}.csv"
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(response.text)
            self.last_downloaded_file = filename  # Speichere den Pfad der heruntergeladenen Datei
            QMessageBox.information(self, "Information", "CSV-Datei erfolgreich heruntergeladen.")
            return filename
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
        filename_today, filename_yesterday = self.generate_filenames_for_last_two_days()

        # Überprüfe, ob die Dateien existieren
        if not os.path.exists(filename_today) or not os.path.exists(filename_yesterday):
            QMessageBox.warning(self, "Warnung", "Eine oder beide Dateien für die letzten beiden Tage fehlen.")
            return

        # Lese die CSV-Dateien ein
        df_today = pd.read_csv(filename_today, sep=',')
        df_yesterday = pd.read_csv(filename_yesterday, sep=',')

        # Entferne Duplikate in der SKU-Spalte
        df_today.drop_duplicates(subset=['SKU'], inplace=True)
        df_yesterday.drop_duplicates(subset=['SKU'], inplace=True)

        # Setze 'SKU' als Index
        df_today.set_index('SKU', inplace=True)
        df_yesterday.set_index('SKU', inplace=True)

        # Merge die DataFrames basierend auf 'SKU' effizient
        merged_df = pd.merge(df_today[['Avaliable', 'Stock']], df_yesterday[['Avaliable', 'Stock']], left_index=True, right_index=True, suffixes=(' (Heute)', ' (Gestern)'))

        # Berechne die Differenz der 'Stock'-Werte
        merged_df['Stock-Differenz'] = merged_df['Stock (Heute)'] - merged_df['Stock (Gestern)']

        # Debugging-Ausgabe
        print("Merged DF:")
        print(merged_df.head())

        # Gib die Länge des DataFrame aus
        print("Länge von merged_df:", len(merged_df))

        # Setze die Tabelle auf
        self.tableWidget.clear()
        self.tableWidget.setRowCount(len(merged_df.index))
        self.tableWidget.setColumnCount(8)  # 8 Spalten für SKU und die restlichen Daten
        self.tableWidget.setHorizontalHeaderLabels(['SKU', 'Avaliable (Heute)', 'Stock (Heute)', 'Avaliable (Gestern)', 'Stock (Gestern)', 'SKU (Gestern)', 'Stock-Differenz'])

        print("table created")

        # Fülle die Tabelle
        for row, (index, row_data) in enumerate(merged_df.iterrows()):
            self.tableWidget.setItem(row, 0, QTableWidgetItem(index))  # SKU
            for col, data in enumerate(row_data):
                table_item = QTableWidgetItem(str(data))
                self.tableWidget.setItem(row, col + 1, table_item)  # Verschiebe um 1, um die SKU zu überspringen



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CSVLoaderApp()
    window.show()
    sys.exit(app.exec_())
