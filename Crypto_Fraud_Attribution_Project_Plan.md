# Project Plan: Crypto Fraud Attribution System

**Problem Statement ID:** SIH26183
**Problem Statement Title:** Real-Time Identification of Fraud-Linked Cryptocurrency Exchanges from Victim-Reported Suspect Wallet Addresses through Automated Blockchain Analytics
**Theme:** Cybersecurity / Blockchain
**PS Category:** Software
**Team ID:** 26183
**Team Name:** NEXUS

---

## 1. Problem Statement

Victims of cryptocurrency fraud typically have only a suspect wallet address or a
transaction hash to report. Manually tracing how stolen funds move across wallets,
identifying which exchange ultimately received them, and building investigation
evidence is slow, manual, and doesn't scale with the volume of crypto-fraud
complaints (e.g. via NCRP/SAHYOG). This project automates that entire pipeline.

## 2. Objective

Build a platform that, given a victim-reported wallet address or transaction hash:
1. Automatically traces stolen cryptocurrency across multiple connected wallets.
2. Detects fraud patterns (rapid transfers, wallet hopping, fund splitting/layering).
3. Identifies the exchange/VASP wallet(s) where funds were ultimately deposited.
4. Generates an explainable risk score and an automated investigation report,
   reducing manual blockchain-tracing effort for investigators.

## 3. Solution Summary

The system ingests a suspect wallet address, retrieves its on-chain transaction
history, and performs a multi-hop breadth-first trace of outgoing fund movements.
Each wallet touched is checked against a known exchange/VASP address database,
and the whole traced network is scored using a set of explainable fraud-pattern
rules (rapid pass-through, fund splitting, layering depth, exchange convergence,
network size). Results are shown on an investigator dashboard as a fund-flow
graph, a risk score, and a downloadable investigation report.

## 4. Core Modules

| Module | Function |
|---|---|
| **Achievements Repository** | Stores reported fraud cases, suspect wallets, transaction details, and past investigation reports for future reference |
| **Multi-Level Blockchain Analysis** | Retrieves transactions (amount, time, hash, wallet) and maps connected wallets |
| **Fraud Risk Detection** | Detects rapid transfers, multiple wallet hops, and fund splitting; generates an explainable Low/Medium/High risk score |
| **Exchange Identification** | Matches traced wallets against known exchange/VASP addresses |
| **Visual Investigation Dashboard** | Shows fund flow between wallets, transactions, and suspicious activity in one place |
| **Automated Investigation Report** | Generates a report with wallet, fund-flow, transaction, and risk details |

## 5. Unique Value Proposition

- **Automated Blockchain Fund Tracing** — automatically traces stolen crypto across
  multiple wallets and visualizes the fund movement from the suspect wallet onward.
- **Exchange Destination Matching** — analyzes suspicious transactions and matches
  wallet addresses against known exchanges to identify likely fund destinations.
- **Clear Fund-Flow Visualization** — a single dashboard showing transaction details,
  wallet connections, and risk information together, instead of scattered manual lookups.

---

## 6. Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React.js, Tailwind CSS, React Flow, Cytoscape.js |
| **Backend** | Python, FastAPI, REST API |
| **Blockchain / Web3** | Ethereum, BNB Chain, Polygon, Bitcoin, Chainlink, Alchemy (blockchain APIs / indexers) |
| **Database** | PostgreSQL (transactions, users, cases), Neo4j (wallet relationship graph), Redis (cache — sessions, real-time data) |
| **AI / ML** | Python, scikit-learn, pandas, NetworkX (graph analysis) |
| **Visualization** | React Flow, Cytoscape.js, Chart.js, D3.js, ECharts |
| **Deployment** | Docker, Google Cloud (or AWS), Nginx, GitHub |

### Prototype-stage stack (what's actually built and running today)

| Layer | Technology used in the working prototype |
|---|---|
| Frontend | Plain HTML/CSS/JS + vis-network.js (no build step, instantly runnable) |
| Backend | Python, FastAPI |
| Blockchain data | Etherscan API (live mode) + bundled sample dataset (demo mode) |
| Graph engine | NetworkX (multi-hop BFS fund-flow graph) |
| Risk scoring | Explainable rule-based scorer (stand-in for the trained scikit-learn model, pending labeled case data) |
| Exchange DB | Seed JSON file of known exchange wallet addresses |
| Storage | In-memory (per session) — placeholder for PostgreSQL / Neo4j |
| Deployment | Docker + docker-compose |

