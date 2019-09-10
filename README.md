# ravencoin-supply-chain-sim
A supply chain simulation to exercise memos feature on testnet.  


## Setup:
 ```pip3 install python-bitcoinrpc```
 


## Glossary:
Bill of Lading (BoL) - A transferrable document which indicates goods have been loaded, and acts as a conclusive receipt.   

Token - The RVN token represents the goods.  Upon issuance, a description of the goods can be linked in the metadata.  The QTY of tokens represents the qty of goods in the smallest shippable unit.  This might be a box, a carton, a bottle, a gross, a ton, etc.  

Memo - A memo is the name used by Ravencoin for IPFS messages recorded with each transfer.  The memo is used to record information about the transit.  Each memo appends to the previous, building a chain (supply chain), as the goods are transferred.  

Split Shipment - For purposes of this simulation, this is when a larger shipment is broken into two or more shipments.  The qty for a split shipment is handled the on-chain accounting.  The memo data will record different shipping tracking numbers.  

Single Shipment - For purposes of this simulation, this is just sending the shipment to a new location, or potentially changing carriers, but the entire shipment is tranferred.  It might be an entire shipping container from a ship to a truck as an example.  

Carrier - A shipper like FedEx, UPS, etc.

Tracking Number - A unique identifier for the shipment.  The txid could be used as a tracking number.

Audit - A separate script can use the public blockchain to build an audit trail that shows qty, and its chain of custody.

End Point - The final shipping location to the purchaser.  The end of the supply chain.

