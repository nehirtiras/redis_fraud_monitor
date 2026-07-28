import random
import time
import redis


r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)


cards = {
    "1001": {"name": "Nehir Tiras", "city": "Istanbul", "limit": 50000},
    "1002": {"name": "Pinar Yilmaz", "city": "Ankara", "limit": 40000},
    "1003": {"name": "Mert Kaya", "city": "Izmir", "limit": 100000},
    "1007": {"name": "Mehmet Celik", "city": "Istanbul", "limit": 120000},
    "1013": {"name": "Emre Kaplan", "city": "Ankara", "limit": 110000},
}


merchants = [
    "Electronics Store",
    "Online Gaming",
    "Luxury Hotel",
    "Digital Wallet",
    "Airline",
    "Streaming Service",
    "Grocery",
    "Crypto Exchange",
]


cities = [
    ("Istanbul", "TR"),
    ("Ankara", "TR"),
    ("Izmir", "TR"),
    ("Berlin", "DE"),
    ("Paris", "FR"),
    ("Dubai", "AE"),
]


channels = [
    "POS",
    "ECOM",
]


def print_title(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def initialize_cards():
    for card_id, card in cards.items():
        card_key = f"card:{card_id}"

        r.hset(card_key, mapping={
            "name": card["name"],
            "city": card["city"],
            "limit": card["limit"],
            "status": "active"
        })

        r.zadd("risk_scores", {card_key: 0})


def calculate_risk(card_id, amount, tx_city, tx_country, channel):
    card = cards[card_id]
    reasons = []
    risk = 0

    if amount > card["limit"] * 0.10:
        risk += 20
        reasons.append("high amount")

    if tx_country != "TR":
        risk += 25
        reasons.append("foreign transaction")

    if tx_city != card["city"]:
        risk += 15
        reasons.append("city mismatch")

    if channel == "ECOM":
        risk += 10
        reasons.append("e-commerce channel")

    velocity_key = f"velocity:{card_id}"
    velocity_count = r.incr(velocity_key)

    if r.ttl(velocity_key) == -1:
        r.expire(velocity_key, 60)

    if int(velocity_count) >= 3:
        risk += 30
        reasons.append("high velocity")

    return risk, reasons, velocity_count


def generate_transaction():
    card_id = random.choice(list(cards.keys()))

    # card:1007 için daha riskli işlem üretme ihtimalini artırıyoruz.
    if random.random() < 0.35:
        card_id = "1007"

    amount = random.choice([
        250,
        750,
        1500,
        3000,
        8500,
        12000,
        25000,
    ])

    merchant = random.choice(merchants)
    tx_city, tx_country = random.choice(cities)
    channel = random.choice(channels)

    return {
        "card_id": card_id,
        "amount": amount,
        "merchant": merchant,
        "city": tx_city,
        "country": tx_country,
        "channel": channel,
    }


def process_transaction(tx):
    card_id = tx["card_id"]
    card_key = f"card:{card_id}"

    risk_delta, reasons, velocity_count = calculate_risk(
        card_id=card_id,
        amount=tx["amount"],
        tx_city=tx["city"],
        tx_country=tx["country"],
        channel=tx["channel"],
    )

    r.xadd("transactions:stream", {
        "card_id": tx["card_id"],
        "amount": tx["amount"],
        "merchant": tx["merchant"],
        "city": tx["city"],
        "country": tx["country"],
        "channel": tx["channel"],
        "created_at": int(time.time()),
    })

    r.lpush(
        f"recent_tx:{card_id}",
        f"{tx['amount']} | {tx['merchant']} | {tx['city']} | {tx['country']} | {tx['channel']}"
    )
    r.ltrim(f"recent_tx:{card_id}", 0, 4)

    r.zincrby("risk_scores", risk_delta, card_key)

    total_score = r.zscore("risk_scores", card_key)

    if total_score >= 60:
        r.sadd("suspicious_cards", card_key)
        r.hset(card_key, "status", "under_review")

    return risk_delta, reasons, velocity_count, total_score


def show_top_risky_cards():
    top_cards = r.zrevrange("risk_scores", 0, 4, withscores=True)

    print("\nTop 5 risky cards:")

    for rank, item in enumerate(top_cards, start=1):
        card_key = item[0]
        score = item[1]
        name = r.hget(card_key, "name")
        status = r.hget(card_key, "status")

        print(f"{rank}. {card_key} | {name} | score={score} | status={status}")


def main():
    print_title("LIVE REDIS FRAUD MONITOR")

    try:
        r.ping()
        print("Redis connection successful.")
    except redis.exceptions.ConnectionError:
        print("Redis connection failed. Start Redis with: docker compose up -d")
        return

    r.flushdb()
    initialize_cards()

    print("Initial card data loaded.")
    print("Live transaction simulation is starting...")
    print("Press CTRL + C to stop.\n")

    try:
        for i in range(1, 16):
            tx = generate_transaction()
            risk_delta, reasons, velocity_count, total_score = process_transaction(tx)

            print_title(f"Transaction #{i}")

            print("New transaction:")
            print(tx)

            print("\nRisk analysis:")
            print("Risk delta:", risk_delta)
            print("Risk reasons:", reasons if reasons else ["normal transaction"])
            print("Velocity count:", velocity_count)
            print("Total card risk score:", total_score)

            if total_score >= 60:
                print("ALERT: Card added to suspicious_cards watchlist.")

            show_top_risky_cards()

            time.sleep(2)

    except KeyboardInterrupt:
        print("\nLive monitor stopped by user.")

    print_title("LIVE MONITOR COMPLETED")

    print("Suspicious cards:")
    print(r.smembers("suspicious_cards"))

    print("\nLatest 5 transaction events:")
    latest_events = r.xrevrange("transactions:stream", "+", "-", count=5)

    for event_id, event_data in latest_events:
        print(event_id, event_data)


if __name__ == "__main__":
    main()