This two-row table matters for your presentation: the top table is the target
production stack from your architecture diagram; the bottom is what's demoable
right now. Being explicit about the gap (real DB, live multi-chain, trained ML
model) reads as engineering maturity to judges, not a weakness.

---

## 7. System Architecture (8 Layers)

1. **Input Layer** — Cybercrime officer / investigator submits a victim-reported wallet address via a complaint portal (SAHYOG / NCRP) or directly.
2. **Blockchain Data Layer** — Fetches transactions, blocks, and token transfers from Ethereum, BNB Chain, Polygon, Bitcoin, and other chains.
3. **External Data Sources** — Known exchange/VASP wallet database, sanctioned/illicit address lists, threat intelligence sources.
4. **Processing & Analytics Engine**
   - 4.1 Data Ingestion — fetch transactions, blocks, token transfers
   - 4.2 Data Processing — clean, normalize, enrich data
   - 4.3 Transaction Graph Builder — build wallet relationship graph
   - 4.4 Fund Flow Analysis — trace multi-hop fund movement
   - 4.5 Intermediary Detection — detect layering, mixers, burners
   - 4.6 Cross-Chain Tracker — track funds across chains and bridges
5. **VASP / Exchange Identification** — match destination wallets with known exchange/VASP clusters
6. **AI/ML Risk Scoring** — model suspicious patterns (transaction behavior, wallet age/activity, fund movement speed, exchange activity, cross-chain activity) → risk score 0–100
7. **Results & Output** — investigator dashboard (fund-flow visualization), automated investigation report (PDF/CSV/JSON), alerts & notifications for high-risk/exchange detected
8. **Data Storage Layer** — PostgreSQL (transactions, users, cases), Neo4j (wallet relationship graph), object storage (reports, logs, documents), Redis cache (sessions, real-time data)

---

## 8. Development Plan / Phases

| Phase | Deliverable | Status |
|---|---|---|
| **Phase 1 — Problem Analysis & Architecture** | Finalize problem scope, architecture diagram, tech stack | ✅ Done |
| **Phase 2 — Core Prototype** | Wallet-address input, blockchain transaction retrieval, transaction graph construction, fund-flow tracing, VASP identification, risk-scoring module | ✅ Done (single-chain Ethereum, demo + live mode) |
| **Phase 3 — Investigator Dashboard** | Fund-flow visualization, risk score panel, exchange destination panel, automated report generation | ✅ Done (basic dashboard) |
| **Phase 4 — Persistence Layer** | Move from in-memory case storage to PostgreSQL (case metadata) + Neo4j (wallet graph) | ⏳ Planned |
| **Phase 5 — Multi-Chain Support** | Add BNB Chain, Polygon, Bitcoin data adapters; cross-chain/bridge tracking | ⏳ Planned |
| **Phase 6 — ML Risk Model** | Train a scikit-learn classifier on labeled historical fraud cases, replacing/augmenting the rule-based scorer | ⏳ Planned |
| **Phase 7 — Admin & Victim Dashboards** | Separate role-based dashboards, case management, multilingual support | ⏳ Planned |
| **Phase 8 — Deployment & Hardening** | Dockerized deployment on Google Cloud/AWS, Nginx reverse proxy, authentication, rate limiting, alerting | ⏳ Planned |

---

## 9. Feasibility & Viability

**Feasibility**
- *Technical:* Uses public blockchain APIs, automated transaction analysis, wallet tracing, and web-based visualization — all achievable with open-source tools.
- *Operational:* Simple interface for investigators to submit a wallet address or transaction hash and get an analyzed case.
- *Financial:* Built on open-source technologies and free-tier blockchain APIs, keeping development and deployment costs low.
- *Scalability:* Modular service design (separate data-fetch, graph, risk, and exchange-matching services) allows adding chains, wallets, and exchange databases without rearchitecting.

**Viability**
- *For victims:* Report crypto fraud with just a wallet address or transaction hash and track where stolen funds moved.
- *For investigators:* Automates blockchain analysis, flags suspicious wallets, and produces ready-to-use investigation evidence.
- *For sustainability:* Can expand to more cryptocurrencies, blockchains, and continuously updated exchange-address databases.

