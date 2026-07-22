# Post 1 — Ready to Publish (Authority / F7 Odd-Precision)

## ⚠️ Before you post: you need a public link

The first comment carries the article link. Right now the article (README.md) only
exists on your machine. Publish it publicly first, then paste the URL where marked below.

Fastest option: push this repo to a **public** GitHub repo. GitHub renders README.md
(figures and all) as the repo landing page, so the repo URL is the article.
Example URL shape: `https://github.com/<your-username>/data-football`

---

## 1) THE POST (paste into the post box)

Home teams in the Brasileirão take 63.1% of all points on offer.

Not 63%. 0.631, across 5,319 matches from 2012 to 2025. I counted every one.

I went looking for the strongest home advantage in world football. Here is the ledger, home share of all points won, Brazil against every one of Europe's big five, same 2012 to 2025 window:

- Brasileirão: 0.631
- La Liga: 0.596
- Ligue 1: 0.577
- Bundesliga: 0.575
- Premier League: 0.570
- Serie A: 0.563

That gap looks small. It isn't. Over a 38-game season it's the difference between a Champions League spot and mid-table.

What surprised me: the usual suspects don't explain it. I built features for travel distance, altitude, heat, days of rest. Then I tested whether any of them predict a single match better than a plain Elo rating.

They don't. The home edge is enormous in the season table.. and almost invisible match to match, because the rating already knows.

So the real question isn't "why do home teams win." It's why the effect is so much bigger here than in Europe, and I don't think crowd noise alone covers it.

Full breakdown in the comments.

What's a number in your field that everyone rounds off and shouldn't?

#FootballAnalytics #DataScience

---

## 2) THE FIRST COMMENT (paste as your own first comment, right after posting)

### Recommended (bonus-stat version — rewards the reader who clicks into comments)

One more number that didn't fit above: even during the closed-door COVID window, with empty stadiums, the home points share only fell from 0.634 to 0.582. Crowd is part of it, not all of it. Full breakdown, charts and code: [PASTE PUBLIC LINK HERE]

### Alternate (plain value version)

If you want the how, not just the number: the write-up walks through the crowd, travel and heat decomposition, the model, and where each effect shows up (and where it vanishes). Charts and code included: [PASTE PUBLIC LINK HERE]

---

## 3) HOW TO POST THE FIRST COMMENT (mechanics)

1. Publish the post first. Do NOT put the link in the post body — LinkedIn throttles
   reach on posts with outbound links in the body.
2. Within the first minute, add the first comment yourself as the author, with the link.
   Being the first comment + early activity is a reach signal, and the link is safe here.
3. Don't edit the post afterward to sneak the link in. Editing right after publishing can
   dampen reach, and a body link is penalized anyway. Keep the link in the comment.
4. For the next 60 minutes, reply fast to every commenter. Reply latency in the first hour
   is one of the strongest reach multipliers. Have 2-3 answers ready for the obvious
   pushback ("small sample", "refs bias", "isn't this just crowd noise").
5. Optional: leave the link comment as-is. If your account shows a pin/feature option on
   your own comment, pin it so it stays at the top.

## Verify before posting
- [ ] Public link works in an incognito window (no login wall, figures render)
- [ ] Post body has NO link
- [ ] First comment has the link at the very end
- [ ] The two numbers match your data: 0.634 -> 0.582 (closed-door window)
