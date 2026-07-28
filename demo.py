import time
import redis

r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)


#SAMPLE DATA
cards = [
    {"id": "1001", "name": "Nehir Tiras", "segment": "Retail", "city": "Istanbul", "limit": 50000},
    {"id": "1002", "name": "Pinar Yilmaz", "segment": "Retail", "city": "Ankara", "limit": 40000},
    {"id": "1003", "name": "Mert Kaya", "segment": "Premium", "city": "Izmir", "limit": 100000},
    {"id": "1004", "name": "Elif Demir", "segment": "Retail", "city": "Bursa", "limit": 30000},
    {"id": "1005", "name": "Can Aydin", "segment": "Corporate", "city": "Istanbul", "limit": 200000},
    {"id": "1006", "name": "Ayse Arslan", "segment": "Retail", "city": "Antalya", "limit": 35000},
    {"id": "1007", "name": "Mehmet Celik", "segment": "Premium", "city": "Istanbul", "limit": 120000},
    {"id": "1008", "name": "Zeynep Aksoy", "segment": "Retail", "city": "Eskisehir", "limit": 25000},
    {"id": "1009", "name": "Kerem Sahin", "segment": "Corporate", "city": "Ankara", "limit": 250000},
    {"id": "1010", "name": "Selin Ozturk", "segment": "Premium", "city": "Izmir", "limit": 90000},
    {"id": "1011", "name": "Burak Koc", "segment": "Retail", "city": "Istanbul", "limit": 45000},
    {"id": "1012", "name": "Derya Yildiz", "segment": "Retail", "city": "Konya", "limit": 22000},
    {"id": "1013", "name": "Emre Kaplan", "segment": "Premium", "city": "Ankara", "limit": 110000},
    {"id": "1014", "name": "Ece Polat", "segment": "Retail", "city": "Adana", "limit": 28000},
    {"id": "1015", "name": "Ozan Kurt", "segment": "Corporate", "city": "Istanbul", "limit": 300000},
    {"id": "1016", "name": "Buse Ergin", "segment": "Retail", "city": "Trabzon", "limit": 24000},
    {"id": "1017", "name": "Ali Dogan", "segment": "Premium", "city": "Bursa", "limit": 95000},
    {"id": "1018", "name": "Nazli Gunes", "segment": "Retail", "city": "Istanbul", "limit": 32000},
    {"id": "1019", "name": "Tolga Eren", "segment": "Corporate", "city": "Izmir", "limit": 180000},
    {"id": "1020", "name": "Yagmur Tas", "segment": "Retail", "city": "Ankara", "limit": 26000},
]


transactions = [
    {"card_id": "1001", "amount": 1250, "merchant": "Electronics Store", "city": "Istanbul", "country": "TR", "channel": "POS"},
    {"card_id": "1003", "amount": 8500, "merchant": "Luxury Hotel", "city": "Dubai", "country": "AE", "channel": "ECOM"},
    {"card_id": "1005", "amount": 30000, "merchant": "B2B Supplier", "city": "Istanbul", "country": "TR", "channel": "POS"},
    {"card_id": "1007", "amount": 9900, "merchant": "Online Gaming", "city": "Berlin", "country": "DE", "channel": "ECOM"},
    {"card_id": "1007", "amount": 2500, "merchant": "Streaming Service", "city": "Berlin", "country": "DE", "channel": "ECOM"},
    {"card_id": "1007", "amount": 1500, "merchant": "Digital Wallet", "city": "Berlin", "country": "DE", "channel": "ECOM"},
    {"card_id": "1013", "amount": 7200, "merchant": "Airline", "city": "Paris", "country": "FR", "channel": "ECOM"},
    {"card_id": "1015", "amount": 45000, "merchant": "IT Equipment", "city": "Istanbul", "country": "TR", "channel": "POS"},
    {"card_id": "1019", "amount": 25000, "merchant": "Wholesale Market", "city": "Izmir", "country": "TR", "channel": "POS"},
    {"card_id": "1012", "amount": 300, "merchant": "Grocery", "city": "Konya", "country": "TR", "channel": "POS"},
]


