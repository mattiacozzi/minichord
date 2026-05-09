import os
import sys
import mido                                     #MIDI
from PyQt6 import QtWidgets, uic, QtGui, QtCore #UI
from datetime import datetime                   #Timestamps

# apertura porta virtuale con il nome del programma
out_port = mido.open_output('MiniChord di Alice', virtual=True)
# percorso relativo
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# creo una classe che eredita le proprietà di QMainWindow
class MiniChord(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # recupero il percorso dell'interfaccia
        ui_path = resource_path("interfaccia.ui")
        # carico il file dell'interfaccia
        uic.loadUi(ui_path, self)
        # dict degli accordi impostati
        self.accordi = {
            'maggiore': {   # default
                'nome_completo': 'Maggiore',
                'abbreviato': 'Maj',
                'intervalli': [0, 4, 7, 12],
                'widget': self.radio0
            },
            'minore': {
                'nome_completo': 'Minore',
                'abbreviato': 'min',
                'intervalli': [0, 3, 7, 12],
                'widget': self.radio1
            },
            'diminuito': {
                'nome_completo': 'Diminuito',
                'abbreviato': 'dim',
                'intervalli': [0, 3, 6, 12],
                'widget': self.radio2
            },
            '7maggiore': {
                'nome_completo': 'Settima Maggiore',
                'abbreviato': 'maj7',
                'intervalli': [0, 4, 7, 11],
                'widget': self.radio3
            },
            '7minore': {
                'nome_completo': 'Settima Minore',
                'abbreviato': 'min7',
                'intervalli': [0, 3, 7, 10],
                'widget': self.radio4
            },
            '7dom': {
                'nome_completo': 'Settima di Dominante',
                'abbreviato': '7',
                'intervalli': [0, 4, 7, 10],
                'widget': self.radio5
            },
            '7semidim': {
                'nome_completo': 'Settima Semidiminuita',
                'abbreviato': 'm7',
                'intervalli': [0, 3, 6, 10],
                'widget': self.radio6
            },
            '7dim': {
                'nome_completo': 'Settima Diminuita',
                'abbreviato': 'dim7',
                'intervalli': [0, 3, 6, 9],
                'widget': self.radio7
            }
        }
        # lista con i nomi (brevi) degli accordi, cioè le chiavi del dict precedente
        nomi_accordi = list(self.accordi.keys())

        # inizializzazione dei parametri di default
        self.volume = 35
        self.ottava = 4
        # usa il primo elemento del dict degli accordi come default
        self.accordo = next(iter(self.accordi))
        self.channel = 0
        self.sustain = False
        self.chord_mode = True
        self.record_mode = False

        # scorciatoie da tastiera
        self.actions = {'+': lambda: self.set_volume(self.volume + 5),
                        '-': lambda: self.set_volume(self.volume - 5),
                        '0': lambda: self.set_accordo(nomi_accordi[0]),
                        '1': lambda: self.set_accordo(nomi_accordi[1]),
                        '2': lambda: self.set_accordo(nomi_accordi[2]),
                        '3': lambda: self.set_accordo(nomi_accordi[3]),
                        '4': lambda: self.set_accordo(nomi_accordi[4]),
                        '5': lambda: self.set_accordo(nomi_accordi[5]),
                        '6': lambda: self.set_accordo(nomi_accordi[6]),
                        '7': lambda: self.set_accordo(nomi_accordi[7]),
                        '8': lambda: self.set_ottava(self.ottava - 1),
                        '9': lambda: self.set_ottava(self.ottava + 1),
                        ',': lambda: self.set_channel(self.channel - 1),
                        '.': lambda: self.set_channel(self.channel + 1),
                        'z': lambda: self.toggle_sustain(),
                        'x': lambda: self.panic(),
                        'c': lambda: self.toggle_mode(),
                        'b': lambda: self.clear_all_buffers(),
                        'n': self.recButton.toggle,
                        'm': lambda: self.save_to_file(),}

        # mappatura delle 12 note di base e dei tasti che le suonano
        self.note_map = {
            'a': {'midi': 12, 'it': 'Do',  'en': 'C'}, 
            's': {'midi': 13, 'it': 'Do#', 'en': 'C#'}, 
            'd': {'midi': 14, 'it': 'Re',  'en': 'D'}, 
            'f': {'midi': 15, 'it': 'Re#', 'en': 'D#'}, 
            'g': {'midi': 16, 'it': 'Mi',  'en': 'E'}, 
            'h': {'midi': 17, 'it': 'Fa',  'en': 'F'}, 
            'j': {'midi': 18, 'it': 'Fa#', 'en': 'F#'}, 
            'k': {'midi': 19, 'it': 'Sol', 'en': 'G'}, 
            'l': {'midi': 20, 'it': 'Sol#', 'en': 'G#'}, 
            'ò': {'midi': 21, 'it': 'La',  'en': 'A'}, 
            'à': {'midi': 22, 'it': 'La#', 'en': 'A#'}, 
            'ù': {'midi': 23, 'it': 'Si',  'en': 'B'}
        }

        # dict in cui salvare le note attive
        self.active_notes = {}
        # lista degli ultimi accordi/note suonati
        self.history_list = []
        # lista in cui salvare una registrazione (fa da buffer)
        self.recorded_data = []
        # welcome text
        self.histLabel.setText("Ciao, benvenuta nel tuo MiniChord!")

#|-------------|
#| INTERFACCIA |
#|-------------|
        # configurazione iniziale dei widget
        self.volDial.setValue(self.volume)
        self.volSpin.setValue(self.volume)
        self.octDial.setValue(self.ottava)
        self.octSpin.setValue(self.ottava)
        self.chanSpin.setValue(self.channel)
        self.chanDial.setValue(self.channel)
        # attiva il radio del primo elemento del dict degli accordi
        self.set_accordo(next(iter(self.accordi)))
        # rendo il bottone di registrazione un interruttore
        self.recButton.setCheckable(True)
        # collega l'interfaccia ai valori delle variabili
        self.connetti_interfaccia()

    # contiene le funzioni da eseguire al verificarsi di certe azioni nell'interfaccia
    def connetti_interfaccia(self):
        # dials (gli spins si aggiornano automaticamente)
        self.volDial.valueChanged.connect(self.set_volume)
        self.octDial.valueChanged.connect(self.set_ottava)
        self.chanDial.valueChanged.connect(self.set_channel)
        # bottone per spegnimento completo note (Kill 'em All)
        self.panicButton.clicked.connect(self.panic)
        # sliders
        self.susSlider.valueChanged.connect(self.toggle_sustain)
        self.modeSlider.valueChanged.connect(self.toggle_mode)
        # radio buttons: scorro tra chiavi e valori del dict degli accordi
        for nome, dati in self.accordi.items():
            # recupero quello attivato e cambio l'accordo
            dati['widget'].toggled.connect(lambda checked, n=nome: self.set_accordo(n))
        # bottone di registrazione
        self.recButton.toggled.connect(self.toggle_record)
        # bottone di salvataggio
        self.saveButton.clicked.connect(self.save_to_file)
        # bottone di pulizia
        self.delButton.clicked.connect(self.clear_all_buffers)
#|----------|
#| SETTINGS |
#|----------|
    def set_volume(self, nuovo_valore):
        # limita il valore tra 0 e 127 (standard MIDI)
        self.volume = max(0, min(127, nuovo_valore))
        # sposta il dial
        self.volDial.blockSignals(True)
        self.volDial.setValue(self.volume)
        self.volDial.blockSignals(False)
        # cambia l'indicatore numerico
        self.volSpin.blockSignals(True)
        self.volSpin.setValue(self.volume)
        self.volSpin.blockSignals(False)
        # DEBUG
        print(f"Volume: {self.volume}")

    def set_ottava(self, nuova_ottava):
        # limita il valore tra 0 e 8
        self.ottava = max(0, min(8, nuova_ottava))
        # sposta il dial
        self.octDial.blockSignals(True)
        self.octDial.setValue(self.ottava)
        self.octDial.blockSignals(False)
        # cambia l'indicatore numerico
        self.octSpin.blockSignals(True)
        self.octSpin.setValue(self.ottava)
        self.octSpin.blockSignals(False)
        # DEBUG
        print(f"Ottava: {self.ottava}")

    def set_channel(self, nuovo_canale):
        # limita il valore tra 0 e 15
        self.channel = max(0, min(15, nuovo_canale))
        # sposta il dial
        self.chanDial.blockSignals(True)
        self.chanDial.setValue(self.channel)
        self.chanDial.blockSignals(False)
        # cambia l'indicatore numerico
        self.chanSpin.blockSignals(True)
        self.chanSpin.setValue(self.channel)
        self.chanSpin.blockSignals(False)
        # DEBUG
        print(f"Canale: {self.channel}")
    
    def set_accordo(self, nuovo_accordo):
        # scopro chi ha chiamato la funzione
        mittente = self.sender()
        # se il mittente è None (cioè la tastiera) oppure il mouse ha attivato un radio
        if mittente is None or mittente.isChecked():
            # cambia la variabile col nome del nuovo accordo
            self.accordo = nuovo_accordo
            # recupero i dati dell'accordo (sotto forma di dict) dal dict degli accordi
            dati = self.accordi.get(nuovo_accordo)
            if dati:
                # DEBUG
                print(f"Accordo impostato su: {dati['nome_completo']}")
                # recupero il widget su cui devo agire
                widget = dati['widget']
                # blocco gli altri segnali
                widget.blockSignals(True)
                # attivo il radio
                widget.setChecked(True)
                # riattivo i segnali
                widget.blockSignals(False)

    def toggle_sustain(self):
        # inverto il valore booleano
        self.sustain = not self.sustain
        # DEBUG
        print(f"Sustain: {'ON' if self.sustain else 'OFF'}")
        # sposto lo slider
        self.susSlider.blockSignals(True)
        self.susSlider.setValue(self.sustain)
        self.susSlider.blockSignals(False)
    
    def toggle_mode(self):      # (accordo|nota singola)
        # inverto il valore booleano
        self.chord_mode = not self.chord_mode
        # DEBUG
        print(f"Chord mode: {'ON' if self.chord_mode else 'OFF'}")
        # sposto lo slider
        self.modeSlider.blockSignals(True)
        self.modeSlider.setValue(self.chord_mode)
        self.modeSlider.blockSignals(False)
    
    def toggle_record(self, checked):
        # recupero la variabile booleana
        self.record_mode = checked
        # se sto registrando
        if self.record_mode:
            # pulisco l'eventuale registrazione precedente
            self.recorded_data.clear()
            # cambio il colore del bottone
            self.recButton.setStyleSheet("background-color: red; color: white;")
            self.recButton.setText("● Rec") # Opzionale: aggiunge un pallino
        else:
            # torno allo stile predefinito
            self.recButton.setStyleSheet("") 
            self.recButton.setText(" Rec ")
        # se sto registrando, disabilito i pulsanti di pulizia e salvataggio
        self.saveButton.setEnabled(not self.record_mode)
        self.delButton.setEnabled(not self.record_mode)
        # DEBUG
        print(f"Registrazione: {'ON' if self.record_mode else 'OFF'}")

#|-----------------|
#| METODI MUSICALI |
#|-----------------|
    def nota_on(self, nota):
        out_port.send(mido.Message('note_on', channel=self.channel, note=nota, velocity=self.volume))

    def nota_off(self, nota):
        out_port.send(mido.Message('note_on', channel=self.channel, note=nota, velocity=0))
    
    def accordo_on(self, nota, accordo):
        # scorre la lista degli intervalli per il tipo di accordo selezionato
        for intervallo in self.accordi[accordo]['intervalli']:
            # suona tutte le note dell'accordo
            out_port.send(mido.Message('note_on', channel=self.channel, note=nota+intervallo, velocity=self.volume))

    def accordo_off(self, nota, accordo):
        # scorre la lista degli intervalli per il tipo di accordo selezionato
        for intervallo in self.accordi[accordo]['intervalli']:
            # spegni tutte le note dell'accordo
            out_port.send(mido.Message('note_on', channel=self.channel, note=nota+intervallo, velocity=0))

    def panic(self):    # spegni tutto
        out_port.send(mido.Message('control_change', control=123, value=0, channel=self.channel))
        # DEBUG
        print("Spengo tutte le note!")
        # coloro il bottone di rosso
        self.panicButton.setStyleSheet("background-color: red; color: white;")
        # dopo 100 millisecondi rimuovo le modifiche al CSS del bottone
        QtCore.QTimer.singleShot(100, lambda: self.panicButton.setStyleSheet(""))

#|-----------------------------|
#| REGISTRAZIONE E SALVATAGGIO |
#|-----------------------------|
    def registra_evento(self, segnale):
        # se la modalità registrazione è attiva
        if self.record_mode:
            # recupero l'orario e lo formatto fino ai centesimi di secondo
            ora = datetime.now().strftime("%H:%M:%S.%f")[:-4]
            # aggiungo l'ultimo accordo/nota suonati alla fine della lista
            self.recorded_data.append(f"[{ora}] {segnale}")
            # DEBUG
            print(f"La canzone attuale è:\n{self.recorded_data}")

    def save_to_file(self):
        # se sto registrando
        if self.record_mode:
            # DEBUG
            print("Impossibile salvare durante la registrazione. Interrompi e riprova.")
            # non fare nulla
            return
        # se la registrazione è vuota
        if not self.recorded_data:
            # DEBUG
            print("Nulla da salvare!")
            return
        # apro una finestra di dialogo di sistema
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Salva Registrazione", "", "Text Files (*.txt);;All Files (*)"
        )
        # se ho indicato un percorso valido
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    # scorro la lista dei dati registrati
                    for riga in self.recorded_data:
                        # scrivo ogni elemento in una nuova riga
                        f.write(f"{riga}\n")
                # DEBUG    
                print(f"File salvato con successo in: {path}")
            except Exception as e:
                # DEBUG
                print(f"Errore durante il salvataggio: {e}")

    def clear_all_buffers(self):
        # se sto registrando
        if self.record_mode:
            # DEBUG
            print("Impossibile pulire la coda durante la registrazione. Interrompi e riprova.")
            # non fare nulla
            return
        # svuota la lista delle ultime canzoni suonate
        self.history_list.clear()
        # pulisce la lista della registrazione
        self.recorded_data.clear()        
        # aggiorna il testo della barra delle ultime note/accordi suonati
        self.histLabel.setText(" ")
        # DEBUG
        print("Storico e buffer di registrazione svuotati.")

