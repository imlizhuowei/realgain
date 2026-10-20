import json, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
c = [f for f in fm.findSystemFonts() if 'NotoSansCJK' in f or 'Noto Sans CJK' in f or 'NotoSerifCJK' in f]
if c:
    fm.fontManager.addfont(c[0]); plt.rcParams['font.family'] = fm.FontProperties(fname=c[0]).get_name()
o = json.load(open('aflow_first_pass.json')); ds = list(o)
B1, B2, T1, T2, S = '#2a78d6', '#eb6834', '#0b0b0b', '#52514e', '#fcfcfb'
fig, ax = plt.subplots(1, 2, figsize=(12, 4.8), facecolor=S)
x = np.arange(len(ds)); w = 0.36
a = ax[0]; a.set_facecolor(S)
r = [o[d]['run_sd_median'] * 100 for d in ds]; q = [o[d]['item_se_median'] * 100 for d in ds]
a.bar(x - w/2 - 0.01, r, w, color=B1, label='运行随机性（5 次重复能测到）')
a.bar(x + w/2 + 0.01, q, w, color=B2, label='抽题误差（5 次重复测不到）')
a.set_xticks(x, [f"{d}\n{o[d]['n_questions']}题" for d in ds], color=T2, fontsize=9)
a.set_ylim(0, 7)
a.set_ylabel('分数的标准误（百分点）', color=T2)
a.set_title('① AFlow 的重复只测到了小的那部分噪声', color=T1, loc='left', fontsize=12)
a.legend(frameon=False, fontsize=9, loc='upper left', ncol=2)
a2 = ax[1]; a2.set_facecolor(S)
tot = sum(o[d]['n_accepted'] for d in ds); r1 = sum(o[d]['accepted_beyond_run_noise'] for d in ds); r2 = sum(o[d]['accepted_beyond_question_noise'] for d in ds)
vals = [tot, r1, r2]; labs = ['被保留的改动', '超出运行随机性\n(z>2)', '超出抽题误差\n(95% CI 不含 0)']
a2.bar(range(3), vals, 0.5, color=[B1, B1, B2])
for i, v in enumerate(vals):
    a2.text(i, v + 0.4, str(v), ha='center', color=T1, fontsize=11)
a2.set_xticks(range(3), labs, color=T2, fontsize=9); a2.set_ylim(0, tot + 4)
a2.set_title(f'② {tot} 个被保留的改动里，能和噪声区分开的只有 {r2} 个', color=T1, loc='left', fontsize=12)
for A in ax:
    for s in ['top', 'right']: A.spines[s].set_visible(False)
    A.spines['left'].set_color('#cfcdc6'); A.spines['bottom'].set_color('#cfcdc6'); A.tick_params(colors=T2)
    A.yaxis.grid(True, color='#ecebe7'); A.set_axisbelow(True)
fig.text(0.01, 0.01, '数据：AFlow 公开运行日志（6 个 benchmark，gpt-4o-mini）。逐步检验，未做多重比较校正；初步结果。', color=T2, fontsize=8)
plt.tight_layout(rect=(0, 0.04, 1, 1)); plt.savefig('aflow_first_pass.png', dpi=150, facecolor=S)
