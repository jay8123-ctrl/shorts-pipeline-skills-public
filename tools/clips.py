"""clips.py: clip config for build_short.py. This is a WORKED EXAMPLE from a real batch (a 26-min English panel on X,
1920x1080 59.94p): five picks with zh-Hans karaoke lines. Copy this file for each new source and replace everything below.

Schema
  SOURCE      dict(url, title, channel): goes into each clip's metadata JSON and the README
  SUB         small source line printed at the bottom of every title card (outlet · event · date)
  CLIPS       {clip_id: dict(...)}. clip_id is the file prefix ("NN" or "N-PP" = publish order + pick number)
      pick, order   researcher pick number, publish order
      slug          short English kebab-case name -> "<clip_id>-<slug>.mp4"
      src_in/out    source seconds, snapped to sentence boundaries (word timestamps + rms.py)
      card          (kicker, title line 1, title line 2): neutral Chinese, claims attributed to the speaker
      theme         one-line zh summary (metadata only)
      lines         [(zh-Hans text <= ~12 chars, English as spoken, anchor = source start time of its first word), ...]
      fade_out      optional audio fade-out seconds (default 0.3); still_t optional still time (clip seconds)
  MANUAL_X    {(clip_id, shot_src_t0 rounded to 3): (crop x, reason)}: fixed crop for shots where faces alone can't
              decide (wide shots / panels: frame the current speaker)
  CUTS        hard-cut times in source seconds (detect_cuts.py, confirmed by eye)
  WORD_FIXES  extra [start, end, word] entries added to words.json (words ASR mistimed or dropped)
  LOGO        (x0, x1) source-px span of a burned-in logo near the subtitle zone, or None
  CARD_Y, SUB_MARGIN_V, SUB_MARGIN_V_LOGO  layout overrides (1080x1920 output px)
Line anchors come from faster-whisper medium word starts (overlapping 30 s windows + VAD re-runs), cross-checked with
50 ms audio RMS (rms.py). Line ends are derived in build_short.py."""

SOURCE = dict(url="https://x.com/RSBNetwork/status/2105045751898268096",
              title="FULL: Elon Musk, Jensen Huang, Tom Brown Discuss the AI Revolution & What's Next",
              channel="RSBN (@RSBNetwork on X)")
WORD_FIXES = [[1305.20, 1305.60, "essential,"],   # windows mis-timed it; RMS burst 1305.2-1305.55
              [1390.75, 1391.10, "SIs"]]          # RMS onset of "the SIs are tools" at 1390.75
LOGO = (94, 280)          # broadcaster bug burned into the source at x 94-280 (y 806-990): lines over it are raised
CARD_Y = 1120             # card below the faces (face centres at output y≈340-770), above the subs
SUB_MARGIN_V = 370        # subs end at output y≈1550, above the burned-in news ticker (output y≈1770+)
SCHEDULE_NOTE = "Pending user review; not scheduled, not uploaded"

SUB = "RSBN · 白宫超级智能座谈 · 2026.9.29"