#|---------------------------|
#| BARRA ULTIMI ACCORDI/NOTE |
#|---------------------------|
    def update_history(self, segnale):
        # aggiungo il nome in fondo alla lista
        self.history_list.append(segnale)
        # se necessario, registro l'accordo/nota
        self.registra_evento(segnale)
        # limite elementi: se sono più di 5, elimino il primo (più vecchio)
        if len(self.history_list) > 5:
            self.history_list.pop(0)
        # creo una copia invertita della lista
        history_invertita = self.history_list.copy()
        history_invertita.reverse() 
        # definisco una lista di colori e degli elementi html stilizzati (uno in più, ma non è un problema)
        colori = ["#00FF00", "#00CC00", "#009900", "#006600", "#004400", "#002200"]
        html_elements = []
        # scorro la lista invertita
        for i, accordo in enumerate(history_invertita):
            # recupero i colori in ordine, gli (eventuali) elementi oltre il sesto si prendono tutti il colore più scuro
            colore = colori[i] if i < len(colori) else colori[-1]
            # stilizzo l'elemento e lo aggiungo alla lista
            html_elements.append(f'<span style="color: {colore};">{accordo}</span>')
        # unisco con la freccina
        testo_barra = " <span style='color: #444;'>◄</span> ".join(html_elements)
        # imposto il testo della barra
        self.histLabel.setText(f"{testo_barra}")

