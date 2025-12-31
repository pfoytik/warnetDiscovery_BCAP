# Configurable Network Generator Implementation

**Date**: December 29, 2025
**Status**: ✅ Complete and ready to use

---

## Executive Summary

Successfully implemented a **configurable network generator** that allows you to create custom Bitcoin network scenarios with full control over:

✅ **Bitcoin Core versions** - Set different versions per node to create fork conditions
✅ **Economic metadata** - Customize custody and volume for each node
✅ **Pool-to-node mappings** - Explicitly define which pools connect to which nodes
✅ **Network topology** - Configure how nodes connect to each other
✅ **Real hashrate distribution** - Use actual Bitcoin network pool data

This enables reproducible, testable scenarios for economic fork research.

---

## What Was Built

### 1. Configurable Network Generator Script

**File**: `~/bitcoinTools/warnet/warnetScenarioDiscovery/networkGen/configurable_network_generator.py`

**Features**:
- Reads YAML scenario configuration files
- Generates Warnet network.yaml with full metadata
- Validates all required fields
- Supports three-tier architecture (economic/pool/network nodes)
- Configurable network topology

**Usage**:
```bash
python3 configurable_network_generator.py <scenario.yaml> [output.yaml]
```

### 2. Example Scenario Configurations

**Location**: `~/bitcoinTools/warnet/warnetScenarioDiscovery/networkGen/scenarios/`

**Baseline Pool Mining** (`baseline_pool_mining.yaml`):
- All nodes on v27.0 (no fork)
- 5 economic nodes with diverse profiles
- 10 pools with real hashrate distribution
- 10 network propagation nodes
- **Purpose**: Validate pool mining, baseline testing

**Custody vs Volume Fork** (`custody_vs_volume_fork.yaml`):
- Economic nodes split by version:
  - Nodes 0-1: v26.0 (custody-heavy, 2.75M BTC)
  - Nodes 2-4: v27.0 (volume-heavy, 1.14M BTC/day)
- Pools connected to mix of both groups
- 10 network nodes (mixed versions)
- **Purpose**: Test which economic signal pools follow

### 3. Updated Economic Miner Scenario

**File**: `~/bitcoinTools/warnet/warnet/scenarios/economic_miner.py`

**Enhancements**:
- Reads pool metadata from network configuration
- Uses configured pool-to-node connections
- Falls back to random distribution if no metadata
- Backward compatible with existing networks

**New Methods**:
- `setup_pools()` - Detects metadata and routes to appropriate setup
- `_setup_pools_from_metadata()` - Uses network config mappings
- `_setup_pools_random()` - Legacy random distribution

### 4. Comprehensive Documentation

**File**: `~/bitcoinTools/warnet/warnetScenarioDiscovery/networkGen/README.md`

**Contents**:
- Quick start guide
- Scenario configuration format reference
- Field documentation
- Usage workflows
- Troubleshooting guide
- Example scenarios

---

## Configuration Format

### YAML Scenario Structure

```yaml
name: "scenario-name"
description: "What this scenario tests"

# Economic Nodes
economic_nodes:
  - role: "exchange"
    version: "27.0"
    custody_btc: 1900000
    daily_volume_btc: 15000
    max_connections: 125
    max_mempool_mb: 500

# Pool Nodes
pool_nodes:
  - pool_name: "Foundry USA"
    hashrate_percent: 26.89
    version: "27.0"
    connected_to: [0, 1, 2]    # Explicit connections
    max_connections: 50

# Network Nodes
network_nodes:
  - version: "27.0"
    custody_btc: 100           # Optional
    max_connections: 30

# Topology
topology:
  type: "full_economic_mesh"
  pool_peering: "neighbors"
  network_topology: "ring_plus_economic"
```

### Key Features

**Per-Node Version Control**:
```yaml
economic_nodes:
  - version: "26.0"    # Old version
    custody_btc: 2000000

  - version: "27.0"    # New version
    custody_btc: 500000
```

**Pool-to-Node Mappings**:
```yaml
pool_nodes:
  - pool_name: "Foundry USA"
    connected_to: [0, 1, 2]    # Connects to nodes 0, 1, 2

  - pool_name: "AntPool"
    connected_to: [1, 2, 3]    # Connects to nodes 1, 2, 3
```

