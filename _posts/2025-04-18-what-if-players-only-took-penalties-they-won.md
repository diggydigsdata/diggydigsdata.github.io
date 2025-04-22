---
layout: post
title: "DRAFT: You Won It, You Take It"
date: 2025-04-18 19:02 +0000
description:
image:
category: [Football, Penalties]
tags: [data, analytics, hypotheticals, rule changes, basketball, penalties, soccer, football]
---

What do Raheem Sterling and Shaquille O'Neal have in common? Quite a lot, actually.

Raheem is the PL's greatest ever winner of penalties - with 26. Raheem is also one of the PL's greatest ever goalscorers; with 123 goals, he ranks 20th all-time. Meanwhile, Shaq is one of basketball's greatest ever free throw foul-drawers. He ranks 4th all-time:

1.	Karl Malone	13188
2.	Wilt Chamberlain	11862
3.	LeBron James	11735
4.	Shaquille O'Neal	11252

Source: [https://www.basketball-reference.com/leaders/fta_career.html](https://www.basketball-reference.com/leaders/fta_career.html)

But Shaq and Raheem are also historically bad at converting the chances their drawn fouls create. O'Neal only succeeded with 52% of his attempts. In Premier League play, Sterling has converted 43%. That is abysmal considering the average success rate in the Premier League era is 78.9%.

Despite Shaq's poor shooting from the free throw line, those points nevertheless helped him rack up the points. He is the 9th-highest scoring player in NBA history. Where would he rank if Kobe Bryant got to take all of Shaq's fouls?*Shaq wouldn't fall quite as far as you might think. See footnote about 'Hack-A-Shaq'. It would make NBA scoring contests very dull. The same players would always top the statlines.

But that's basically the case in football. Harry Kane has been excellent for Bayern Munich. But some of the hyperbole around his goalscoring is overblown. When you have Leroy Sane and Jamal Musiala dribbling at defenders, you will win an extraordinary volume of penalties. And sure enough, Harry is way out in front of the Bundesliga scoring charts this season with 24 goals. But he's not first if you take away everyone's penalties. That would be Patrick Schick (17), then Harry (15), just ahead of Ermedin Demirovic (13) - who most people have never heard of.

Despite Sterling winning lots of penalties, he very rarely gets to take them. He has only taken 7 in the Premier League; typically, the ball was whipped away from him by Steven Gerrard (33 PL penalties converted at a rate of 80.5%), or Sergio Aguero (27 PL penalties scored for 81.82% success). Raheem currently ranks 30 in the all-time PL scoring charts with 123 goals. If he took all those penalties, where would he rank? And why stop there? Unfortunately, I don’t have PkWon data further back than 2016/17; otherwise, Alan Shearer’s PL goals record would be under threat from Andy Cole. Only 1 of Cole’s 187 PL goals came from the spot. Whereas 58 of Shearer’s 260 came from the spot. That's a 15 goal buffer. But Cole won a lot of penalties. Nevertheless, we’re going to rewrite the record books as much as possible.

If we use Raheem's non-penalty goals as a base (120) then add the only penalties he would be entitled to take - 26 - then work out his `PwxG`, or Penalties won to expected goals, he'd have scored 26 * 0.43 more goals or 11.18. Now on 131, he'd jump above Son, Anelka, Robbie Keane and Jimmy Floyd Hasselbaink (all of whom took their fair share of penalties) and he'd sit in 16th on 134 PL goals, just behind Jamie Vardy. Oh wait, hasn't Jamie Vardy scored 27 penalties? But he only won 23 of them. So shouldn't his `G-PK+xPwg` be 27 * 0.82 based on his PL penalty success rate? He's only *entitled* to 22 penalty goals. So he loses 4 and he's down to 139 PL goals.

| Player   | PL goals incl. pens | Non-pen goals | `PkWon` | PK Conversion % | `xPwG` | `G-PK+xPwG` |
| -------- | ------------------- | ------------- | ------- | --------------- | ------ | ----------- |
| Vardy    | 143                 | 116           | 23      | 82              | 18.81  | 134.81      |
| Sterling | 123                 | 120           | 26      | 43              | 11.18  | 131.18      |

>**Key:**
>- `PkWon` = penalty kicks won  
>- `xPwG` = expected penalties won goals, which is simply conversion % * `PkWon`  
>- `G-PK+xPwG` = non-penalty goals + `xPwG`

It's enough for Vardy to hang onto 15th place, but you can see where this is going.

Unfortunately, I don't have `PkWon` data further than 2016/17; otherwise, Alan Shearer's PL goals record would be under serious threat from Andy Cole. Only 1 of Cole's 187 PL goals came from the spot. Whereas 58 of Shearer's 260 came from the spot. And Cole won a lot of penalties. Nevertheless, we're going to rewrite the record books as much as possible.

## Methodology

The methods for calculating conversion rates for each player and allocating an `xPwG` get a little more exacting for my actual analysis. All of that awaits in the methodology. And then we'll be ee who the best players really were from a goal contributions perspective seeing who the best goalscorers really are if if we get rid of ball-snatching penalty-takers.

Not much to say on the data. It's the 200 highest-scoring players in the Premier League for 2022/23 and a bunch of goalscoring metrics. It all comes from FBref, and this project is possible because they have a PKwon metric - they log who is responsible for winning each penalty. FBref only has this data for the Premier League as far back as the 2016/17 season. My tally from Raheem Sterling includes earlier years - I guess that data exists somewhere because Opta has an article about it. But I don't have those numbers. Anyway, for La Liga, FBref have it untl 2015/16.

I've created a metric for this. It's not catchy, so bear with me.

### **`xPwG`**
`xPwG`, or Expected penalties won leading to goals, needs some unpacking. I have assigned a value of 0.75% to each penalty. Why?

#### Penalty Conversion Rates
For another project - No Fear At That Age - I compiled penalty data from:

- Every normal time penalty taken in the Premier League - in other words, since the 1992/1993 season
- Every normal time penalty taken in the Champions League since the 1999/2000 season
- Every normal time penalty taken in La Liga since the 1999/2000 season

For this project, I am adding:
- Every penalty taken in the shootout of a major international tournament.

Interesting that I have 7 less years from La Liga than the Premier League, but 64 more penalties.

* The club data was taken from FBref while the international shootout data comes from [RSSSF](https://www.rsssf.org/miscellaneous/penaltiestour.html)


| **League**       | **Total Penalties** |
| ---------------- | ------------------- |
| Premier League   | 2892                |
| La Liga          | 2956                |
| Champions League | 925                 |
| Int. Shootouts   | 1907                |
| **Total**        | **6773**            |

And when it comes to conversion rates, all three leagues are roughly equivalent:

| Competition      | Conversion Rate (%) |
| ---------------- | ------------------- |
| Club Comps       | 77.99               |
| Champions League | 77.19               |
| Premier League   | 78.84               |
| La Liga          | 77.40               |
| Int. Shootouts   | 73.52               |

Unsurprisingly, the international shootouts have worse conversion. Players are more nervous *and* many penalty takers are non-specialist; i.e. they don't take penalties for their club sides.

Hypothetically, if this new rule really came into place, then the specialist penalty takers would necessarily be the players who are most likely to win penalties - that is, attacking players. The data backs this up.

Those players could assume they will win their fair share, whereas defensive players wouldn't. Specialisation would have to fall in line accordingly. Therefore, I will propose assigning a conversion rate based on player positions. *To Do: Get this into SQL so I can join datasets for each year and group by position. In addition, I need to group by position for penalty taking success*. Note: I will do a mini dashboard piece about success rate by position.

Unfortunately, I haven't added positional data for the datasets I downloaded. For wingers and forwards I will assign a value based on the specialists' average: - 78%. For everyone else the value will be based on a middle ground between specialists in club comps and the pressure cooker penalty shootout success rate - that middle ground is roughly 75.75%.

This means that an attacking midfield or forward player who wins a penalty will be treated a specialist and assigned 0.78 expected goals. Everyone else will get 0.7575 expected goals.

Let's take an example. In 2023/24 Anthony Gordon won an extraordinary 6 penalties for Newcastle. As a winger, he gets a 0.78 expected goals value. That means his `xPwG` is 0.78*6, or 4.68 goals.

On the other hand, Jarrad Branthwaite won 1 penalty for Everton. He is a defender, so he gets 0.7575*1 for an `xPwG` of 0.7575 goals.

### **`G-PK+xPwg`**
If we now take Anthony Gordon's non-penalty goals - 11 - and add his `xPwG` we get his `G-PK+xPwg`: 11+4.68. If Anthony Gordon took the penalties he won in 2023/24 we could expect him to score 15.68 goals.

In my analysis to come, I will also deploy `xAG` - expected Assists Leading to Goals. This is not a stat of my own invention and it's a close cousin of expected assists. I will quote the [NY Times](https://www.nytimes.com/athletic/6214991/2025/03/20/erling-haaland-assists-premier-league/) on this:
>"Where expected assists (xA) considers all passes and the probability that they may ultimately lead to a scoring chance, xAG solely focuses on the passes that directly contribute to an expected goal." 

If Kobe took Shaq's free throws, he would tumble down the scoring charts. Although not by quite as much as you might expect. Shaq was so bad at shooting when 15 feet from the basket - a little over two Shaq's laid head to toe to head to toe - that a new tactic was invented: 'Hack-a-Shaq'. The idea was that if you simply fouled Shaq and put him at the free throw line, he would likely score less points - 1 from his 2 free throw attempts - than if you took the risk of letting the play continue because he'd probably manage to pivot and dunk for 2 points. So, if teams knew Kobe was stepping up with his 83.7% shooting then Shaq would have been hacked a heck of a lot less.

Shaq may be long gone, but this tactic has evolved into a huge problem for the sport.


would give him an additional which is a metric I have invented for this article.

And yet, football might stand to learn something from it. No, I'm not about to propose that players deliberately foul each other, but the basic principle of NBA free throws - that the fouled player takes the shot, would be a fascinating addition to the sport. Moreover, I think it would allow for better performance comparisions and minimise the effects of statistics padding caused by players who feast on penalties that their team-mates have earned for them.

Let's just see *what happens if we start retroactively giving penalties to the players who won them*. We'll use penalty conversion averages to change historical goalscoring statistics, and in the spirit of meritocracy, we'll also be playing with xAG (expected assisted goals). Basically, the goal of all of this is to s
