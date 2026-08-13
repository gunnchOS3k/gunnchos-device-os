# Factory / RMA / support digital operational model

**Status:** DIGITAL_PREPARATION · DEV/TEST only  
**PRODUCTION_RELEASE_CLAIMED:** false  
**Commercial warranty:** EXTERNAL  
**Cursor merges:** false

This packet implements software workflows for factory identity, support/RMA,
supply-chain *fields*, and first-use. It does not run a factory, buy parts,
issue production certs, or stand behind a warranty.

## Real (digital)

| Area | What exists |
| --- | --- |
| Factory | DEVTEST serials, locally-administered MAC pool, dummy key *interface*, device-cert *request* (CSR, unsigned by any CA), eSIM *interface* (`EXTERNAL_PENDING`), calibration + test-result import, flash refuse-on-fail, device record export, repair/rework, factory secure-wipe of the digital record |
| Support | Diagnostic bundle (redacted), fault-code catalog, RMA state machine, service history, repair mode, backup/replacement transfer, digital wipe, spares *mapping* (part IDs only), update-support/EOL metadata |
| First-use | Language, a11y, network, offline continuation, privacy, AI choice, Ring *software* pair request, dock *digital* scan, update defer-when-offline, recovery help, student profile |
| Supply chain | Machine-readable BOM/AVL/alternate/sole-source/NRND-EOL/lead-time/MOQ *fields*; unknown stays `UNKNOWN` |

## EXTERNAL / PHYSICAL (not claimed)

- Production keys, production CA issuance, HSM key ceremony
- Carrier eSIM credentials
- RFQ, purchase, fab, physical factory line
- Physical media sanitize / NAND secure erase
- Commercial warranty / SLA / depot logistics
- Quoted stock, price, real lead-time, real MOQ
- Physical Ring pairing and physical dock discovery

## OPEN

- Human/EXTERNAL CA and HSM ceremony
- Carrier eSIM contract
- CM/factory bring-up
- Warranty legal terms
- Supplier AVL quotes
- Independent verification of this STREAM
- Edmund merge (Cursor never merges)
