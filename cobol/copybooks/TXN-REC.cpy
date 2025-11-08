       05  ACCT-ID             PIC X(12).
       05  TXN-ID              PIC X(16).
       05  ORIG-TXN-ID         PIC X(16).
       05  TXN-CODE            PIC X(4).     *> "DEPO","WDRW","FEE ","INT ","REV "
       05  TXN-AMOUNT          PIC S9(9)V99  COMP-3.
       05  TXN-TS              PIC 9(14).    *> YYYYMMDDHHMMSS
       05  CHANNEL             PIC X(4).     *> "ATM ","BRCH","WEB ","ACH "