---

## 10. Impact & Benefits

**Law Enforcement:** faster cyber-fraud investigations, automated transaction tracing, improved digital evidence collection.
**Financial / VASP:** faster identification of receiving VASPs, improved coordination with exchanges, supports timely fund preservation/freezing requests.
**Technological:** real-time blockchain analytics, multi-chain transaction analysis, AI/ML-based risk scoring.

**Benefits:**
- Faster investigation (automated tracing vs. manual wallet-by-wallet lookup)
- Faster fund freezing (early VASP identification)
- Better evidence (transaction timelines, wallet relationship graphs, standardized reports)
- Multi-chain analysis (cross-chain/bridge fund tracking)
- Fraud pattern detection (rapid transfers, layering, burner wallets)
- Centralized investigation (one dashboard for wallet analysis, risk scores, graphs, case info)
- Real-time alerts on high-risk wallet activity
- Reduced investigator workload through automated repetitive analysis

**Future Model:** A National Crypto Fraud Intelligence Network — a unified platform
with advanced cross-chain intelligence (additional blockchains, bridges, DeFi
protocols) and AI-powered fraud detection trained on historical investigation data
to identify emerging fraud typologies and wallet networks.

---

## 11. Research & Benchmarking

**Reference areas researched:** blockchain fraud detection, transaction network
analysis, ML-based fraud pattern detection, blockchain fund tracing, exchange
address identification.

**Existing (manual) approach vs. proposed (automated) approach:**

| Capability | Existing approach | Proposed system |
|---|---|---|
| Fraud Detection | Manual analysis | Automated analysis |
| Fund Tracing | Limited, single-hop | Multi-wallet tracing |
| Risk Detection | Basic/manual judgment | Automated, explainable risk scoring |
| Exchange Identification | Manual checking | Known-address matching |
| Investigation Report | Manual compilation | Automated report generation |
| Visualization | Limited / spreadsheet-based | Interactive fund-flow graph |

**Reference tools/resources:** Ethereum documentation, Etherscan (blockchain
explorer), Chainalysis and Elliptic (commercial blockchain analytics platforms
used as benchmarks for the exchange-identification and risk-scoring approach).

---

## 12. Team Roles (suggested split for Team NEXUS)

| Role | Responsibility |
|---|---|
| Backend/Blockchain Engineer | Blockchain data layer, transaction graph builder, fund-flow tracing service |
| Data/ML Engineer | Risk-scoring logic, feature design, eventual ML model training |
| Frontend Engineer | Investigator dashboard, fund-flow visualization, report UI |
| DevOps | Docker/deployment, database setup (PostgreSQL/Neo4j/Redis), CI |
| Research/Documentation | Exchange address database curation, competitive benchmarking, report/documentation, presentation |

---

## 13. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Free-tier blockchain API rate limits | Cache results in Redis; cap transactions fetched per address; batch requests |
| Known-exchange address database incompleteness | Start with a curated seed list; plan integration with a commercial/community-maintained VASP address feed (e.g. Chainalysis/Elliptic-style labels) |
| False positives in rule-based risk scoring | Keep the scorer explainable (reasons list) so investigators can judge each flag; refine thresholds against real case data before trusting scores blindly |
| Cross-chain tracing complexity | Scope Phase 1 to a single chain (Ethereum); add chains incrementally behind the same graph-builder interface |
| Data privacy / sensitive case data | Store case data behind authentication; avoid exposing victim-identifying details in shared dashboards |

---

## 14. Deliverables Checklist

- [x] Problem statement analysis and architecture diagram
- [x] Working prototype: wallet input → transaction fetch → fund-flow graph → risk score → exchange match → report
- [x] Investigator dashboard (fund-flow graph, risk panel, exchange panel, report download)
- [ ] Persistent storage (PostgreSQL + Neo4j)
- [ ] Multi-chain support (BNB Chain, Polygon, Bitcoin)
- [ ] Trained ML risk model
- [ ] Admin & victim role-based dashboards
- [ ] Production deployment (Docker + cloud + Nginx)
- [ ] Final presentation deck and demo video
