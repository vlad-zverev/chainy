# PyCoin

Simple naive decentralized crypto blockchain

TODO:
- completely switch to sqlalchemy models Block and Transaction containing Blockhain
- return transaction hash to the user for /send request
- improve scalability (paging /blocks requests, analyze only last blocks (N?) to check validity of neighboring node)
- add completely block validation by every node to prevent processing invalid transactions
- integration tests for miner-hacker with attempts to process fraudulent transactions
- extend checks for malicious injections in lock-scripts (interrupt if execution longer than X millisec)
- research ways to lower impact of permanent executing lock-scripts
- CI/CD
- UI
