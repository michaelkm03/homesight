

![Image description](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/boclko09fvsprmrq296a.png)

Two ZIP codes. Same city. 13x apart in home value growth.

75225 — University Park, Dallas. Home values up 26% over 3 years.

75252 — North Dallas. Home values up 1.9% over 3 years.

Same metro. Same window. A 13x gap in home price appreciation.

When I found this, I checked my math. Then I checked it again. The numbers were right — and this wasn't a fluke. Once I started looking at ZIP-level home value data instead of metro averages, I found the same pattern everywhere.

Sun Belt cities where massive metro-level home price gains hid flat or declining ZIPs underneath. Midwest markets written off in every headline while specific neighborhoods quietly compounded home values at 10% a year for a decade. Old industrial cities with suburbs whose home appreciation outperformed markets people pay a premium to enter.

Metro averages were burying all of it.

## City-Level Home Price Data Is the Wrong Unit

Every housing headline you've ever read is built on metro-level data. It's easy to produce: aggregate all home sales in a city, compute a median price, publish a number.

The problem is that number doesn't describe any actual neighborhood.

Dallas metro home values "up 10%" is a blend of University Park (+26%), North Dallas (+1.9%), and hundreds of ZIPs in between. That number is technically accurate. It's useless for deciding where to buy.

The variance in home price appreciation within a city is often larger than the variance between cities. Which ZIP you buy into matters more than which metro — but almost nothing shows you ZIP-level home value data clearly and for free.

That gap is what I built [HomeSight](https://homesight.live/) to fill.

## How I Processed the Home Value Data

[HomeSight ](https://homesight.live/)runs on a publicly available dataset tracking median home values at the ZIP level, updated monthly, going back to 2000.

For each of the 26,000+ ZIPs in the dataset, I calculated home value appreciation over 1, 3, 5, 10, and 20-year windows. I filtered out P.O. Box ZIPs, IRS processing centers, and any ZIP without enough transaction history to produce a reliable home price trend.

I also pulled in rent trends, median list prices, and new listing volume — because home price appreciation alone doesn't tell the full story. A ZIP up 20% with rising inventory is a different real estate bet than one up 20% with shrinking supply.

The result is a national picture of how home values have moved at the neighborhood level for the past two decades.

## What the Home Value Data Actually Shows

Four patterns stand out across the full dataset.


Sun Belt home price gains were real — and uneven. Austin, Phoenix, and Tampa all showed big metro-level home value appreciation from 2020–2022. Zoom into individual ZIPs and it gets messier: outer suburban areas that boomed on remote-work demand are now flat or negative on a 3-year home price basis. Urban
cores held up far better. The metro average looks like a clean story. The ZIP-level home value data is a patchwork.

The Midwest is quietly building home equity. Columbus, Indianapolis, Kansas City — markets that never show up in housing headlines. At the ZIP level, you find specific neighborhoods that have compounded home values at 8–12% annually for a decade with low volatility. If you only look at metro comparisons,
you'd skip these entirely.

Old industrial cities have home value pockets the average hides. Metro Detroit gets written off constantly in national housing coverage. ZIP-level data shows suburbs like Royal Oak and Ferndale with 10-year home price appreciation that rivals markets people pay a premium to enter. The metro average buries
them completely.

The biggest home value gaps are within metros, not between them. This was the most consistent finding across the full dataset. The spread in home appreciation between the top and bottom ZIPs in a single metro often exceeds the spread between metros entirely. Picking the right ZIP matters more than picking
the right city — and that's the decision almost no free tool is designed to help you make.

## Who This Is For

First-time buyers trying to understand what they're walking into. Buying into a ZIP that's appreciated 25% in home values over 3 years is a fundamentally different bet than one that's moved 3% — even if list prices look similar today.

Real estate investors who need to screen markets at scale. ZIP-level home value data lets you identify which neighborhoods have outperformed their metro before digging into individual properties. The rankings panel does this automatically for any city.

Current homeowners who want context on their own market. How does your ZIP's home value growth compare to your neighbors? To your metro median? To the national trend? The answer is usually more specific — and more interesting — than any headline will tell you.

## What You Can Do With It

![Image description](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/o6k2s7qlomdv8xjna4v3.png)
[HomeSight ](https://homesight.live/)is free at https://homesight.live/. No account, no email.

Every ZIP is color-coded by home value appreciation rate. Toggle between time windows and the map updates. Click any ZIP and you get:

- 1, 3, 5, 10, and 20-year home value appreciation
- Rent trends over time
- Median sale prices
- New listing volume
![Image description](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/hb7v0afvbj4x0xrg9bev.png)
- Metro ranking — where this ZIP's home price growth sits relative to every other in the same city

## One Honest Caveat

This dataset tracks median home value trends at the ZIP level — not individual sale prices or specific property types. It won't tell you why a ZIP appreciated or what's coming next. For that you need local knowledge: employer moves, transit announcements, neighborhood dynamics on the ground.

What it does tell you: exactly how much home values have moved, at the ZIP level, across the whole country, for the last 20 years. That's the baseline most buyers and investors are missing before they make a decision worth hundreds of thousands of dollars.

## The Question Worth Asking

"Is Dallas a good real estate market?" is the wrong question.

"Which Dallas?" is the one that matters.

The same is true for every metro in this country. The answer has always been in the ZIP-level home value data — it just wasn't easy to see until now.

[homesight.live](https://homesight.live/) — free, no signup required. I Mapped Home Prices Across 26,000 U.S. ZIP Codes. Here's What City Averages Are Hiding.
