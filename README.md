# Real-Time Card Fraud Velocity Monitoring and Risk Scoring with Redis

This project demonstrates how Redis can be used in a real-time card fraud monitoring and risk scoring scenario.

The system stores card/customer profiles, transaction events, risk scores, suspicious card lists, recent transactions, and short-term velocity counters using different Redis data structures.

The main goal of the project is not only to store data, but also to show how Redis can support real-time decision-making by combining Hash, Sorted Set, Stream, List, Set, and TTL-based keys.

---

## Project Scenario

In this project, a simplified banking fraud monitoring scenario is implemented.

A bank receives card transactions and tries to detect suspicious behavior in real time. For example, if a card normally used in Istanbul suddenly receives multiple e-commerce transactions from Berlin, the system increases the card's risk score.

If the total risk score exceeds a certain threshold, the card is added to the suspicious card watchlist and its status is updated to `under_review`.

This is a demo project and does not represent a real banking fraud detection model.

---

## Selected NoSQL Database

The selected NoSQL database is **Redis**.

Redis is a key-value based NoSQL database. However, it also supports multiple advanced data structures such as:

- Hash
- Set
- Sorted Set
- List
- Stream
- TTL-based temporary keys

These features make Redis suitable for real-time analytics, fast counter updates, event streams, temporary data tracking, and leaderboard-style ranking systems.

---

## Why Redis?

Redis was selected because fraud monitoring systems require fast reads, fast updates, and real-time tracking.

When a card transaction arrives, the system needs to quickly answer questions such as:

- What is the card/customer profile?
- What is the current risk score?
- How many transactions happened in a short time window?
- Is the card among the riskiest cards?
- Is the card already in the suspicious watchlist?
- What are the latest transactions of the card?

In a relational database, these operations may require multiple tables, joins, counters, and ordering queries.

In Redis, these access patterns can be modeled directly using specific data structures. For example, risk scores can be stored in a Sorted Set, allowing the system to retrieve the riskiest cards efficiently.

---

## Redis Data Model

| Data Need | Redis Data Structure | Example Key |
|---|---|---|
| Card/customer profile | Hash | `card:1001` |
| Risk scores | Sorted Set | `risk_scores` |
| Transaction events | Stream | `transactions:stream` |
| Recent card transactions | List | `recent_tx:1007` |
| Suspicious cards | Set | `suspicious_cards` |
| Short-term velocity tracking | String + TTL | `velocity:1007` |
| City-based grouping | Set | `city:Istanbul` |
| Segment-based grouping | Set | `segment:Premium` |

The data model is designed according to application access patterns instead of relational table normalization.

---

## Redis Data Structures Used

### Hash

Card and customer profiles are stored as Redis Hashes.

Example:

```redis
HSET card:1001 name "Nehir Tiras" segment "Retail" city "Istanbul" status "active" limit 50000
```

Read example:

```redis
HGETALL card:1001
```

---

### Sorted Set

Risk scores are stored in a Redis Sorted Set.

This allows the system to rank cards by risk score.

Example:

```redis
ZADD risk_scores 15 card:1001
```

Increase risk score:

```redis
ZINCRBY risk_scores 35 card:1003
```

Get top risky cards:

```redis
ZREVRANGE risk_scores 0 4 WITHSCORES
```

---

### Stream

Transaction events are stored in a Redis Stream.

Example:

```redis
XADD transactions:stream * card_id 1007 amount 9900 merchant "Online Gaming" city "Berlin" country "DE" channel "ECOM"
```

Read latest events:

```redis
XREVRANGE transactions:stream + - COUNT 5
```

---

### List

Recent transactions of each card are stored in Redis Lists.

Example:

```redis
LPUSH recent_tx:1007 "9900 | Online Gaming | Berlin | DE | ECOM"
```

Read recent transactions:

```redis
LRANGE recent_tx:1007 0 4
```

---

### Set

Suspicious cards and grouping structures are stored using Redis Sets.

Example:

```redis
SADD suspicious_cards card:1007
```

City and segment grouping:

```redis
SADD city:Istanbul card:1001 card:1005 card:1007
SADD segment:Premium card:1003 card:1007
```

Intersection query:

```redis
SINTER city:Istanbul segment:Premium
```

---

### TTL-Based Velocity Counter

Short-term transaction velocity is tracked using `INCR`, `EXPIRE`, and `TTL`.

Example:

```redis
INCR velocity:1007
EXPIRE velocity:1007 60
TTL velocity:1007
```

This structure is used to represent how many transactions occurred in the last 60 seconds.

---

## Risk Scoring Logic

The project uses a simplified demo risk scoring model.

| Risk Rule | Added Score |
|---|---|
| Transaction amount is greater than 10% of card limit | +20 |
| Transaction is from a foreign country | +25 |
| Transaction city differs from card's normal city | +15 |
| Transaction channel is e-commerce | +10 |
| Card has 3 or more transactions in a short time window | +30 |

