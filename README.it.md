# MyHouse Pro Cloud

Integrazione non ufficiale della comunità per Home Assistant, provata con due termostati **MAXA MC6** collegati al servizio MyHouse Pro. Curata da Ignazio Giannossi, senza affiliazione o approvazione del produttore.

[English](README.md) · [Segnala un problema](https://github.com/ignaziogiannossi/home-assistant-myhouse-pro/issues)

## Stato e funzioni

Prima versione candidata alla distribuzione pubblica: **0.2.1**, derivata dalla 0.2.0 usata sui due MC6. Altri modelli e account restano da verificare. L'installazione tramite link GitHub è distinta dall'inserimento nel catalogo ricercabile del Marketplace/HACS, che richiede una revisione.

| Funzione | Comportamento |
| --- | --- |
| Temperatura ambiente e umidità | Lettura cloud ogni 60 secondi per termostato |
| Accensione e spegnimento | Comando esplicito seguito da rilettura cloud |
| Temperatura desiderata | Entità numerica, 5–35 °C a passi di 0,5 °C |
| Dati aggiuntivi | Differenziale, antigelo, mantenimento e altri campi disponibili, tutti in sola lettura |
| Più termostati | Ripetere la configurazione per ciascun dispositivo |
| Diagnostica | Solo dati numerici selezionati, senza credenziali, identificativi, nomi o risposte cloud complete |

Alcuni dati aggiuntivi sono codici o durate del produttore con significato/unità ancora da verificare: le etichette lo indicano. I campi assenti risultano non disponibili.

**La conferma cloud non equivale alla conferma fisica.** I dati possono essere ritardati o diversi dal display. L'integrazione non misura il relè della richiesta calore e non crea un'entità `climate`: eventuali calcoli di isteresi e plance personalizzate sono separati. Termostato acceso non significa caldaia in riscaldamento. Cambio caldo/freddo, programmazione, tastiera e comandi ventola non sono implementati.

## Connessione e credenziali

Il protocollo del produttore implementato usa **HTTP**, con cifratura applicativa AES-ECB e chiave fissa: **non offre la protezione HTTPS** contro chi può intercettare o modificare il traffico. Questo limite è indicato anche nella configurazione. Non vengono disattivate verifiche dei certificati né seguiti reindirizzamenti delle richieste.

Le credenziali del proprio account vengono salvate nella configurazione locale di Home Assistant e inviate al servizio MyHouse Pro per l'accesso. Proteggere Home Assistant e i backup. Il progetto non raccoglie telemetria e il repository non contiene credenziali, configurazioni domestiche o registri degli utenti. Servono Internet e il cloud del produttore; modifiche del servizio possono interrompere l'integrazione.

## Installazione

Richiede **Home Assistant 2026.11 o successivo**, versione attualmente presa come riferimento.

1. Aprire **Impostazioni → Marketplace → Aggiungi da link**.
2. Inserire `https://github.com/ignaziogiannossi/home-assistant-myhouse-pro`, scegliere **Integrazione** se richiesto e installare.
3. Riavviare Home Assistant.
4. Aprire **Impostazioni → Dispositivi e servizi → Aggiungi integrazione → MyHouse Pro Cloud**.
5. Leggere la nota sulla connessione, inserire email e password del proprio account e scegliere un termostato. Ripetere per gli altri dispositivi.

Con HACS usare **Repository personalizzati**, lo stesso link e categoria **Integrazione**. Per l'installazione manuale copiare `custom_components/myhouse_pro` nella cartella `custom_components` della configurazione HA, riavviare e seguire i punti 4–5.

Il termostato deve già funzionare nell'app MyHouse Pro ed essere in modalità Wi-Fi/cloud. Per questa integrazione non va attivato Modbus TCP. La configurazione esegue solo letture e non modifica automaticamente accensione, temperature o programmi.

## Aggiornamento del prototipo

Creare prima un backup di Home Assistant. Dominio `myhouse_pro`, formato della configurazione e identificativi delle entità della 0.2.0 sono conservati. Sostituire la cartella del componente o affidarne la gestione a Marketplace/HACS, quindi riavviare e verificare letture e plance. I nomi supportano ora italiano e inglese; i nomi personalizzati restano gestiti dal registro entità di HA. Nessuna plancia o automazione domestica viene distribuita o modificata da questo pacchetto.

## Problemi e rimozione

- Accesso rifiutato: verificare le credenziali nell'app. La riautenticazione richiede lo stesso account.
- Termostato assente: controllare modalità cloud, account e visibilità nell'app. I dispositivi diversi dai tipi termostato/riscaldamento del protocollo sono esclusi.
- Entità non disponibili: controllare app, Internet e servizio cloud e attendere il prossimo aggiornamento. Le risposte sconosciute vengono rifiutate.
- Comando non confermato: controllare app e display prima di riprovare. Un timeout non dimostra che il comando non sia stato eseguito; le scritture non vengono reinviate automaticamente.
- Valori aggiuntivi insoliti: indicare campo e modello, senza attribuire significati non verificati ai codici.
- Rimozione: eliminare la voce in **Dispositivi e servizi**, disinstallare dal Marketplace/HACS (o rimuovere la cartella per l'installazione manuale) e riavviare. Il controllo manuale del termostato è indipendente.

Nelle segnalazioni indicare versioni, modello, comportamento atteso e osservato, usando solo dati anonimizzati. Non pubblicare password, token, identificativi, nomi di casa, schermate non oscurate o backup completi.

## Verifiche

I test automatici usano dati fittizi: verificano protocollo, comandi, rilettura e struttura del pacchetto. GitHub Actions esegue anche HACS e hassfest. Non sostituiscono le prove su altri termostati e account. Dettagli e comandi nel [README inglese](README.md).

Licenza MIT. Nomi e marchi appartengono ai rispettivi titolari; l'icona è un simbolo generico originale.
