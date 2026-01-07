# Anforderungen

Um das Projekt korrekt bearbeiten zu können, müssen zuvor die Anforderungen mit Problemstellung, Ziel und weiteren Hinweise geklärt werden.

## Problembeschreibung

Die Arbeit als System Engineer bedeutet oft das Bearbeiten von den immer wieder gleichen Aufgaben. Manche Tage arbeitet man nur an repetitiven Aufgaben wie z.B. das (Grund)-Konfigurieren von Switchen.

Grundsätzlich muss man sich dabei mit jedem einzelnen Switch nacheinander über die Konsole verbinden, verschiedene Einstellungen treffen, um anschließend per SSH oder HTTP(S) weiter konfigurieren zu können.

Manche Kundenaufträge verlangen diese Aufgabe bei mehr als einem Dutzend Switchen. Das kann dann schon einen ganzen Tag in Anspruch nehmen. 

## Zielstellung

Die Lösung für das zuvor genannte Problem ist damit eindeutig. Dadurch, dass das Problem durch die Repetitivität der Aufgabe entsteht, soll hier eine Automatisierung der Aufgabe entstehen. Dabei soll das System den System Engineer größtmöglich entlasten. 

Fehler müssen ausgeschlossen werden, denn wenn Fehler passieren, wird dem System nicht vertraut und es wird nicht genutzt. Wenn es nicht genutzt wird, können System Engineers nicht entlastet werden.

## Business Objectives

1. Zeitersparnis für System Engineers maximieren  
2. Fehlerfreie Bearbeitung der Aufgabe  
3. Einfache, Intuitive Nutzung des Systems ohne Schulungen

## Ausgangslage

Im Lab steht aktuell ein von mir zuvor gebautes System, welches die Möglichkeit bietet, bis zu 16 Konsolen Sessions gleichzeitig zu betreiben. Diese Voraussetzung vereinfacht das Projekt stark, da Switche so noch schneller automatisch konfiguriert werden, ohne die Switche nacheinander anstecken zu müssen. Das System basiert auf einem Raspberry PI mit einem 16-Stecker-Konsolen Adapter. Der Raspberry PI kennt die Ports mit Symlinks über “port\<1-16\>”.

# System Design

## **1\) Empfohlenes Ziel-Design (Kombination aus C \+ D)**

### **Architektur in 2 Phasen (entscheidend für Fehlerfreiheit & Geschwindigkeit)**

**Phase 1: Console Bootstrap (auf dem Pi, parallel bis 16 Ports)**

* Ziel: Minimale, standardisierte Baseline, damit das Gerät stabil via SSH/HTTPS erreichbar ist.  
* Typische Baseline:  
  * Hostname  
  * Management-IP/Mask/Gateway  
  * mgmt VLAN / Interface / VRF (vendorabhängig)  
  * SSH aktivieren, Keys, lokale Admin-Creds (oder initiale Passwörter)  
  * HTTP(S) optional  
  * NTP/DNS optional, nur wenn gefordert  
  * Save/Write memory

* Ergebnis: Device ist remote erreichbar und eindeutig identifizierbar.


**Phase 2: Remote Provisioning (SSH, optional Ansible/Nornir)**

* Ziel: Alles, was umfangreich ist und besser idempotent geht (VLANs, Trunks, STP, LLDP, SNMP, AAA, Banner, Syslog).  
* Vorteil: Deutlich weniger “Screen-scraping”, bessere Validierbarkeit.

### **Kernkomponenten (konkret)**

1. **Frontend (Wizard \+ Live Dashboard)**

   * Auftrag anlegen, Geräte-Inputs erfassen/importieren, Port-Zuordnung.  
   * “Preview” der generierten Konfiguration pro Gerät.  
   * Start/Stop, Live-Logs, Ergebnis-Report (PDF/CSV).

2. **Backend API (FastAPI)**

   * Endpoints: Jobs, Devices, Ports, Templates, Runs, Reports.  
     Auth: kein Auth, Lan Only Zugriff ausreichend  
3. **Session Engine (Python)**

   * `pyserial` pro `portX` (robuste Settings: baudrate, parity, flow control).  
   * Pro Session eine **State Machine**:

     * Connect → Detect vendor/OS/prompt → optional “factory default dialog handling”  
     * Enter enable/config mode  
       Apply baseline commands in kontrollierten Blöcken  
     * Verify (show commands \+ Parser)  
     * Save  
   * Parallelität: `asyncio` mit Threadpool oder reine Threads (pro Port ein Worker). Aufträge müssen nicht 100% parallel ausgeführt werden. Batching mit je 4 Ports ausreichend.