If the total risk score becomes high enough, the card is added to the `suspicious_cards` set and its status is updated to `under_review`.

---

## CRUD Operations

The project demonstrates basic CRUD operations using Redis commands.

### Insert

```redis
HSET card:1001 name "Nehir Tiras" segment "Retail" city "Istanbul" status "active" limit 50000
ZADD risk_scores 15 card:1001
XADD transactions:stream * card_id 1001 amount 1250 merchant "Electronics Store" city "Istanbul" country "TR" channel "POS"
```

### Read

```redis
HGETALL card:1001
ZSCORE risk_scores card:1001
```

### Update

```redis
ZINCRBY risk_scores 35 card:1003
HSET card:1003 status "under_review"
SADD suspicious_cards card:1003
```

### Delete

```redis
SREM suspicious_cards card:1003
DEL velocity:1003
```

---

## Advanced Queries

### 1. Top 5 Risky Cards

```redis
ZREVRANGE risk_scores 0 4 WITHSCORES
```

This query returns the top 5 cards with the highest risk scores.

### 2. Risk Rank of a Specific Card

```redis
ZREVRANK risk_scores card:1007
ZSCORE risk_scores card:1007
```

This shows the rank and score of a specific card in the risk leaderboard.

### 3. Latest Transaction Events

```redis
XREVRANGE transactions:stream + - COUNT 5
```

This query reads the latest transaction events from the Redis Stream.

### 4. City and Segment Intersection

```redis
SINTER city:Istanbul segment:Premium
```

This returns cards that are both located in Istanbul and belong to the Premium segment.

---

## Innovation Feature

In addition to the static CRUD and query demo, the project includes a live fraud monitor simulation.

The `live_monitor.py` file generates new transaction events at regular intervals. For each transaction, the system:

- Writes the event to Redis Stream
- Updates the velocity counter
- Calculates risk reasons
- Updates the risk score
- Refreshes the real-time risk leaderboard
- Adds high-risk cards to the suspicious watchlist

This feature demonstrates real-time functionality using Redis Stream, Sorted Set, and TTL-based counters together.

---

## Project Files

```text
bonus_redis_fraud_monitor/
├── docker-compose.yml
├── requirements.txt
├── demo.py
├── live_monitor.py
├── commands.redis
└── README.md
```

| File | Description |
|---|---|
| `docker-compose.yml` | Starts the Redis container with Docker |
| `requirements.txt` | Contains the Python Redis dependency |
| `demo.py` | Main demo file for data loading, CRUD operations, and advanced queries |
| `live_monitor.py` | Real-time fraud monitor simulation |
| `commands.redis` | Manual Redis CLI commands |
| `README.md` | Project documentation |

---

## How to Run the Project

### 1. Start Redis with Docker

```bash
docker compose up -d
```

Check if the Redis container is running:

```bash
docker ps
```

Open Redis CLI:

```bash
docker exec -it bonus-redis redis-cli
```

Test Redis:

```redis
PING
```

Expected output:

```redis
PONG
```

---

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

### 3. Run the Main Demo

```bash
python demo.py
```

This script:

- Connects to Redis
- Clears old data
- Loads 20 card/customer records
- Inserts transaction events
- Calculates risk scores
- Detects suspicious cards
- Demonstrates CRUD operations
- Runs advanced queries

---

### 4. Run the Live Fraud Monitor

```bash
python live_monitor.py
```

This script generates transaction events in real time and updates the risk leaderboard dynamically.

---

### 5. Run Redis CLI Commands on PowerShell

```powershell
Get-Content .\commands.redis | Where-Object { $_.Trim() -ne "" -and -not $_.Trim().StartsWith("#") } | docker exec -i bonus-redis redis-cli
```

---

## SQL vs Redis Comparison

In a relational database approach, the system would likely require tables such as:

- Customers
- Cards
- Transactions
- RiskScores
- SuspiciousCards

This could require joins, ordering queries, and additional logic for counters.

In Redis, the model is designed around fast access patterns:

- Hash for card profiles
- Sorted Set for risk ranking
- Stream for transaction events
- List for recent transactions
- Set for suspicious cards
- TTL keys for temporary velocity tracking

This makes Redis suitable for real-time risk tracking and fast leaderboard-style queries.

---

## Conclusion

This project demonstrates how Redis can be used for a real-time fraud monitoring scenario.

The project includes:

- 20 card/customer records
- Redis Hash, Sorted Set, Stream, List, Set, and TTL usage
- CRUD operations
- Multiple advanced queries
- Real-time fraud monitor simulation
- SQL vs NoSQL data modeling comparison

Redis is especially useful in scenarios that require fast reads, fast updates, real-time counters, leaderboard ranking, event streams, and temporary key expiration.
