#!/usr/bin/env python3
"""yt_analytics_report.py [START END]: read-only channel report (defaults to the last 30 days). Needs token_analytics.json from yt_analytics_auth.py."""
import os,json
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
T=Path(__file__).resolve().parents[3]/'_internal'/'.youtube'/'token_analytics.json'
c=Credentials.from_authorized_user_file(str(T))
if not c.valid: c.refresh(Request()); T.write_text(c.to_json(),encoding='utf-8')
an=build('youtubeAnalytics','v2',credentials=c); yt=build('youtube','v3',credentials=c)
import sys
from datetime import date,timedelta
A=dict(startDate=sys.argv[1] if len(sys.argv)>1 else (date.today()-timedelta(days=30)).isoformat(),endDate=sys.argv[2] if len(sys.argv)>2 else (date.today()-timedelta(days=1)).isoformat())
def q(**k):
    try: return _q(**k)
    except Exception as e: return {'rows':[],'columnHeaders':[],'err':str(e)[:80]}
def _q(**k): return an.reports().query(ids='channel==MINE',**A,**k).execute()
out=[]
r=q(metrics='views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,subscribersLost,likes,comments,shares')
out.append('CHANNEL '+str(dict(zip([h['name'] for h in r['columnHeaders']],r['rows'][0]))))
r=q(metrics='views,estimatedMinutesWatched,averageViewPercentage,subscribersGained',dimensions='video',sort='-views',maxResults=15)
ids=[x[0] for x in r['rows']]
tt={v['id']:v['snippet']['title'] for v in yt.videos().list(part='snippet',id=','.join(ids)).execute()['items']}
for x in r['rows']: out.append(f"{x[1]} views | avg%viewed {x[3]:.0f} | subs+{x[4]} | {tt.get(x[0],'')}")
r=q(metrics='views,subscribersGained',dimensions='video',sort='-subscribersGained',maxResults=8)
ids=[x[0] for x in r['rows']]
tt={v['id']:v['snippet']['title'] for v in yt.videos().list(part='snippet',id=','.join(ids)).execute()['items']}
out.append('TOP SUB GAINERS')
for x in r['rows']: out.append(f"subs+{x[2]} views {x[1]} | {tt.get(x[0],'')}")
out.append('TRAFFIC '+str(q(metrics='views,estimatedMinutesWatched',dimensions='insightTrafficSourceType',sort='-views')['rows']))
out.append('COUNTRY '+str(q(metrics='views',dimensions='country',sort='-views',maxResults=6)['rows']))
out.append('DEMO '+str(sorted(q(metrics='viewerPercentage',dimensions='ageGroup,gender')['rows'],key=lambda x:-x[2])[:6]))
out.append('SHORTS-vs-LONG '+str(q(metrics='views,averageViewPercentage',dimensions='creatorContentType')['rows']))
out.append('DAILY '+str([(a[5:],b) for a,b in q(metrics='views',dimensions='day',sort='day')['rows']]))
print(chr(10).join(out))