CLIPS = {
 "1-04": dict(pick=4, order=1, slug="china-electricity-3x", src_in=178.45, src_out=244.45,
   card=("超级智能座谈 · 能源", "马斯克：中国发电量", "约为美国的三倍"),
   theme="马斯克：美国要赢必须扩大能源和芯片产能；最大竞争对手中国的发电量约为美国三倍，核心挑战是发电和本土逻辑/存储芯片产能",
   lines=[
    ("太棒了。埃隆，我们怎么赢？", "Awesome. Elon, how do we win?", 178.88),
    ("怎样才能一直赢下去？", "How do we keep winning?", 181.24),
    ("嗯，我们需要", "Well, we need", 184.55),
    ("大量电力", "a lot of power,", 188.00),
    ("大量的发电能力", "a lot of energy generation.", 189.80),
    ("所以我认为扩大能源规模", "So scaling energy, I think,", 194.90),
    ("是最重要的事情之一", "is one of the biggest things.", 196.88),
    ("你必须扩大能源规模", "You've got to scale energy,", 198.08),
    ("必须扩大芯片产能", "you've got to scale chip production.", 198.98),
    ("我认为我们在软件上领先", "And I think we're winning on software,", 201.22),
    ("凡是智力、数字领域都领先", "on anything intellectual or digital.", 205.02),
    ("但从长远来看", "But in the long run,", 207.18),
    ("我们需要有能力", "we need to be able to", 210.58),
    ("发出足够的电来竞争", "generate enough power to compete with —", 213.08),
    ("我认为中国基本上", "I think, essentially, China", 217.34),
    ("就是最大的竞争对手", "is the biggest competitor.", 218.52),
    ("而中国的发电量", "And China has about", 219.44),
    ("约是美国的三倍", "three times the electricity production of the United States.", 222.32),
    ("我想我们能搞定芯片制造", "And I think we'll figure out how to make chips.", 225.91),
    ("所以真正的核心挑战", "So really, the central challenge, I think,", 231.04),
    ("从长远看将是", "long-term, is going to be", 233.98),
    ("如何发出足够的电", "how do you generate enough power,", 235.22),
    ("以及如何确保我们", "and how do you ensure that we have", 236.62),
    ("有足够的逻辑芯片", "enough logic", 239.18),
    ("和存储芯片制造产能", "and memory fabrication capacity", 240.60),
    ("在美国或安全地区", "in the United States or in a safe region?", 242.06),
   ]),
 "2-20": dict(pick=20, order=2, slug="claude-research-3-minutes", src_in=1207.88, src_out=1283.95,
   card=("超级智能座谈 · AI日常", "黄仁勋：用Claude做研究", "4到8小时缩到3分钟"),
   theme="黄仁勋自称“普通美国人”，用 Claude 做对比研究并自动生成图表报告，过去周末要花四到八小时的研究现在约三分钟完成",
   lines=[
    ("对普通美国人来说", "For ordinary Americans,", 1208.05),
    ("超级智能如今在做什么？", "what's superintelligence doing today,", 1209.34),
    ("一年后又能做什么？", "and what's it gonna be able to do in a year?", 1211.62),
    ("我就是个普通美国人", "I'm an ordinary American,", 1214.10),
    ("我用Claude", "and I use Claude", 1216.80),
    ("帮我做研究", "to help me do research.", 1220.60),
    ("它不只是直接给我答案", "And instead of giving me just answers —", 1224.24),
    ("我的研究大多是", "most of my research,", 1226.12),
    ("对比性质的研究", "maybe there's comparative research that I'm doing,", 1227.58),
    ("某件事有两三种做法", "and there's two or three different approaches to something,", 1230.20),
    ("我想回答一连串问题", "and I wanted to answer a list of different questions", 1232.68),
    ("比较、对照增长率", "and compare and contrast rates of growth", 1235.75),
    ("或变化率之类的", "or rates of change, or whatever it is.", 1240.18),
    ("所以我会原原本本地", "And so I describe, literally, you know,", 1242.66),
    ("写下我的每一个问题", "every single question I have.", 1244.84),
    ("最让我开心的是", "And nothing gives me more joy than —", 1246.94),
    ("我让它做一份漂亮的报告", "and I ask it to create a nice report", 1248.36),
    ("再画成图表", "and plot it out.", 1250.36),
    ("有时是饼图，有时是柱状图", "Sometimes it's a pie chart, sometimes it's a bar graph,", 1252.00),
    ("然后我按下回车", "and I just hit enter.", 1254.72),
    ("最让我开心的就是", "And nothing gives me more joy than", 1256.08),
    ("看着它“咔咔咔”地运转", "just watching it go ch-ch-ch-ch,", 1257.36),
    ("然后结果出来了", "and then it comes back,", 1259.10),
    ("生成一份漂亮的报告", "and it creates a beautiful, you know, beautiful report.", 1260.00),
    ("不用再把这些课题", "And then instead of researching all these different topics", 1263.36),
    ("花四、六、八个小时去研究", "for four, six, eight hours,", 1266.16),
    ("以前我常在周末这么做", "which back in the old days I would on a weekend,", 1268.00),
    ("学点新东西", "you know, learn something new,", 1270.04),
    ("它就自己去给我生成", "it goes off and creates me", 1271.94),
    ("一份非常非常漂亮的", "this really, really beautiful", 1273.60),
    ("最终报告，只要三分钟左右", "final report in about three minutes,", 1276.02),
    ("而且内容都浓缩好了", "and, you know, it's all condensed,", 1279.52),
    ("你就能更快地变聪明", "and now you're getting smarter faster.", 1281.24),
   ]),
 "3-21": dict(pick=21, order=3, slug="ai-reads-xrays-mri", src_in=1286.10, src_out=1343.85, fade_out=0.2,  # "Awesome." ~0.3 s after the cut
   card=("超级智能座谈 · AI医疗", "马斯克：AI看X光和核磁共振", "纠正了医生的误诊"),
   theme="马斯克：AI 将成为工作和生活的必需品；他听过许多医生误诊、患者把X光或核磁共振交给AI后得到正确诊断的案例",
   lines=[
    ("那你呢？", "What about for you?", 1286.33),
    ("你怎么看超级智能", "How are you seeing superintelligence", 1287.63),
    ("如何帮助普通美国人？", "helping ordinary Americans?", 1290.58),
    ("你觉得一两年后它能做什么？", "What do you think it'll do in a year or two?", 1292.80),
    ("比如说一两年以后", "Maybe a year or two, take the year or two from now.", 1295.00),
    ("嗯，我认为它正在帮助人们", "Yeah, well, I think it's helping people", 1297.72),
    ("打理生活、把工作做得更好", "organize their lives and do better at their jobs.", 1299.88),
    ("所以我认为它真的会", "So I think it really will", 1303.18),
    ("变得不可或缺", "become essential,", 1304.66),
    ("如果现在还没有的话", "if it isn't already,", 1306.90),
    ("人们会在工作中用AI", "for people to use AI in their professional lives,", 1308.14),
    ("这是肯定的，私人生活也是", "certainly, and in their private lives.", 1312.88),
    ("所以AI就是一个", "So AI is just an", 1315.36),
    ("非常有帮助、有用的东西", "incredibly helpful, useful thing.", 1317.66),
    ("我听过很多案例", "You know, I've heard many anecdotes", 1321.16),
    ("AI帮助人们处理医疗问题", "of AI helping people with medical issues,", 1323.90),
    ("在很多情况下", "and in many cases", 1327.54),
    ("医生判断错了", "where the doctor was wrong,", 1329.56),
    ("他们把X光或核磁共振结果", "and they submitted their X-rays or MRI", 1331.36),
    ("交给了AI", "to AI,", 1335.42),
    ("而AI判断对了", "and AI got it right.", 1337.82),
    ("要不是有AI", "But for AI,", 1340.00),
    ("他们早就死了", "they would have died,", 1341.32),
    ("这样的案例我听过很多", "and I've heard many such cases.", 1342.40),
   ]),
 "4-05": dict(pick=5, order=4, slug="electricity-gdp-spacex-10gw", src_in=250.12, src_out=333.45,
   card=("超级智能座谈 · SpaceX新增10吉瓦", "马斯克：用电量增加1%", "GDP约增长1%"),
   theme="主持人称 SpaceX 计划新增 10 吉瓦电力；马斯克称美国平均用电约 500 吉瓦，用电每增 1% 约对应 GDP 增 1%，因为每瓦智能在硬件和算法两端持续提升",
   lines=[
    ("埃隆，如果你们新增", "Elon, if you bring on", 250.34),
    ("10吉瓦电力", "10 gigawatts,", 251.86),
    ("SpaceX已公开谈过这件事", "which SpaceX has discussed publicly,", 253.00),
    ("约占全美新增电力的25%", "that'll be about 25% of all the power added in America.", 256.08),
    ("我知道你们让火箭工程师", "And I know you have literal rocket engineers", 259.80),
    ("投入到电力建设中", "working on bringing on the power,", 262.72),
    ("帮忙制造涡轮机", "helping make the turbines.", 264.64),
    ("能谈谈这个吗？", "So can you talk about that?", 266.40),
    ("是的，先说个背景", "Yeah, I mean, just to frame this,", 269.30),
    ("美国的平均用电功率", "the average power consumption in the United States", 273.00),
    ("大约是500吉瓦", "is about 500 gigawatts.", 275.04),
    ("所以每增加5吉瓦", "So every 5 gigawatts", 277.00),
    ("持续稳定的发电量", "of incremental steady-state production", 278.24),
    ("就意味着用电量增加1%", "is a 1% increase in the power used.", 279.78),
    ("而我认为这实际上", "And I think actually it will", 284.60),
    ("会转化为大约1%的GDP增长", "materialize to be approximately 1% increase in GDP,", 286.08),
    ("因为每瓦电力产生的智能", "because the intelligence per watt", 291.66),
    ("在不断提升", "keeps increasing.", 292.90),
    ("如果你把它画成曲线", "So if you just, you know, plot on a curve,", 294.24),
    ("每瓦的有效智能", "how is the useful intelligence per watt", 298.16),
    ("是怎样增长的？", "increasing?", 299.62),
    ("一方面在硬件层面", "Both at the hardware level —", 301.18),
    ("黄仁勋的GPU", "Jensen's GPUs", 303.90),
    ("每瓦算力不断提升", "keep getting better in terms of the compute per watt.", 306.00),
    ("算法也在进步", "And the algorithms also get better", 311.66),
    ("每瓦能产出更多智能", "in getting more intelligence per watt.", 313.50),
    ("这也许是个有意思的观察", "So that's maybe an interesting note.", 317.88),
    ("我敢跟任何人打赌", "I would bet anyone", 320.98),
    ("用电量增加1%", "that 1% increase in power usage", 322.34),
    ("大致对应GDP增长1%", "corresponds to roughly 1% increase in GDP.", 324.82),
    ("所以10吉瓦", "And so 10 gigawatts", 327.28),
    ("就意味着GDP增长2%", "would be a 2% increase in GDP,", 328.48),
    ("我想，用上Rubin芯片的话", "with the Rubins, I think.", 331.74),
   ]),
 "5-22": dict(pick=22, order=5, slug="steak-knife-analogy", src_in=1382.65, src_out=1470.75,
   card=("超级智能座谈 · 价值观", "黄仁勋：AI像一把牛排刀", "工具该有多少“判断力”？"),
   theme="黄仁勋“说点有争议的”：超级智能是工具，若判断力过多就像遇到一分熟牛排就切不动的牛排刀；网络安全中防守方的动作也可能像攻击",
   lines=[
    ("我们可以说点有争议的吗？", "Are we allowed to say anything controversial?", 1382.90),
    ("说点有争议的吧", "Say something controversial.", 1384.78),
    ("好的，那么", "OK, so", 1386.86),
    ("超级智能是工具", "the SIs are tools.", 1390.75),
    ("而让超级智能有价值观", "And the challenge with an SI with values,", 1392.50),
    ("问题在于它会有判断力", "meaning it has judgment:", 1398.28),
    ("取决于你怎么使用它", "depending on how you use that SI,", 1400.82),
    ("它可能会去评判你", "it may decide how it may judge you,", 1403.02),
    ("它的效能会受这种判断影响", "and its effectiveness would be affected by that judgment.", 1408.22),
    ("这有点像一把牛排刀", "And so it's a little bit like a steak knife,", 1411.52),
    ("如果上来的是七分熟", "where if you were served medium well,", 1413.64),
    ("它切得非常完美", "it cuts perfectly.", 1418.36),
    ("但如果是一分熟的牛排", "But if you were served rare steak,", 1420.02),
    ("看上去简直像生肉", "and it looks awfully like live meat,", 1422.71),
    ("它不知怎么就切不动了", "somehow it doesn't cut.", 1426.69),
    ("所以我心里还有个疑问", "And so I think there's a, you know, there's a question in my mind yet", 1428.63),
    ("这些工具到底该有", "about how much judgment you really want", 1434.18),
    ("多少判断力", "these tools to have.", 1436.50),
    ("所以使用者的意图……", "And so the intentions of the user —", 1438.54),
    ("当然，我只是拿刀举个例子", "you know, obviously I use the knife as an example,", 1442.44),
    ("你还能想到很多别的例子", "but you can think of a whole bunch of other examples.", 1445.92),
    ("意图会略有不同", "The intentions are a little bit different,", 1448.48),
    ("看你是防守方还是攻击方", "you know, whether you're a defender or an attacker,", 1451.04),
    ("比如在网络安全领域", "for example, in cybersecurity.", 1453.94),
    ("防守方的行动", "The defender's actions", 1455.98),
    ("可能看起来像攻击者", "could resemble an attacker.", 1457.20),
    ("而你希望防守方……", "And you want the defender —", 1459.62),
    ("你希望这个超级智能", "you want this SI", 1461.36),
    ("替防守方采取行动", "to activate on behalf of the defender,", 1462.84),
    ("哪怕这看起来", "even though it appears", 1466.96),
    ("像是一次攻击性行动", "to be an aggressive action.", 1468.14),
   ]),
}

