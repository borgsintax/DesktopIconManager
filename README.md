# Desktop Icon Manager (DIM)

Desktop Icon Manager (DIM) è un'applicazione Python pensata per la gestione delle posizioni delle icone sul desktop di Windows. Capita spesso, aggiornando i driver delle schede video o cambiando risoluzione allo schermo, che le icone di Windows perdano la loro disposizione originale, finendo raggruppate casualmente. DIM permette di salvare la posizione attuale di tutte le icone del desktop e di ripristinarle in base a questi salvataggi.

Il programma si avvale di un'interfaccia grafica intuitiva (sviluppata con `customtkinter`) e di un modulo core, `icon_manager.py`, che interroga nativamente le API grafiche del sistema operativo Windows per estrarre e successivamente impostare con precisione la posizione (x, y) di ciascuna icona.

## Caratteristiche
- **Salvataggio Posizioni**: Memorizza in tempo reale le esatte coordinate delle icone presenti sul Desktop in piccoli file generati dinamicamente.
- **Ripristino Veloce**: In caso di perdita del posizionamento delle icone, basterà selezionare il backup e cliccare "Ripristina".
- **Backup all'Avvio**: Può essere configurato per essere eseguito in modo completamente invisibile all'avvio di Windows (`--silent`), in modo tale che ogni volta che accenderai il PC un backup della tua griglia icone verrà salvato.
- **Backup del Registro**: Salva a scopo diagnostico o per sicurezza aggiuntiva l'albero del registro Windows che mappa le Desktop Bags.

## Prerequisiti

Per eseguire l'applicativo **è necessario aver installato Python** sul proprio computer.
Puoi scaricare Python dal sito ufficiale: [python.org](https://www.python.org/downloads/) (assicurati di spuntare "Add Python to PATH" durante l'installazione su Windows se non l'hai già fatto).

## Installazione

1. Clona o scarica questo repository sul tuo computer.
2. Apri il Prompt dei Comandi (o PowerShell) e spostati nella cartella contenente i file.
3. Installa i requisiti aprendo il terminale ed eseguendo il comando:

```bash
pip install -r requirements.txt
```

Nello specifico l'unico modulo esterno richiesto è `customtkinter`. Tutte le altre librerie utilizzate sono standard library di Python (come `ctypes`, `json`, etc).

## Come si usa

1. Utilizza il file `start_dim.bat` per lanciare comodamente l'interfaccia grafica. In alternativa, puoi lanciare il programma dal terminale con:
   ```bash
   python dim.py
   ```
2. **Per salvare**: Clicca su **"Backup Posizioni Ora"**. Questo creerà un file JSON nella cartella `/backups/` con posizione e nome di ogni icona.
3. **Per ripristinare**: Seleziona il backup in base alla data e ora dell'esecuzione e premi su **"Ripristina"** di fianco ad esso. Le icone torneranno al loro esatto posto istantaneamente (può essere necessario fare tasto destro su un punto vuoto del desktop sul proprio PC e assicurarsi che `"Disponi icone automaticamente"` sia spento per permetterne il libero movimento).
4. **Altre Opzioni**: 
   - Premi "Esegui Backup all'Avvio di Windows" per far partire silenziosamente il programma all'accensione, creando una cronologia dei tuoi layout desktop.
