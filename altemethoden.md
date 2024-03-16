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