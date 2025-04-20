---
layout: post
title: "Post-Relegation Attendance Churn"
date: 2025-04-18 19:02 +0000
description:
image:
category: [Football, Attendances]
tags: [data, analytics, attendance, relegation, fandom, soccer, football]
---
I'm a Burnley fan. And in honour of our impending promotion to the Premier League and consolidation as a yoyo club par excellence, I thought it would be a good time to assess the impact of relegation from the Premier League on attendance figures. Because it's never too early to plan ahead.

### Yoyo Club Rankings

| Club                 | PL Relegations | Championship Promotions | Current League   |
| -------------------- | -------------- | ----------------------- | ---------------- |
| Norwich City         | 6              | 5                       | Championship     |
| West Bromwich Albion | 5              | 5                       | Championship     |
| Burnley              | 4              | 5                       | Premier League   |
| Leicester City       | 5              | 5                       | Championship     |
| Crystal Palace       | 4              | 4                       | Premier League   |
| Middlesbrough        | 4              | 4                       | Championship/TBD |
| Sunderland           | 4              | 4                       | Championship/TBD |
| Watford              | 4              | 4                       | Championship     |
| Sheffield United     | 4              | 3                       | Championship/TBD |
| Southampton          | 3              | 2                       | Championship     |

Incidentally, Leicester's recent relegation not only brings them into second place on the Premier League relegation rankings but pulls them clear of Birmingham atop the Top-Flight relegations table with 13.


## Methodology

