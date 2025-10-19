---
layout: post
title: "DRAFT(but updated with python plots): No Fear At That Age"
date: 2025-09-30
categories: [football, analysis]
tags: [python, plotly, penalties, logistic regression, quarto, jupyter, data analysis]
---

‘There’s no fear at that age’ is a familiar refrain from pundits. The
idea goes that young players are naive, innocent; they take risks, they
express themselves, and in an ‘ignorance is bliss way’ they don’t show
nerves the way older players do - or something.

I guess the fearlessness theory rests on the presumption that young
players think they have all the time in the world so a few blunders
early on in their career won’t be the end of it. Or, there is so little
pressure applied on them relative to senior players that they play with
freedom and can ‘express themselves’. I can understand that to a certain
extent, although young players could easily go in the other, overawed
direction. 18 year old me would definitely have fallen into the shitting
myself camp. But then, it could be argued that I don’t have the
mentality of an elite athlete.

In any case, I’ve always been skeptical. They are young adults, not
toddlers. And loads of promising young careers go up in smoke; the
consequences for these players’ lives are devastating. Look at Jose
Baxter, for example. I would imagine most young players have seen enough
academy cohort colleagues fall by the wayside that they are acutely
aware of their vulnerability. So I wanted to dig into this throwaway
comment from pundits and find some way to interrogate it statistically.

## How to measure fear?  
To put fearlessness to the statistical test, I've turned to the penalty. That’s because another fairly common idea is that every elite
player *should* be able to tuck away a penalty. And that, 12 yards from
goal, it is nerves rather than technique which undoes the pro player.  

While the best way to explore fear would be penalty shootout data -
where every single kick is critical - I haven’t got that and will make do with
normal-time penalties. These don’t have quite the
same almighty importance but they still tell us something about the
effects of nerves.

This is part of a series of analyses I’m doing where I fixate on
penalties. It just drives me crazy how prevalent they are. It
increasingly like every final is decided on penalties and every match a
penalty is awarded. And it’s not just because of VAR. Penalties per match have been increasing for some time. See
<a href="#fig-penalties-per-match" class="quarto-xref">Figure 1</a>. Or
the interactive version <a href="#fig-penalties-per-match-plotly"
class="quarto-xref">Figure 2</a> (more league data will be added). If you'd like to see a world where Penaldo doesn't exist, this is my main project. It assess hat would happen if players who won the penalties were the only ones who got to take them, and it re-evaluates historical data to use non-penalty goals while crediting players who won penalties instead of the takers. I also throw in some assist analyses for good measure. [Read more here]({{ "/football/npg+pkwon/" | relative_url }})


<div id="fig-penalties-per-match">
  <img src="{{ '/assets/files/NoFearCode_files/figure-commonmark/fig-penalties-per-match-output-1.png' | relative_url }}"
       alt="Average penalties per match over time, by league (with global trend)">
  <figcaption>Figure 1: Average penalties per match over time, by league (with global trend)</figcaption>
</div>

<div id="fig-penalties-per-match-plotly">

<iframe src="{{ "/assets/plots/penalties_over_time.html" | relative_url }}" width="100%" height="600" frameborder="0" loading="lazy"></iframe>

Figure 2

</div>

# Methodology

## Penalty sampling

I have whipped up the following (courtesy of Stathead / FBref):

- Every normal time penalty taken in the Premier League - in other
  words, since the 1992/1993 season
- Every normal time penalty taken in the Champions League since the
  1999/2000 season
- Every normal time penalty taken in La Liga since the 1999/2000 season

| **League**       | **Total Penalties** |
|------------------|---------------------|
| Premier League   | 2892                |
| La Liga          | 2956                |
| Champions League | 925                 |
| **Total**        | **6773**            |

## Age bands

Finally, I have constructed some age groupings. See . This is in order
to prevent small samples for different ages giving unreliable values.
For example, there is a 20% difference in the success rate for La Liga
19 year-olds compared 20 year-olds. However, given these age groups have
relatively few attempts it’s easy for the data to get a little wild.