# Manual x (mostly wide shots): one fixed crop per shot, x chosen for the speaker(s) from YuNet face centres of the wide shot
# (4-person wide: Tom Brown cx≈215, Musk ≈737, Jensen ≈1245, moderator ≈1710; 3-person wide: Musk ≈300, Jensen ≈970, moderator ≈1604).
# key: (clip, shot src_t0 rounded to 3) -> (crop x of a 608-wide window, note)
MANUAL_X = {
 ("2-20", 1207.88): (909, "4-person wide; moderator asks (5 s), then Jensen answers (9.5 s) and leans toward the moderator (face box x 1124-1303). Jensen + moderator span 622 px > 608, so the window is centred on Jensen, the main speaker of the shot; the moderator's question is heard off-frame"),
 ("2-20", 1223.606): (600, "close-up; Jensen leans between face-box x 552 and 1256 (704 px > 608), x=600 minimises overflow (worst ≈26% of the face box for ~1 s at 1262 s)"),
 ("2-20", 1274.94): (941, "4-person wide; Jensen speaking (cx≈1248)"),
 ("3-21", 1286.10): (1312, "4-person wide; moderator asks the question (cx≈1704, window clamped at the right edge); Musk only starts ~1 s before the cut to his close-up"),
 ("4-05", 250.12): (1300, "3-person wide; moderator speaking (cx≈1604)"),
 ("4-05", 266.867): (0, "3-person wide; moderator ends question at 267.8, Musk answers from 269.3 (cx≈284, window at the left edge)"),
 ("4-05", 308.492): (208, "angled 3-person wide; Musk speaking (cx≈512)"),
 ("5-22", 1382.65): (921, "4-person wide; Jensen asks (1 s), moderator replies 'Say something controversial' (0.7 s). Two-shot would put both faces on the window edges (span 1137-1740), so the window is centred on Jensen (face box x 1137-1313)"),
 ("5-22", 1447.579): (939, "4-person wide; Jensen speaking (cx≈1243)"),
}
# Hard cuts: per-frame grey MAD peaks (detect_cuts.py) confirmed by ffmpeg select=gt(scene,0.25) and HSV-histogram correlation; each checked on frames either side.
CUTS = [177.577, 183.183, 246.83, 255.655, 266.867, 271.872, 308.492, 325.992, 336.386,
        1202.051, 1223.606, 1274.94, 1298.731, 1345.845, 1386.719, 1387.536, 1447.579]
# The shot 177.577-183.183 (clip 1-04 opening) is a Jensen close-up while the off-screen moderator asks the question: framed on Jensen (only face in shot).