4. **Template & Policy Layer**

   * Jinja2-Templates pro Vendor/Model/OS-Version.  
   * Strikte Trennung: Daten (Inputs) vs. Render-Logik.  
   * Policy-Regeln: z. B. “Gateway muss im Subnetz liegen”, “IP darf nicht doppelt”, “Hostname-Schema”.

5. **Parsing & Verification**

   * TextFSM / Genie / eigene Regex-Parser, um “show” Ausgaben zu normalisieren.  
   * Verifikation als “Pass/Fail” Kriterien (z. B. Management-IP gesetzt, SSH listening, VLAN existiert).

6. **Persistenz & Audit**

   * SQLite (lokal, simpel, ausreichend) für Jobs/Devices/Runs.  
   * Logfiles pro Run/Port (rotierend), plus strukturierte Events in DB.

---

## **2\) User-Inputs und UX-Workflow (ohne Schulung bedienbar)**

### **A) Inputs, die der System Engineer liefert**

Minimal (für Console Bootstrap):

* Anzahl Geräte / Zielauftrag (Jobname)  
* Pro Gerät:

  * Port (“auto-detect & assign”)  
  * Vendor/Model (oder Auto-Erkennung, falls möglich)  
  * Hostname  
  * Management-IP, Maske, Gateway  
  * Mgmt VLAN (falls erforderlich)  
  * Zugangsdaten (initial/target), SSH-Policy (Key/Password)  
     Optional:

* DNS/NTP/Syslog  
* Admin-User/Role-Mapping  
* “Enable secret” / privilege escalation (vendorabhängig)  
* Compliance-Profil (z. B. “Customer A Baseline”)

Praktisch für viele Switches:

* **CSV-Import** (oder Excel-Export als CSV) mit Spalten:  
  * `port, hostname, mgmt_ip, mask, gateway, mgmt_vlan, model, serial(optional), site(optional)`

### **B) Geführter Workflow im UI (Ziel: One-Wizard)**

1. **Job erstellen** (Customer/Projekt/Datum automatisch vorbelegt)  
2. **Geräte-Daten importieren** (CSV) oder manuell hinzufügen  
3. **Ports scannen**: Live-Detect, welche `port1..port16` aktiv sind  
4. **Geräte zuordnen**:

   * Entweder durch manuelle Auswahl je Port  
   * Oder Auto-Zuordnung via “Press Enter” → liest Banner/Prompt → identifiziert

5. **Preview**:

   * Rendered Baseline pro Gerät anzeigen (diff-fähig)  
     Validierungsfehler inline (rot) mit konkreter Korrektur

6. **Run starten**:

   * Parallelisiert über alle Ports  
   * Live Status \+ Logs

7. **Verifikation & Report**:

   * “Verified” nur, wenn Checks erfüllt  
   * Export: CSV/PDF mit Ergebnissen, Zeiten, verwendeten Templates, Hash der Konfig

---

## **3\) Fehlerfreiheit systematisch sicherstellen (entscheidend für Akzeptanz)**

### **Technische Mechanismen**

* **Input-Validation vor Start**

  * IP-Format, Subnetzlogik, Duplikate, reserved ranges, VLAN range.

* **Deterministische Templates**

  * Keine freien Textfelder ohne Constraints (z. B. Hostname Regex).

* **Command Execution in Blöcken**

  * Nach jedem Block Checkpoint: Prompt OK? Error-Messages erkannt?

* **Erkennung typischer CLI-Fehler**

  * “Invalid input”, “Ambiguous”, “Incomplete command”, “% Error”.

* **Timeout-/Retry-Strategie**

  * Bei unstable console: Reconnect, “send newline”, prompt re-sync.

* **Verifikation nach Apply**

  * `show running-config | include ...` oder vendor-equivalent  
  * `show ip interface`, `show vlan`, `show ssh`, etc.

* **Fail-fast \+ sichere Abbrüche**

  * Wenn kritische Schritte scheitern (z. B. mgmt IP), Job stoppt für dieses Gerät und markiert “Needs attention”.

* **Auditierbarkeit**

  * Alle Inputs \+ generierte Config \+ Outputs versioniert (Hash, Zeit, Template-Version).

### **Operative Mechanismen**

* “Golden baseline profiles”.  
* “Dry-run” Mode (nur Render \+ Plausibilitätschecks, ohne Apply).  
* “Staged rollout”: zuerst 1–2 Geräte, dann “Apply to all”.