I think the groups I have created are fairly logical. At the top and
bottom end we’ve got open intervals - we can have players from 0 to 20;
though the youngest penalty taker in this data is 17. And our 33+ group
can go to infinity. Though the oldest penalty taker is .. This group are
called No Fear At That Age? Because it’s the age when expectations are
minimal, you are at your most naive, innocent, etc. And the elder
statesmen are called Cherry on Top. I would theorise that they also have
a bit less pressure, because they have already had a good career, and
nobody is looking at their performance as a measure of their potential.
They are a known quantity by this point.

They sandwich 3-year age bands. 21-23 could be the most pressurised age.
That’s the point at which many wonderkid careers have gone awry - think
Bojan Krkic. It’s the moment when you need to step up, mature, realise
your potential and be consistent. Otherwise, a journeyman career in the
lower leagues could await you. Then 24-26 could constitute the beginning
of a player’s peak years. 27-29 would often be considered, depending a
little on position, the absolute peak years of the average player. 30-32
has proven very fruitful for many players too. However, the perspective
on these players definitely shifts. At this point, pressure amplifies
because pundits and fans are often questioning whether you are ‘past
it’, whether you should get a multi-year contract renewal or not. Just
look at Mo Salah. In 2024/2025 he has having a career year but, at the
age of 32, Liverpool have spent all season agonising about whether to
give him a commensurate contract because of his age.

### Caveat

One enormous **caveat**, however, is that the ages provided by Stathead
simply use the player’s age at the commencement of the season, not their
age at the time of taking a penalty. Consequently, the oldest penalty
taker in the dataset is Teddy Sheringham. He appears as 39 in my
dataset, but he had recently turned 40 when he missed a final-day
penalty for West Ham against Tottenham in the 2005/06 season. Jorge
Molina also appears as 39 in my dataset, but he was 40 when he missed
against Espanyol on the final day of the 2021/22 season, effectively
relegating Granada from La Liga.

Similarly, the dataset indicates a 17 year-old - Bojan Krkic. But he was
18 by the time he took his penalty for Barcelona against Manchester
United in the Champions League. This is all rather annoying, but it
would be more trouble than it’s worth to separate out every single
penalty from each player’s season statistics and dial in the taker’s age
on a specific date. It just means there is a +/- of 9 months (i.e. the
length of a season) for each player’s age.

## Averages

In this analysis I calculate **conversion rates** in two different ways,
which reflect slightly different questions:

- **Weighted (overall) mean**: This is the percentage of all penalties
  scored divided by the total penalties attempted within a group (e.g. a
  competition). Every penalty counts equally, so players who take more
  penalties have more influence. This measure tells us the *true success
  rate of the group as a whole*.

- **Unweighted (player) mean**: This is the simple average of individual
  players’ conversion rates. Each player counts equally, no matter how
  many penalties they have taken. This measure answers the question:
  *what does the “average player” in this group look like?*

In the charts shown here, the main benchmark (red dashed line) is the
**weighted overall mean**, because it reflects the actual outcome of all
penalties taken across the dataset.

## Analysis

First off, when it comes to conversion rates across the leagues, there
are no differences whatsoever. Which is boring but convenient that we
don’t need to worry too much about league effects.

![](assets\files\NoFearCode_files\figure-commonmark\cell-9-output-1.png)

             PKatt    PK  PKm  conversion_rate
    Comp                                      
    CL         925   714  211        77.189189
    EPL       2892  2280  612        78.838174
    La Liga   2956  2288  668        77.401894

Or do we? Any differences when we break the leagues down by age group?


There’s *maybe* a trend towards improved penalty conversion as you
accumulate experience. The ‘no fear’ players are *slightly* more
clinical than the players aged 21-23 who may be coming under pressure to
make the next step as more mature and consistent players.

### Age Group Penalty Data (Champions League)

| Age Group                  | Penalty Attempts | Penalty Conversions | Conversion Rate (%) |
| -------------------------- | ---------------- | ------------------- | ------------------- |
| <=20: No Fear At That Age? | 41               | 30                  | 73.17               |
| 21-23: Not A Kid Anymore   | 139              | 99                  | 71.22               |
| 24-26: Early Peak          | 238              | 184                 | 77.31               |
| 27-29: Peak Peak           | 272              | 217                 | 79.78               |
| 30-32: Over The Hill?      | 158              | 122                 | 77.22               |
| 33+: Cherry On Top         | 77               | 62                  | 80.52               |
| **Grand Total**            | **925**          | **714**             | **77.19**           |