#|-----------------------|
#| PRESSIONE DI UN TASTO |
#|-----------------------|
    def keyPressEvent(self, event):
        # se il tasto è una ripetizione (perché è tenuto premuto)
        if event.isAutoRepeat():
            # non fare nulla
            return
        # recupero del tasto
        char = event.text().lower()
        # converto in stringa eventuali pressioni di tasti particolari (alt, ctrl)
        if not char:
            char = QtGui.QKeySequence(event.key()).toString()
        # DEBUG
        print(f"Pressione di {char.upper() if char.islower() else char}")
        # se la nota è già tra quelle attive
        if char in self.active_notes:
            # non fare nulla
            return
        # se char corrisponde ad una delle funzioni del MiniChord
        if char in self.actions:
            # esegui l'azione prendendola dal dict
            self.actions[char]()
        # se char è una delle note preimpostate (seconda riga della tastiera)
        if char in self.note_map:
            # recupera il numero corrispondente alla lettera nel dict delle note
            # e calcola il numero corretto della nota considerando l'ottava selezionata
            note = self.note_map[char]['midi'] + self.ottava*12
            # recupera anche il nome della nota nel dict delle note
            note_name = self.note_map[char]['it']
            # se la modalità accordo è attiva
            if self.chord_mode:
                # invio un accordo del tipo stabilito
                self.accordo_on(note, self.accordo)
                # DEBUG
                print(f"Accordo di {note_name} {self.accordi[self.accordo]['nome_completo']} ({note}, sulla {self.ottava}a ottava)")
                # aggiorno la lista degli ultimi accordi/note
                self.update_history(f"{note_name}{self.accordi[self.accordo]['abbreviato']}")
            else:
                # invio la singola nota
                self.nota_on(note)
                # DEBUG
                print(f"Suono un {note_name} ({note}, sulla {self.ottava}a ottava)")
                # aggiorno la lista degli ultimi accordi/note
                self.update_history(f"{note_name}")
            # salvo la nota nel dict delle note attive: key=char,value=note
            self.active_notes[char] = note

