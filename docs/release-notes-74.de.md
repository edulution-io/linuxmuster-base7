# linuxmuster-base7 7.4

linuxmuster-base7 ist das zentrale Werkzeugpaket für die Einrichtung und
Verwaltung des Schulservers – Ersteinrichtung, Geräte- und Netzwerkverwaltung,
Zertifikate sowie die Anbindung der OPNsense-Firewall.

## Grundlegende Überarbeitung für Ubuntu 26.04

Mit 7.4.0 wurde der gesamte Python-Code neu strukturiert und auf ein reguläres
Python-Paket umgestellt. Dabei wurden mehrere sicherheitsrelevante Schwachstellen
geschlossen, unter anderem im Umgang mit Passwörtern und Shell-Befehlen. Die
Anbindung an die OPNsense-Firewall erfolgt seither über deren REST-API statt
über SSH-Kommandos.

## Zertifikatsverwaltung überarbeitet

Die Erneuerung des CA-Zertifikats war zeitweise fehlerhaft: Sie schlug beim
Aufruf fehl oder installierte das neue Zertifikat nicht korrekt im System.
Mit 7.4.21 wurde die Zertifikatserzeugung überarbeitet, die Erneuerung
funktioniert nun wieder zuverlässig. Neu erzeugte Zertifikate enthalten
außerdem die von modernen Browsern und Betriebssystemen erwartete
Zusatzangabe (Subject Alternative Name).

## Stabilität von Firewall, Netzwerk und Systemstart

In den Folgeversionen wurden zahlreiche kleinere Fehler behoben, die im
laufenden Betrieb auftreten konnten – bei der Firewall-Einrichtung (etwa beim
Zurücksetzen der Konfiguration und beim Single-Sign-On des Webproxys), bei
der Quota- und Dateisystemverwaltung sowie beim Netzwerk-Setup (etwa bei der
Prüfung von IP-Adressen in Subnetzen).

## LINBO-Hardwareklassen pro Schule

Hardwareklassen (LINBO-Gruppen) gehören jetzt einer Schule. Für jede Schule außer
`default-school` heißt die Gruppe `<schule>__<gruppe>` (zwei Unterstriche), etwa
`abc__raum101`; die `start.conf.<schule>__<gruppe>` und die Boot-Konfiguration
tragen denselben Namen. Für `default-school` ändert sich nichts. Dadurch können
zwei Schulen eine Gruppe gleichen Namens haben, und ein Schuladministrator kann
nur noch die Gruppen der eigenen Schule sehen und ändern.

**Was beim Upgrade geschieht**

Beim nächsten `linuxmuster-import-devices` einer Schule werden deren bestehende
Gruppen übernommen:

- Die `start.conf.<gruppe>` wird nach `start.conf.<schule>__<gruppe>` kopiert, die
  Zeile `Group` darin wird auf den neuen Namen gesetzt. Eine selbst angelegte
  `<gruppe>.cfg` wird ebenfalls kopiert.
- Übernommen werden nur Gruppen, die die Schule bisher in ihrer Zuordnung
  verwendet hat. Eine Gruppe, die später hinzukommt, startet mit der leeren
  Vorlage und nicht mit der Konfiguration einer anderen Schule.
- Vorhandene Dateien werden nie überschrieben; ein weiterer Lauf ändert nichts.
- Die bisherigen Dateien bleiben unverändert liegen und können nach der
  Kontrolle von Hand gelöscht werden.

**Was Sie beachten müssen**

- Eigene Skripte (`postsync`, `prestart`), die den Gruppennamen auswerten
  (`$HOSTGROUP`), sehen für Schulen außer `default-school` den neuen Namen mit
  Schulpräfix.
- In `devices.csv` darf eine Gruppe kein `__` enthalten; `linuxmuster-import-devices`
  lehnt die Zeile ab. Ein einzelner Unterstrich ist weiterhin erlaubt.
- Die Aktualisierung muss in dieser Reihenfolge erfolgen: zuerst
  linuxmuster-linbo7, dann linuxmuster-base7, danach linuxmuster-tools und
  linuxmuster-api. Ein Client, dessen LINBO-Server noch nicht aktualisiert ist,
  findet die Konfiguration der neuen Gruppe im Offline-Betrieb nicht.
- Wird der Import zwischen der Umstellung der Zuordnung und dem Kopieren der
  Dateien abgebrochen, erkennt der nächste Lauf die bisherigen Gruppen nicht
  mehr. In dem Fall die Datei `start.conf.<gruppe>` von Hand nach
  `start.conf.<schule>__<gruppe>` kopieren.

## Upgrade-Hinweis

Wegen der grundlegend geänderten Paketstruktur ist ein Umstieg vom Branch 7.3
nur gemeinsam mit dem Upgrade auf Ubuntu 26.04 möglich. Bestehende
Konfigurationsdateien bleiben davon unberührt.

Alle Änderungen im Detail gibt es [hier](https://github.com/linuxmuster/linuxmuster-base7/compare/v7.4.0...master).

Signed-off by: thomas@linuxmuster.net
Assisted by  : Claude