There's a clear trend towards improved penalty conversion as you accumulate experience. The 'no fear' players are *slightly* more clinical than the players aged 21-23 who may be coming under pressure to make the next step as more mature and consistent players.

But this is the smallest dataset - only 925 penalties.

![](assets\files\NoFearCode_files/figure-commonmark/cell-10-output-1.png)

![](assets\files\NoFearCode_files/figure-commonmark/cell-11-output-1.png)

### Age Group Penalty Data (Premier League)

| Age Group | Penalty Attempts | Penalty Conversions | Conversion Rate (%) |
|----|----|----|----|
| \<=20: No Fear At That Age? | 80 | 60 | 75.00 |
| 21-23: Not A Kid Anymore | 503 | 398 | 79.13 |
| 24-26: Early Peak | 834 | 654 | 78.42 |
| 27-29: Peak Peak | 793 | 624 | 78.69 |
| 30-32: Over The Hill? | 495 | 387 | 78.18 |
| 33+: Cherry On Top | 187 | 157 | 83.96 |
| **Grand Total** | **2892** | **2280** | **78.84** |

In the Premier League, things level out a bit more, although there still
seems to be a mild advantage for experience.

### Age Group Penalty Data (La Liga)

| Age Group | Penalty Attempts | Penalty Conversions | Conversion Rate (%) |
|----|----|----|----|
| \<=20: No Fear At That Age? | 81 | 63 | 77.78 |
| 21-23: Not A Kid Anymore | 405 | 307 | 75.80 |
| 24-26: Early Peak | 829 | 653 | 78.77 |
| 27-29: Peak Peak | 833 | 644 | 77.31 |
| 30-32: Over The Hill? | 511 | 400 | 78.28 |
| 33+: Cherry On Top | 297 | 221 | 74.41 |
| **Grand Total** | **2956** | **2288** | **77.40** |

Things get flipped on their head a little bit in La Liga. For the first
time, the Cherry on Top vets aren’t the most effective penalty takers.
In fact, in La Liga they are the worst. Meanwhile, the 20s and under are
right up there near the top. And if we drill down into that age group,
we can really appreciate how precocious those La Liga teens are.

| Age Group | Penalty Attempts | Penalty Conversions | Conversion Rate (%) |
|----|----|----|----|
| \<=20: No Fear At That Age? | 81 | 63 | 77.78 |
| 18 | 10 | 8 | 80.00 |
| 19 | 27 | 24 | 88.89 |
| 20 | 44 | 31 | 70.45 |

Let’s remove the 20 year olds. Now, La Liga teens have a success rate of
86%! Of course, there’s a caveat… That’s a population size of just 37.
Ezequiel Garay - one of history’s great centre-back penalty takers and a
stalwart of my FC Atlas team in Football Manager - accounts for 22% of
the entire La Liga teenage penalty taking population. And Jose Antonio
Reyes accounts for another 19%. All together, those two players - and
their combined 92% success rate - represent 41% of the whole group.

So let’s bundle everything together and see what we get…

| Age Group | Penalty Attempts | Penalty Conversions | Conversion Rate (%) |
|----|----|----|----|
| \<=20: No Fear At That Age | 202 | 153 | 75.74 |
| 21-23: Not A Kid Anymore | 1047 | 804 | 76.79 |
| 24-26: Early Peak | 1901 | 1491 | 78.43 |
| 27-29: Peak Peak | 1898 | 1485 | 78.24 |
| 30-32: Over The Hill? | 1164 | 909 | 78.09 |
| 33+: Cherry On Top | 561 | 440 | 78.43 |
| **Grand Total** | **6773** | **5282** | **77.99** |