#HELPER FUNCTIONS
def print_title(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def calculate_risk_score(card, tx, velocity_count):
    """
    Simple fraud risk scoring logic.
    This is not a real banking model; it is a demo model for the project.
    """

    score = 0

    # High amount compared to card limit
    if tx["amount"] > card["limit"] * 0.10:
        score += 20

    # Foreign transaction
    if tx["country"] != "TR":
        score += 25

    # City mismatch
    if tx["city"] != card["city"]:
        score += 15

    # E-commerce transaction
    if tx["channel"] == "ECOM":
        score += 10

    # Too many transactions in a short time
    if velocity_count >= 3:
        score += 30

    return score


def get_card_by_id(card_id):
    for card in cards:
        if card["id"] == card_id:
            return card
    return None


#SETUP

print_title("CONNECTING TO REDIS")

try:
    r.ping()
    print("Redis connection successful. PING -> PONG")
except redis.exceptions.ConnectionError:
    print("Redis connection failed. Make sure Docker Redis container is running.")
    exit()


print_title("CLEAN DATABASE")

r.flushdb()
print("Old Redis data cleared with FLUSHDB.")


print_title("INSERT: LOAD 20 CARD/CUSTOMER RECORDS")

for card in cards:
    card_key = f"card:{card['id']}"

    # Hash: card profile
    r.hset(card_key, mapping={
        "name": card["name"],
        "segment": card["segment"],
        "city": card["city"],
        "limit": card["limit"],
        "status": "active"
    })

    # Set: city and segment grouping
    r.sadd(f"city:{card['city']}", card_key)
    r.sadd(f"segment:{card['segment']}", card_key)

    # Sorted Set: initial risk score
    r.zadd("risk_scores", {card_key: 0})

print("20 card/customer records inserted.")


print_title("INSERT: LOAD TRANSACTION EVENTS AND UPDATE RISK SCORES")

for tx in transactions:
    card = get_card_by_id(tx["card_id"])
    card_key = f"card:{tx['card_id']}"

    # Stream: transaction event log
    r.xadd("transactions:stream", {
        "card_id": tx["card_id"],
        "amount": tx["amount"],
        "merchant": tx["merchant"],
        "city": tx["city"],
        "country": tx["country"],
        "channel": tx["channel"],
        "created_at": int(time.time())
    })

    # List: recent transactions per card
    recent_tx_key = f"recent_tx:{tx['card_id']}"
    recent_tx_value = f"{tx['amount']} | {tx['merchant']} | {tx['city']} | {tx['country']} | {tx['channel']}"
    r.lpush(recent_tx_key, recent_tx_value)
    r.ltrim(recent_tx_key, 0, 4)

    # String + TTL: velocity counter
    velocity_key = f"velocity:{tx['card_id']}"
    velocity_count = r.incr(velocity_key)

    if r.ttl(velocity_key) == -1:
        r.expire(velocity_key, 60)

    # Calculate and update risk score
    risk_score = calculate_risk_score(card, tx, int(velocity_count))
    r.zincrby("risk_scores", risk_score, card_key)

    # Add to suspicious watchlist if risk is high
    total_score = r.zscore("risk_scores", card_key)

    if total_score >= 60:
        r.sadd("suspicious_cards", card_key)
        r.hset(card_key, "status", "under_review")

print("Transaction events inserted.")
print("Risk scores updated.")
print("Suspicious cards detected.")


#READ OPERATIONS

print_title("READ: CARD PROFILE")

print("Command equivalent: HGETALL card:1007")
print(r.hgetall("card:1007"))


print_title("READ: CARD RISK SCORE")

print("Command equivalent: ZSCORE risk_scores card:1007")
print(r.zscore("risk_scores", "card:1007"))


print_title("READ: RECENT TRANSACTIONS OF CARD 1007")

print("Command equivalent: LRANGE recent_tx:1007 0 4")
print(r.lrange("recent_tx:1007", 0, 4))


# UPDATE OPERATIONS

print_title("UPDATE: MANUALLY INCREASE RISK SCORE")

print("Before update:")
print("Risk score:", r.zscore("risk_scores", "card:1001"))
print("Status:", r.hget("card:1001", "status"))

# Update score and status
r.zincrby("risk_scores", 25, "card:1001")
r.hset("card:1001", "status", "under_review")
r.sadd("suspicious_cards", "card:1001")

print("After update:")
print("Risk score:", r.zscore("risk_scores", "card:1001"))
print("Status:", r.hget("card:1001", "status"))


# ADVANCED QUERIES

print_title("ADVANCED QUERY 1: TOP 5 RISKY CARDS")

print("Command equivalent: ZREVRANGE risk_scores 0 4 WITHSCORES")
top_cards = r.zrevrange("risk_scores", 0, 4, withscores=True)

for rank, item in enumerate(top_cards, start=1):
    card_key = item[0]
    score = item[1]
    card_name = r.hget(card_key, "name")
    card_status = r.hget(card_key, "status")
    print(f"{rank}. {card_key} | {card_name} | risk score: {score} | status: {card_status}")


print_title("ADVANCED QUERY 2: RISK RANK OF CARD 1007")

print("Command equivalent: ZREVRANK risk_scores card:1007")
rank = r.zrevrank("risk_scores", "card:1007")
score = r.zscore("risk_scores", "card:1007")

print("Zero-based Redis rank:", rank)
print("Human-readable rank:", rank + 1)
print("Risk score:", score)


print_title("ADVANCED QUERY 3: LATEST TRANSACTION EVENTS")

print("Command equivalent: XREVRANGE transactions:stream + - COUNT 5")
latest_transactions = r.xrevrange("transactions:stream", "+", "-", count=5)

for tx_id, tx_data in latest_transactions:
    print(tx_id, tx_data)


print_title("ADVANCED QUERY 4: PREMIUM CARDS IN ISTANBUL")

print("Command equivalent: SINTER city:Istanbul segment:Premium")
print(r.sinter("city:Istanbul", "segment:Premium"))


print_title("TTL / VELOCITY MONITORING")

print("Command equivalent: GET velocity:1007")
print("Velocity count:", r.get("velocity:1007"))

print("Command equivalent: TTL velocity:1007")
print("Seconds until velocity key expires:", r.ttl("velocity:1007"))


#DELETE OPERATIONS

print_title("DELETE: REMOVE CARD FROM SUSPICIOUS LIST AND DELETE VELOCITY KEY")

print("Before delete:")
print("Suspicious cards:", r.smembers("suspicious_cards"))

# Delete from suspicious list and delete temporary velocity key
r.srem("suspicious_cards", "card:1001")
r.delete("velocity:1001")

print("After delete:")
print("Suspicious cards:", r.smembers("suspicious_cards"))
print("velocity:1001 value:", r.get("velocity:1001"))


print_title("DEMO COMPLETED")

print("This demo covered:")
print("- Setup and ingestion")
print("- Insert operations")
print("- Read operations")
print("- Update operations")
print("- Delete operations")
print("- Advanced queries")
print("- Redis Hash, Sorted Set, Stream, List, Set, and TTL usage")