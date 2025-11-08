       05  ACCT-ID             PIC X(12).
       05  CUST-ID             PIC X(12).
       05  PRODUCT-CODE        PIC X(4).     *> "CHK ","SAV "
       05  ACCT-STATUS         PIC X(1).     *> "A","I","F"
       05  CURR-BAL            PIC S9(11)V99 COMP-3.
       05  OVERDRAFT-LIMIT     PIC S9(9)V99  COMP-3.
       05  OPEN-DATE           PIC 9(8).     *> YYYYMMDD
       05  CLOSE-DATE          PIC 9(8).     *> 0 or YYYYMMDD
