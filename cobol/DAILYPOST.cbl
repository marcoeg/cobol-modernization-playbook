       IDENTIFICATION DIVISION.
       PROGRAM-ID. DAILYPOST.

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT ACCT-FILE ASSIGN TO "data/accounts.dat"
               ORGANIZATION IS SEQUENTIAL.
           SELECT TXN-FILE  ASSIGN TO "data/txns.dat"
               ORGANIZATION IS SEQUENTIAL.
           SELECT ACCT-OUT  ASSIGN TO "out/accounts_out.dat"
               ORGANIZATION IS SEQUENTIAL.
           SELECT EXC-FILE  ASSIGN TO "out/exceptions.dat"
               ORGANIZATION IS SEQUENTIAL.

       DATA DIVISION.
       FILE SECTION.
       FD  ACCT-FILE RECORD CONTAINS 58 CHARACTERS.
       01  ACCT-IN-REC.
           COPY "ACCOUNT-REC.cpy".

       FD  TXN-FILE  RECORD CONTAINS 72 CHARACTERS.
       01  TXN-IN-REC.
           COPY "TXN-REC.cpy".

       FD  ACCT-OUT  RECORD CONTAINS 58 CHARACTERS.
       01  ACCT-OUT-REC.
           COPY "ACCOUNT-REC.cpy".

       FD  EXC-FILE  RECORD CONTAINS 72 CHARACTERS.
       01  EXC-REC.
           COPY "TXN-REC.cpy".

       WORKING-STORAGE SECTION.
       77  EOF-ACCT         PIC X     VALUE "N".
       77  EOF-TXN          PIC X     VALUE "N".
       77  TODAY            PIC 9(8)  VALUE 20250101.
       77  NEW-BAL          PIC S9(11)V99 COMP-3.

       *> Helpers to compare TXN-TS(1:8) to TODAY without ref-mod on numeric
       77  WS-TS            PIC 9(14).
       77  WS-TS-DATE       PIC 9(8).
       77  WS-MILLION       PIC 9(7)  VALUE 1000000.

       *> Avoid unary minus directly on qualified name:
       77  WS-NEG-LIMIT     PIC S9(11)V99 COMP-3.

       PROCEDURE DIVISION.
       MAIN.
           OPEN INPUT  ACCT-FILE TXN-FILE
                OUTPUT ACCT-OUT EXC-FILE
           PERFORM READ-NEXT-TXN
           PERFORM UNTIL EOF-ACCT = "Y"
              READ ACCT-FILE
                  AT END MOVE "Y" TO EOF-ACCT
              NOT AT END
                 PERFORM APPLY-TODAYS-TXNS
                 WRITE ACCT-OUT-REC FROM ACCT-IN-REC
              END-READ
           END-PERFORM
           CLOSE ACCT-FILE TXN-FILE ACCT-OUT EXC-FILE
           GOBACK.

       READ-NEXT-TXN.
           READ TXN-FILE
              AT END MOVE "Y" TO EOF-TXN
           END-READ.

       APPLY-TODAYS-TXNS.
           *> Loop until we've consumed this account's txns or reached next account
           PERFORM UNTIL EOF-TXN = "Y"
                    OR ACCT-ID OF TXN-IN-REC > ACCT-ID OF ACCT-IN-REC
              IF ACCT-ID OF TXN-IN-REC < ACCT-ID OF ACCT-IN-REC
                 PERFORM READ-NEXT-TXN
              ELSE
                 *> Extract YYYYMMDD from numeric TXN-TS by integer division
                 MOVE TXN-TS OF TXN-IN-REC TO WS-TS
                 COMPUTE WS-TS-DATE = WS-TS / WS-MILLION

                 IF WS-TS-DATE = TODAY
                    EVALUATE TXN-CODE OF TXN-IN-REC
                       WHEN "DEPO"
                          ADD TXN-AMOUNT OF TXN-IN-REC
                              TO CURR-BAL OF ACCT-IN-REC

                       WHEN "WDRW"
                          COMPUTE NEW-BAL = CURR-BAL OF ACCT-IN-REC
                                           - TXN-AMOUNT OF TXN-IN-REC
                          COMPUTE WS-NEG-LIMIT =
                                  0 - OVERDRAFT-LIMIT OF ACCT-IN-REC
                          IF NEW-BAL >= WS-NEG-LIMIT
                             MOVE NEW-BAL TO CURR-BAL OF ACCT-IN-REC
                          ELSE
                             WRITE EXC-REC FROM TXN-IN-REC
                          END-IF

                       WHEN "FEE "
                          ADD TXN-AMOUNT OF TXN-IN-REC
                              TO CURR-BAL OF ACCT-IN-REC

                       WHEN "INT "
                          ADD TXN-AMOUNT OF TXN-IN-REC
                              TO CURR-BAL OF ACCT-IN-REC

                       WHEN "REV "
                          SUBTRACT TXN-AMOUNT OF TXN-IN-REC
                              FROM CURR-BAL OF ACCT-IN-REC
                    END-EVALUATE
                 END-IF

                 PERFORM READ-NEXT-TXN
              END-IF
           END-PERFORM.