There is a *very* mild indication that more experienced players do
better than younger players. Considering the lowest success rates are 20
and under, and 21-23 are 2nd-lowest, there is some indication that young
players are not totally fearless. I think this could be particularly
noteworthy because, players who are designated penalty takers at such a
young are rare and they are, in all likelihood, technically gifted.
Therefore, is it a psychological vulnerability that causes their
penalty-taking to dip a little compared to their older peers? And that
maybe they aren’t so impervious to fear as pundits may casually claim?

Let’s see if this stands up to statistical scrutiny.

Data assembled from: [Stathead](https://stathead.com/fbref/)

### Logistic Regression

#### Method

Each penalty in the dataset is tied to a player, season, and league.
Since some players take penalties in multiple seasons (or even in
multiple leagues), the raw data contained repeated rows for the same
player. To avoid overweighting those players, we collapsed the dataset
to one row per **player × age group × league**, summing up penalties
scored and attempted within each cell. This way, every player
contributes fairly to the analysis.

I used a **logistic regression model** because the outcome of
interest—scoring or missing a penalty—is binary. Logistic regression
lets us model the probability of success while accounting for the number
of attempts in each cell. We tested age group, league, and their
interaction to see if any of them had an effect on conversion rates.
Confidence intervals were estimated around the predicted probabilities
to judge how much overlap there was between groups.

#### Results

To test whether penalty conversion varies by age or by league, I fit a
logistic regression with both predictors and their interaction. The
likelihood-ratio tests showed no evidence that either factor—or their
combination—improves model fit (all p \> .4). In other words, neither
age group nor league explains variation in conversion odds.

Predicted probabilities were remarkably consistent across groups,
generally hovering between **73% and 84%**. For instance:

- **≤20 years**: 73–78% across leagues  
- **21–23 years**: 71–79%  
- **27–29 years (peak)**: 77–79%  
- **33+ years**: 74–84%

Confidence intervals overlapped substantially, indicating no systematic
age or league effect.


| Age Group                   | League   | Predicted Conversion Rate | 95% CI (Low) | 95% CI (High) |
|-----------------------------|----------|--------------------------|--------------|--------------|
| 33+: Cherry On Top          | EPL      | 84.0%                    | 77.9%        | 88.6%        |
| 33+: Cherry On Top          | CL       | 80.5%                    | 70.2%        | 87.9%        |
| 27-29: Peak Peak            | CL       | 79.8%                    | 74.6%        | 84.1%        |
| 21-23: Not A Kid Anymore    | EPL      | 79.1%                    | 75.4%        | 82.5%        |
| 24-26: Early Peak           | CL       | 77.3%                    | 71.6%        | 82.2%        |
| 27-29: Peak Peak            | EPL      | 78.7%                    | 75.7%        | 81.4%        |
| 24-26: Early Peak           | La Liga  | 78.8%                    | 75.9%        | 81.4%        |
| 30-32: Over The Hill?       | CL       | 77.2%                    | 70.0%        | 83.1%        |
| 27-29: Peak Peak            | La Liga  | 77.3%                    | 74.3%        | 80.0%        |
| 24-26: Early Peak           | EPL      | 78.4%                    | 75.5%        | 81.1%        |
| 30-32: Over The Hill?       | La Liga  | 78.3%                    | 74.5%        | 81.6%        |
| 30-32: Over The Hill?       | EPL      | 78.2%                    | 74.3%        | 81.6%        |
| ≤20: No Fear At That Age?   | La Liga  | 77.8%                    | 67.5%        | 85.5%        |
| ≤20: No Fear At That Age?   | EPL      | 75.0%                    | 64.4%        | 83.3%        |
| 21-23: Not A Kid Anymore    | La Liga  | 75.8%                    | 71.4%        | 79.7%        |
| ≤20: No Fear At That Age?   | CL       | 73.2%                    | 57.7%        | 84.5%        |
| 33+: Cherry On Top          | La Liga  | 74.4%                    | 69.1%        | 79.1%        |
| 21-23: Not A Kid Anymore    | CL       | 71.2%                    | 63.2%        | 78.1%        |

*Conversion rates by age group and league, sorted by predicted conversion rate (highest to lowest), with 95% confidence intervals.*