For this project, I gathered attendance data for every relegated club in the season they were relegated, and in the 2 seasons following their relegation. I also checked what league they were in for their 2nd year post-relegation. Had they been promoted at the first attempt? Spent another season in the Championship, or plummeted into League 1. I gathered all of this data from [European-Football-Statistics.co.uk](https://www.european-football-statistics.co.uk/index1.htm).

## Analysis

### Increased attendance after relegation?

Let's start on a positive note. On 10 occasions, teams managed to increase their average attendance following relegation.

| Relegated Team (Season)   | Attd.  | Year After | Attd. year after | Loss/Gain % |
| ------------------------- | ------ | ---------- | ---------------- | ----------- |
| Sunderland (96/97)        | 20,865 | 1997-98    | 33,492           | 60.5%       |
| Leicester City (01/02)    | 19,835 | 2002-03    | 29,231           | 47.4%       |
| Nottingham Forest (92/93) | 21,910 | 1993-94    | 23,051           | 5.2%        |
| Ipswich Town (01/02)      | 24,426 | 2002-03    | 25,455           | 4.2%        |
| **Burnley** (21/22)       | 19,399 | 2022-23    | 19,953           | 2.9%        |
| Newcastle United (15/16)  | 49,754 | 2016-17    | 51,106           | 2.7%        |
| Norwich City (04/05)      | 24,350 | 2005-06    | 24,952           | 2.5%        |
| Crystal Palace (94/95)    | 14,992 | 1995-96    | 15,248           | 1.7%        |
| Luton Town (23/24)        | 11,244 | 2024-25    | 11,420           | 1.6%        |
| Middlesbrough (96/97)     | 29,848 | 1997-98    | 29,994           | 0.5%        |

And I have to give a shoutout to Burnley and, indeed, to Vincent Kompany because he certainly galvanised the supporters that season. 

A couple teams really jump out. Both Sunderland and Leicester City moved into new stadia the year after their relegation, and this gave them a considerable bump. They must have been absolutely packing out their stadia the season prior and had supporters banging down the doors to get in. Sunderland even managed to add over 5,000 supporters to their tally the season after relegation, despite the fact that they were still stuck in the Championship. Leicester also increased attendances in 2003-04, by 1,600 to 30,983. But they spent that season in the Premier League, so it's less startling to see an increase.

Newcastle also catch the eye. 51,106 fans during the 2016-17 is quite extraordinary. Newcastle's fanbase has a reputation for diehard loyalty. It's why many neutrals were happy to see them bought by the Saudis, despite misgivings about sportwashing. Indeed, Newcastle also have the second-highest post-relegation attendance - 43,388 during the 2009-2010 season. That particular season did see an 11% drop on the previous year's PL average. And the contrast between 2016-17 and 2009-10 is enlightening. Similar to how Burnley fell under the spell of Vincent Kompany in 2022/23, Newcastle fans had a great relationship with Rafael Benitez - their manager from 2016 to 2019. Hired towards the end of their 2015/16 relegation season, it was considered quite a coup to attract Benitez to a Championship-bound club. And the fans showed their appreciation during his first full season in charge with record-breaking attendances.

Typically, we start to see the cracks in season 2 outside the top flight. Filtering out teams like Leicester who were promoted at the first attempt and had Premier League fixtures to pull in the fans, only 6 teams see attendance figures in the black by season 2.

| Relegated Team (Season) | Attd.  | Attd. year after | Loss/Gain % | Attd. 2 yrs. after | Loss/Gain % 2 yrs. |
| ----------------------- | ------ | ---------------- | ----------- | ------------------ | ------------------ |
| Sunderland (96/97)      | 20,865 | 33,492           | 60.5%       | 38,745             | 86%                |
| Middlesbrough (92/93)   | 16,724 | 10,400           | -37.8%      | 18,702             | 11.8%              |
| Crystal Palace (94/95)  | 14,992 | 15,248           | 1.7%        | 16,085             | 7.3%               |
| Manchester City (95/96) | 27,869 | 26,753           | -4.0%       | 28,196             | 1.2%               |
| Norwich City (04/05)    | 24,350 | 24,952           | 2.5%        | 24,545             | 0.8%               |
| Ipswich Town (01/02)    | 24,426 | 25,455           | 4.2%        | 24,520             | 0.4%               |

Again, we have some anomalies. Middlesborough's attendance nosedived in 1993-94 but they were undergoing a stadium rebuild. Basically, they had more stadium 2 years later. By 2017-18, Middlesborough were hosting 25,544 fans a game in the Championship and over 30,000 during their stint for the preceding year's stint in the Prem. So their 10,400 fan turnout - heck, even their 18,702 fan turnout, are merely reflective of stadium constraints and not reflective of their true fanbase.

### Nosedives

middlesborough, oldham

### And in general?

On average, attendance falls significantly after relegation. The below table shows a 1st-year average decrease of 13.72%. And it shows that in the second year, there is an average decrease of 12.34%.

| League       | Year After Avg. Loss/Gain % | 2 yrs After Avg. of Loss/Gain % |
| ------------ | --------------------------- | ------------------------------- |
| Championship | -13.72%                     | -19.15%                         |
| League 1     | N/A                         | -23.80%                         |
| PL           | N/A                         | 5.36%                           |
| Overall      | -13.72%                     | -12.34%                         |

EXCLUDING MIDDLESBOROUGH, LEICESTER & SUNDERLAND

| League       | Year After Avg. Loss/Gain % | 2 yrs After Avg. of Loss/Gain % |
| ------------ | --------------------------- | ------------------------------- |
| Championship | -13.45%                     | -21.49%                         |
| League 1     | N/A                         | -23.80%                         |
| PL           | N/A                         | 3.24%                           |
| Overall      | -14.98%                     | -14.59%                         |

I think this table excluding Middlesborough, Leicester and Sunderland who introduce anomalies related to stadium constructions may be a better reference for this data. Superficially, the above data is reassuring. If you just look at the overalls, then it would seem attendances stabilise in Year 2 after relegation. You lose 15% of your attendance immediately after relegation, but at least it doesn't get worse. But it does.

If you didn't get promoted to the Premier League at the first time of asking and spend a 2nd year in the Championship, then you can expect to lose a further 8% of your Premier League attendance. And if you get relegated to League 1, that jumps above 10%. So it seems teams will stick with a team more resolutely in the year after their relegation, likely hoping for a successful season and a swift return. By Year 2, that optimism may fade and attendance figures dwindle still further. Let's probe that performance factor further.

### Does performance affect attendance?

The below table shows how the outcome of your first season post-relegation can impact attendance figures during that season.

| Destination during Championship Season | Average of Loss/Gain % |
| -------------------------------------- | ---------------------- |
| Championship                           | -16.58%                |
| League 1                               | -28.16%                |
| PL                                     | -5.84%                 |
| 2023/24 teams without year 2 data      | -4.07%                 |
| &nbsp;&nbsp;&nbsp;Burnley              | -7.29%                 |
| &nbsp;&nbsp;&nbsp;Luton Town           | 1.57%                  |
| &nbsp;&nbsp;&nbsp;Sheffield United     | -6.47%                 |


EXCLUDING MIDDLESBOROUGH (93/94), LEICESTER (02/03) & SUNDERLAND (97/98)

 | Destination during Championship Season | Average of Loss/Gain % |
 | -------------------------------------- | ---------------------- |
 | Championship                           | -17.53%                |
 | League 1                               | -28.16%                |
 | PL                                     | -8.15%                 |
 | 2023/24 teams with unknown destination | -4.07%                 |
 | &nbsp;&nbsp;&nbsp;Burnley              | -7.29%                 |
 | &nbsp;&nbsp;&nbsp;Luton Town           | 1.57%                  |
 | &nbsp;&nbsp;&nbsp;Sheffield United     | -6.47%                 |


If your club isn't on track to bounce straight back, then they can expect to lose around 17% of the previous years' attendance. And if they are heading for back-to-back relegations, with a freefall to League 1, expect losses of 28.16%. If, however, they are in the hunt for promotion then the losses are considerably less. Teams bound for the Premier League only lose 5.84% (8.15% excluding the new-stadium teams). As you can see, the above data also excludes teams who were relegated in 2023/24 - Burnley, Luton, Sheffield United. However, I think it's best to include them. Luton are likely to be relegated, Burnley are likely to be promoted, and Sheffield United will probably just miss out on the top 2 and console themselves with the playoffs. Since all 3 clubs have spent the entire season on these trajectories, it's safe enough to incorporate their impact on the season's attendances. So I will include them as Luton: relegated to League 1; Burnley and Sheffield United promoted to the Premier League.

With Burnley & Sheffield United as PL, and Luton as League 1

| Destination during Championship Season | Average of Loss/Gain % |
| -------------------------------------- | ---------------------- |
| Overall                                | -13.72%                |
| Championship                           | -16.58%                |
| League 1                               | -20.73%                |
| PL                                     | -5.92%                 |
| Grand Total                            | -13.72%                |

With Burnley & Sheffield United as PL, and Luton as League 1. EXCLUDING MIDDLESBOROUGH (93/94), LEICESTER (02/03) & SUNDERLAND (97/98)

| Destination during Championship Season | Average of Loss/Gain % |
| -------------------------------------- | ---------------------- |
| Overall                                | -14.98%                |
| Championship                           | -17.53%                |
| League 1                               | -20.73%                |
| PL                                     | -8.05%                 |
| Grand Total                            | -14.98%                |

Luton really buck the trend for League 1-destined sides. And because there are so few teams who are relegated from the Premier League to League 1 in consecutive seasons, their outlier status has a huge impact on the data, dropping the averages by almost 8%. But can Luton really be considered anomalous when the data population is so small? In my view, yes. First of all, Luton had an emotional relegation season. Their captain Tom Lockyer suffered a cardiac arrest mid-game. Fortunately, he survived and has been on a road to recovery ever since with the view to playing again. Moreover, Luton battled very bravely against relegation despite these traumatising events and despite being financial minnows. Luton were a uniquely united club during their relegation season. However, that is not the only explanation. The other is that Luton are another stadium-constrained side. Kenilworth Road is famously tiny, and was a peculiar relic among Premier League stadiums. Luton have received approval for a stadium rebuild that will double its capacity. Based on their increased attendances post-relegation, Luton are another case of a club where demand has exceeded supply for some time.

Just a quick note on Burnley, who were in the black during their Kompany-led campaign but have lost almost 8% this season. There are a few factors at play. First, morale sank during Kompany's PL season. Burnley were truly awful and the core of their Championship-winning side was cast aside in favour of new recruits - an inexplicable decision in the view of many fans. Moreover, ALK capital - the ownership group - made some ill-judged and patronising comments to supporters for not bringing a positive enough atmosphere to Turf Moor. In a nutshell, the mood was bleak by the end of 2022-23. Kompany's departure and subsequent replacement by Scott Parker failed to excite fans. Nor did selling half the first team squad and sitting through a million 0-0 draws. Despite the successful campaign, Parker-ball has been a bit of a slog. Sidenote: I was a huge Parker skeptic at first but I think he has brought the solidity Burnley needed and, as the season has gone on, a more cohesive team has taken shape, the football has yielded more goals and the fanbase has gotten on side. In any case, this all goes to highlight that there are complexities behind the averages I am presenting here.

## Conclusions
- Teams can typically expect to lose 12 to 15% of their attendance after relegation
- If you are on track for Promotion, these losses are lessened
- If you are on track to stay in the Championship, these losses are slightly higher
- And if you are on track for League 1, these losses are considerably higher
- Investigating the outliers in the dataset tends to reveal mitigating circumstances. Often these relate to stadium builds, but in other cases - like Newcastle and Burnley - it is just vibes at play. To really understand the data I would dig into each relegated team a little more to understand what underlying factors affect other teams because it's possibly more nuanced than relegation = fanbandonment.
