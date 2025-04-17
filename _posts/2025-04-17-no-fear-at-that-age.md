---
layout: post
title: No Fear At That Age
date: 2025-04-17 22:02 +0000
description: 
image: 
category: [Sports, Football]
tags: [data, analytics, penalties, soccer, football]
---

There's 'no fear at that age' is a familiar refrain from pundits. The idea goes that young players are basically ignorant of the importance of things, and consequently don't feel nerves the way older players do because 'ignorance is bliss' - or something. Presumably this idea rests on the presumption that young players think they have all the time in the world so a few blunders early on in their career won't be the end of it. Or, there is so little pressure applied on them relative to senior players that they play with freedom and can 'express themselves'. I can understand that to a certain extent, although young players could easily go in the other, overawed direction. 18 year old me would definitely have fallen into the shitting myself camp. But then, it could be argued that I don't have the mentality of an elite athlete.

Anyway, out of curiosity I decided to explore the metric that is the easiest to isolate as a corollary for fear. And that is the penalty.

Because another fairly common idea is that every pro player should be able to tuck away a penalty. But, 12 yards from goal, it is nerves which prove decisive. Unfortunately, the best way to explore fear would be penalty shootout data. But I haven't got that. Because normal-time penalties usually don't have quite the same almighty importance. However, they still tell us something about nervousness, and so I have whipped up the following (courtesy of Stathead / FBref):
- Every normal time penalty taken in the Premier League - in other words, since the 1992/1993 season
- Every normal time penalty taken in the Champions League since the 1999/2000 season
- Every normal time penalty taken in La Liga since the 1999/2000 season

## Penalty population
All together, that's:

| League           | Total Penalties |
| ---------------- | --------------- |
| Premier League   | 2892            |
| La Liga          | 2956            |
| Champions League | 925             |
| **Total**        | **6773**        |

Interesting that I have 7 less years from La Liga than the Premier League, but 64 more penalties.

## Conversion Rates
Quick observation. They are evenly matched for conversion rate:
| Competition      | Conversion Rate (%) |
| ---------------- | ------------------- |
| Champions League | 77.19               |
| Premier League   | 78.84               |
| La Liga          | 77.40               |

# What about age?

Well, at first I thought we were onto something.

![Champions League penalty conversion age vs success trendline](/assets/img/CL_conversion_line.png)

## Age Group Penalty Data (Champions League)

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

## Age Group Penalty Data (Premier League)

| Age Group                  | Penalty Attempts | Penalty Conversions | Conversion Rate (%) |
| -------------------------- | ---------------- | ------------------- | ------------------- |
| <=20: No Fear At That Age? | 80               | 60                  | 75.00               |
| 21-23: Not A Kid Anymore   | 503              | 398                 | 79.13               |
| 24-26: Early Peak          | 834              | 654                 | 78.42               |
| 27-29: Peak Peak           | 793              | 624                 | 78.69               |
| 30-32: Over The Hill?      | 495              | 387                 | 78.18               |
| 33+: Cherry On Top         | 187              | 157                 | 83.96               |
| **Grand Total**            | **2892**         | **2280**            | **78.84**           |

In the Premier League, things level out a bit more, although there still seems to be a mild advantage for experience.

![Premier League penalty conversion age vs success trendline](/assets/img/EPL_conversion.png)

## Age Group Penalty Data (La Liga)

| Age Group                  | Penalty Attempts | Penalty Conversions | Conversion Rate (%) |
| -------------------------- | ---------------- | ------------------- | ------------------- |
| <=20: No Fear At That Age? | 81               | 63                  | 77.78               |
| 21-23: Not A Kid Anymore   | 405              | 307                 | 75.80               |
| 24-26: Early Peak          | 829              | 653                 | 78.77               |
| 27-29: Peak Peak           | 833              | 644                 | 77.31               |
| 30-32: Over The Hill?      | 511              | 400                 | 78.28               |
| 33+: Cherry On Top         | 297              | 221                 | 74.41               |
| **Grand Total**            | **2956**         | **2288**            | **77.40**           |

![La Liga penalty conversion age vs success trendline](La_Liga_conversion.png)

Things get flipped on their head a little bit in La Liga. For the first time, the Cherry on Top vets aren't the most effective penalty takers. In fact, in La Liga they are the worst. Meanwhile, the 20s and under are right up there near the top. And if we drill down into that age group, we can really appreciate how precocious those La Liga teens are.

| Age Group                  | Penalty Attempts | Penalty Conversions | Conversion Rate (%) |
| -------------------------- | ---------------- | ------------------- | ------------------- |
| <=20: No Fear At That Age? | 81               | 63                  | 77.78               |
| 18                         | 10               | 8                   | 80.00               |
| 19                         | 27               | 24                  | 88.89               |
| 20                         | 44               | 31                  | 70.45               |

Let's remove the 20 year olds. Now, La Liga teens have a success rate of 86%! Of course, there's a caveat... That's a population size of just 37. Ezequiel Garay - one of history's great centre-back penalty takers and a stalwart of my FC Atlas team in Football Manager - accounts for 22% of the entire La Liga teenage penalty taking population. And Jose Antonio Reyes accounts for another 19%. All together, those two players - and their combined 92% success rate - represent 41% of the whole group.

So let's bundle everything together and see what we get...

![All combined penalty conversion age vs success trendline](/assets/img/alltogether.png)

We don't really get anything. There is a very very mild indication that more experienced players do better than younger players. Considering the lowest success rates are 20 and under, and 21-23 are 2nd-lowest, there is some indication that young players are not totally fearless. I think this is particularly noteworthy because, players who are designated penalty takers at such a young are generally prodigious talents. They are, in all likelihood, incredibly talented. Therefore, is it a psychological vulnerability that causes their penalty-taking to dip a little compared to their older peers?
