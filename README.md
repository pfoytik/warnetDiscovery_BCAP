# warnetDiscovery_BCAP
## Abstract
The Bitcoin network operates as a distributed system of heterogeneous nodes exhibiting substantial variation in software versions, configuration parameters, resource availability, and operational policies. While the protocol's consensus mechanisms have been rigorously analyzed in theoretical contexts, the emergent behaviors arising from realistic node configuration diversity—particularly during protocol upgrade transitions—remain inadequately characterized through empirical testing. This gap is particularly concerning given that configuration heterogeneity, while necessary for decentralization, may create unforeseen interactions that compromise network stability, security, or performance, especially during the vulnerable periods of soft fork activation and deployment.
We present a systematic framework for the continuous discovery and characterization of critical scenarios in heterogeneous Bitcoin networks through controlled configuration variation testing. Our methodology employs the Warnet testing environment to conduct reproducible experiments across a multi-dimensional parameter space encompassing Bitcoin Core version distributions, memory pool configurations, network policy settings, validation rules, resource constraints, and critically, economic node topology patterns during protocol upgrades.

Uses: 
- Warnet repo: https://github.com/bitcoin-dev-project/warnet
- warnetScenarioDiscovery repo: https://github.com/pfoytik/warnetScenarioDiscovery
- BCAP repo: https://github.com/bitcoin-cap/bcap