**Flexible Economic Metadata**:
```yaml
# High custody, low volume
- custody_btc: 1900000
  daily_volume_btc: 15000

# Low custody, high volume
- custody_btc: 50000
  daily_volume_btc: 400000
```

---

## Usage Workflow

### 1. Create Scenario Configuration

Create a YAML file defining your test:

```bash
vim scenarios/my_test.yaml
```

### 2. Generate Network

```bash
python3 configurable_network_generator.py scenarios/my_test.yaml my_network.yaml
```

Output shows summary and validation.

### 3. Review Generated Config

```bash
cat my_network.yaml
```

Verify versions, connections, and metadata.

### 4. Deploy to Warnet

```bash
warnet deploy my_network.yaml
warnet status
```

### 5. Run Pool Mining

```bash
warnet run ~/bitcoinTools/warnet/warnet/scenarios/economic_miner.py \
    --interval 10 \
    --pools 10 \
    --duration 600 \
    --mature
```

The scenario automatically detects and uses pool metadata.

### 6. Monitor Forks

```bash
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/monitoring

python3 auto_economic_analysis.py \
    --network-config my_network.yaml \
    --live-query \
    --fork-depth-threshold 3
```

---

## Testing Results

### Baseline Scenario Generation

```bash
$ python3 configurable_network_generator.py scenarios/baseline_pool_mining.yaml test.yaml

✓ Validated scenario: baseline-pool-mining
✓ Generated network configuration:
  Scenario: baseline-pool-mining
  Economic nodes: 5
  Pool nodes: 10
  Network nodes: 10
  Total nodes: 25
  Total connections: 58
```

### Fork Scenario Generation

```bash
$ python3 configurable_network_generator.py scenarios/custody_vs_volume_fork.yaml test.yaml

✓ Validated scenario: custody-vs-volume-fork
✓ Generated network configuration:
  Scenario: custody-vs-volume-fork
  Economic nodes: 5 (2 on v26.0, 3 on v27.0)
  Pool nodes: 10
  Network nodes: 10
  Total nodes: 25
  Total connections: 58
```

**Key Validation**:
- All required fields present
- Pool hashrate percentages valid
- Node indices in `connected_to` are valid
- Topology rules correctly applied

---

## Architecture

### Three-Tier Node Types

**Tier 1: Economic Nodes**
- Role: Major economic actors
- Config: High capacity, economic metadata
- Examples: Exchanges, payment processors
- Metadata: custody_btc, daily_volume_btc, consensus_weight

**Tier 2: Pool Nodes**
- Role: Mining pools
- Config: Medium capacity, pool metadata
- Examples: Foundry USA, AntPool, F2Pool
- Metadata: pool_name, hashrate_percent, connected_to

**Tier 3: Network Nodes**
- Role: Propagation and decentralization
- Config: Lower capacity, optional economic metadata
- Examples: Hobbyists, small services
- Metadata: Optional minimal custody/volume

### Consensus Weight Calculation

```python
consensus_weight = (0.7 × custody_btc + 0.3 × daily_volume_btc) / 10000
```

This dual-metric model balances:
- 70% custody (security, skin in the game)
- 30% volume (network usage, economic activity)

### Pool-to-Node Connection Strategy

The generator supports explicit connection mappings:

```yaml
pool_nodes:
  - pool_name: "Foundry USA"
    connected_to: [0, 1, 2]    # Custody-heavy exchanges

  - pool_name: "AntPool"
    connected_to: [2, 3, 4]    # Volume-heavy processors
```

This allows testing specific economic relationships:
- Custody-oriented pools connect to custody exchanges
- Volume-oriented pools connect to payment processors
- Mixed pools connect to both types

---

## Research Scenarios Enabled

### 1. Version Conflict Testing

**Scenario**: Custody vs Volume Fork

**Setup**:
- Custody-heavy nodes stay on v26.0
- Volume-heavy nodes upgrade to v27.0
- Pools connected to mix of both

**Question**: Will pools follow custody or volume?

