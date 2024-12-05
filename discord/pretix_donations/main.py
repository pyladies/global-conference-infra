import tomllib
import requests
from pathlib import Path
from discord import SyncWebhook, Embed


with Path("config.toml").open("rb") as f:
    config = tomllib.load(f)

webhook = config["general"]["CHANNEL_WEBHOOK"]
token = config["general"]["PRETIX_TOKEN"]

if __name__ == "__main__":

    donors = []
    total = 0
    url = "https://pretix.eu/api/v1/organizers/pyladiescon/events/2024/orders/"
    while True:
        response = requests.get(url, headers={"Authorization": f"Token {token}"})
        data = response.json()
        for v in data["results"]:
            email = v["email"]
            for p in v["payments"]:
                amount = float(p["amount"])
                if amount > 0 and p["state"] == "confirmed":
                    donors.append((email, amount))
                    total += amount
        if not data["next"]:
            break
        url = data["next"]

    sorted_donors = sorted(donors, key=lambda x: x[1], reverse=True)
    top_donors = "\n- $".join([str(i[1]) for i in sorted_donors[:5]])

    message = f"# {total} USD\n\n## Top 5 donations\n\n- ${top_donors}"

    w = SyncWebhook.from_url(webhook)
    e = Embed(title="Conference Donations", description=message, color= 0xb42a34)
    w.send(embed=e)
