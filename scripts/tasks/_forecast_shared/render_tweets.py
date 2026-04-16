from __future__ import annotations


def render_tweets(tweets: list[dict]) -> str:
    if not tweets:
        return "[no local tweets available for the history end date]"
    return "\n".join(f"{tweet['date']}: {tweet['text']}" for tweet in tweets)