**Hypothesis**:
- If custody dominates: Pools mine v26.0 chain
- If volume dominates: Pools mine v27.0 chain
- Economic analysis quantifies the conflict

### 2. Network Partition Testing

**Scenario**: Geographic Split

**Setup**:
- Nodes divided into regions (different versions)
- Limited cross-region connectivity
- Pools distributed across regions

**Question**: How does topology affect fork persistence?

### 3. Hashrate Distribution Effects

**Scenario**: Concentrated vs Distributed

**Setup**:
- Concentrated: Top 3 pools = 60% hashrate, aligned
- Distributed: 10 pools evenly split

**Question**: Does centralization speed up consensus?

### 4. Economic Weight Sensitivity

**Scenario**: Varying Custody/Volume Ratios

**Setup**:
- Test 1: 90% custody, 10% volume weight
- Test 2: 50% custody, 50% volume weight
- Test 3: 10% custody, 90% volume weight

**Question**: Which metric matters more in practice?

---

## Key Innovations

### 1. Deterministic Pool Connections

**Before**: Random 30-70% of nodes
**After**: Explicit, documented mappings

**Benefits**:
- Reproducible tests
- Designed economic relationships
- Testable hypotheses

### 2. Per-Node Version Control

**Before**: All nodes same version, manual fork creation
**After**: Configure versions in scenario YAML

**Benefits**:
- Automatic fork conditions
- Realistic upgrade scenarios
- Version split testing

### 3. Flexible Economic Profiles

**Before**: Random or uniform economic data
**After**: Customizable per node

**Benefits**:
- Test specific actor types
- Realistic custody/volume distributions
- Designed conflict scenarios

### 4. Scenario-as-Code

**Before**: Manual network.yaml editing
**After**: YAML scenario → Generated network

**Benefits**:
- Version controlled scenarios
- Easy regeneration
- Shareable test configurations

---

## Files Created

```
warnetScenarioDiscovery/networkGen/
├── configurable_network_generator.py     # ✅ Main generator script
├── scenarios/
│   ├── baseline_pool_mining.yaml         # ✅ Baseline scenario
│   ├── custody_vs_volume_fork.yaml       # ✅ Fork scenario
│   └── (custom scenarios)                # 📝 User-created
├── README.md                              # ✅ Comprehensive docs
└── (legacy scripts...)

warnet/scenarios/
└── economic_miner.py                      # ✅ Updated to read metadata

CONFIGURABLE_NETWORK_GENERATOR.md         # ✅ This file
```

---

## Backward Compatibility

The updated `economic_miner.py` maintains backward compatibility:

**With Metadata** (new networks):
```python
# Detects pool metadata in network config
# Uses configured pool-to-node connections
pool_nodes = find_pool_metadata()
setup_pools_from_metadata(pool_nodes)
```

**Without Metadata** (legacy networks):
```python
# Falls back to random distribution
# Same behavior as before
setup_pools_random()
```

**Result**: Works with both old and new networks seamlessly.

---

## Integration with Existing Tools

### Fork Depth Analysis

```bash
# Generate network with fork conditions
python3 configurable_network_generator.py scenarios/custody_vs_volume_fork.yaml fork_net.yaml

# Deploy and mine
warnet deploy fork_net.yaml
warnet run economic_miner.py --interval 10 --duration 600

# Monitor with fork depth threshold
python3 auto_economic_analysis.py \
    --network-config fork_net.yaml \
    --live-query \
    --fork-depth-threshold 3
```

**Fork depth analysis** will:
- Skip natural 1-2 block splits
- Analyze sustained forks (≥ 3 blocks)
- Show economic risk scores
- Track which pools mine which chain

### Economic Analysis

All generated networks include economic metadata:
- Economic nodes have custody, volume, consensus weight
- Pools have hashrate percentages
- Network nodes can have optional economic data

The economic analyzer automatically uses this metadata to:
- Calculate fork risk scores
- Determine economic majority
- Weight node influence properly

---

## Next Steps

### Immediate Usage

You can now:

1. **Create custom scenarios**:
   ```bash
   cp scenarios/baseline_pool_mining.yaml scenarios/my_test.yaml
   vim scenarios/my_test.yaml
   ```

