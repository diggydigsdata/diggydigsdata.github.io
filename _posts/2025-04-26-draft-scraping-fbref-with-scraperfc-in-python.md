---
layout: post
title: "DRAFT A Beginner's Guide to Scraping FBref with Python"
date: 2025-04-26 10:22 +0200
description: "This project documents an easy-peasy and adaptable way to scrape football data from FBref using Python and the ScraperFC package. It is also a practise project for me to play with Oxygen XML."
image:
category: [How-To, Web Scraping]
tags: [technical writing, how-to, guide, python, scraperfc, fbref, oxygen xml]
published: true
sitemap: true
---

# Scraping FBref with Python

This project explains an easy-peasy and adaptable way to scrape football data from FBref using Python and the ScraperFC package. It is particulary suitable for beginner programmers.  
  
By the end of this guide, you should be able to:
- adapt your own scripts to request specific information from FBref datasets
- clean and merge the resulting data for easier analysis across multiple leagues and seasons

## Prerequisites

**Skills: None.**  
I am not a programmer. I need this data for personal projects that are helping me learn coding skills. Therefore, scraping this data was more challenging for me than most people and I made very avoidable errors. Often, documentation assumes a basic level of familiarity with environments and terminology which I do not possess. Therefore, I will explain all steps without assuming any knowledge whatsoever.

**Tools: None.**  
Everything you need to install will be explained.

## Why FBref?

FBref and Stathead host Penalty Kicks Won data, which no other stats provider seems to provide. In addition, I have found FBref and Stathead to be significantly more accurate and comprehensive than competitors such as Transfermarkt, particulary on penalty data.  
When I began this project, I did not understand that Stathead and FBref were 2 different things. Both are run by Sports Reference LLC, and both host the same array of Opta data for football \(soccer\). But there are several crucial differences:

|Stathead|FBref|
|--------|-----|
|Sophisticated stat-search function|No search function - just lots of stats everywhere|
|Excellent for exploration|Awkward for exploration|
|Paid \(approx $8/month as of April 27, 2025\)|Free|
|No ads|Ads|
|Data can be gathered by 'copy and paste' or by download \(Excel &amp; CSV\)|Data can be gathered by 'copy and paste'|
|Data is paginated and only 200 records can be download at one time.|Data is not paginated|
|Data **CANNOT** be scraped - neither physically nor legally|Data **CAN** be scraped|

## Scope Of Instruction

My project focuses on scraping the Big 5 European leagues — Premier League, La Liga, Bundesliga, Serie A, and Ligue 1 — across the 2016/17 to 2023/24 seasons. I adapted the ScraperFC package to get the data I want: its 'standard' and 'miscellaneous' FBref tables. However, this guide makes it very possible for you to extract as much or as little data as you want from FBref.

Instructions are also included for cleaning the scraped datasets and merging them. I am using my own project as an example, but advice on adapting my code will be provided.