#|----------------------|
#| RILASCIO DI UN TASTO |
#|----------------------|
    def keyReleaseEvent(self, event):
        # se il tasto è una ripetizione (perché è tenuto premuto)
        if event.isAutoRepeat():
            # non fare nulla
            return
        # recupero del tasto
        char = event.text().lower()
        if not char:
            char = QtGui.QKeySequence(event.key()).toString()
        # DEBUG
        print(f"Rilascio di {char.upper() if char.islower() else char}")
        # se la nota è tra quelle attive
        if char in self.active_notes:
            # recupero il numero della nota
            note = self.active_notes[char]
            # con sustain attivo,
            if self.sustain:
                # rimuovo dalle note attive ma non spengo la nota/accordo
                del self.active_notes[char]
                # DEBUG
                print(f"Nota {note} rimossa dalla coda (Sustain ON)")
            # con sustain spento,
            else:
                # rimuovo la nota quelle attive
                del self.active_notes[char]
                # se sono in modalità accordo
                if self.chord_mode:
                    # spengo l'accordo
                    self.accordo_off(note, self.accordo)
                # se invece sono in modalità singola nota
                else:
                    # spengo la singola nota
                    self.nota_off(note)
                # DEBUG                
                print(f"Nota {note} rimossa dalla coda e spenta (Sustain OFF)")

#|-----------------------|
#| PULIZIA ALLA CHIUSURA |
#|-----------------------|
    def closeEvent(self, event):    # sovrascrivo la funzione closeEvent di QMainWindow con una personalizzata
        # spegno tutte le note
        self.panic()
        # chiudo la porta
        out_port.close()
        # DEBUG
        print("Chiusura programma e porta MIDI in corso.")
        # procedo con la chiusura della finestra
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    # creo la finestra con la classe che ho creato
    window = MiniChord()
    # mostro la finestra
    window.show()
    # avvio dell'app
    sys.exit(app.exec())