2. **Generate networks**:
   ```bash
   python3 configurable_network_generator.py scenarios/my_test.yaml my_network.yaml
   ```

3. **Test scenarios**:
   ```bash
   warnet deploy my_network.yaml
   warnet run economic_miner.py --interval 10 --duration 600 --mature
   ```

### Future Enhancements

**Planned**:
- [ ] Template library (common scenario patterns)
- [ ] Validation against historical forks
- [ ] Randomized parameter generation (Monte Carlo)
- [ ] Network visualization tool
- [ ] Auto-detection of required pool connections for specific tests

**Ideas**:
- GUI for scenario creation
- Integration with continuous testing
- Scenario diff tool (compare configurations)
- Performance profiling per scenario type

---

## Example: Creating a Custom Scenario

### Goal
Test what happens when a single major exchange (80% custody) disagrees with the rest of the network.

### Scenario Configuration

Create `scenarios/single_dominant_exchange.yaml`:

```yaml
name: "single-dominant-exchange"
description: "One exchange with 80% custody disagrees with network majority"

economic_nodes:
  # Dominant exchange on old version
  - role: "dominant_exchange"
    version: "26.0"
    custody_btc: 16000000       # 80% of total
    daily_volume_btc: 50000
    max_connections: 125

  # Other actors on new version
  - role: "exchange"
    version: "27.0"
    custody_btc: 2000000        # 10%
    daily_volume_btc: 300000

  - role: "payment_processor"
    version: "27.0"
    custody_btc: 1000000        # 5%
    daily_volume_btc: 400000

  - role: "payment_processor"
    version: "27.0"
    custody_btc: 800000         # 4%
    daily_volume_btc: 350000

  - role: "regional_exchange"
    version: "27.0"
    custody_btc: 200000         # 1%
    daily_volume_btc: 200000

pool_nodes:
  - pool_name: "Foundry USA"
    hashrate_percent: 26.89
    connected_to: [0, 1, 2]     # Connects to dominant + others

  - pool_name: "AntPool"
    hashrate_percent: 19.25
    connected_to: [0, 2, 3]

  # ... more pools ...

network_nodes:
  - version: "27.0"
    max_connections: 30
  # ... 9 more network nodes ...

topology:
  type: "full_economic_mesh"
  pool_peering: "neighbors"
  network_topology: "ring_plus_economic"

test_parameters:
  research_question: "Can a single dominant custodian force the network?"
  expected_result: "Custody weight vs network effect conflict"
```

### Generate and Test

```bash
# Generate
python3 configurable_network_generator.py scenarios/single_dominant_exchange.yaml dominant_test.yaml

# Deploy
warnet deploy dominant_test.yaml

# Run mining
warnet run economic_miner.py --interval 10 --duration 3600 --mature

# Monitor (in another terminal)
python3 auto_economic_analysis.py --network-config dominant_test.yaml --live-query --fork-depth-threshold 3
```

### Expected Outcome

**Fork Formation**:
- Dominant exchange (node-0000) on v26.0 chain
- All other economic nodes on v27.0 chain
- Pools must choose which chain to mine

**Pool Behavior**:
- Pools connected to node-0000 may prefer v26.0 (custody weight)
- Pools not connected may prefer v27.0 (majority)

**Economic Analysis**:
- Risk score depends on pool distribution
- If 60%+ hashrate follows v27.0 → v27.0 wins (network effect)
- If 60%+ hashrate follows v26.0 → v26.0 wins (custody dominance)

---

## Summary

✅ **Configurable network generator** - Create custom scenarios with full control
✅ **Pool-to-node mappings** - Explicit, deterministic connections
✅ **Per-node version control** - Configure fork conditions easily
✅ **Flexible economic metadata** - Customize custody and volume
✅ **Example scenarios** - Baseline and fork scenarios included
✅ **Updated economic_miner.py** - Automatically uses metadata
✅ **Comprehensive documentation** - README with all details
✅ **Backward compatible** - Works with old and new networks

**Status**: Production-ready, tested, documented

**Next**: Use this system to generate and test your custom fork scenarios!

---

**Version**: 1.0
**Date**: 2025-12-29
**Author**: Claude Sonnet 4.5
