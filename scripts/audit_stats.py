import sys, pandas as pd, numpy as np
from scipy import stats
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_csv('data/backtest_v2.csv')
df['log_sales'] = np.log1p(df['total_purchases'])
wl = df[df['tier'].isin(['WINNER','LOSER'])].copy()
wl['label'] = (wl['tier']=='WINNER').astype(int)

components = ['sat','demand','dead_health','momentum','forced_buyer','rating_score']

print("=== SPEARMAN: each component vs log(sales) ===")
for c in components+['viability']:
    r,p = stats.spearmanr(df[c], df['log_sales'])
    sig = '***' if p<0.001 else '**' if p<0.01 else '*' if p<0.05 else 'ns'
    print(f"  {c:15s}: r={r:+.4f}  {sig}")

print("\n=== AUC-ROC per component (WINNER vs LOSER) ===")
for c in components+['viability']:
    a = roc_auc_score(wl['label'], wl[c])
    print(f"  {c:15s}: {a:.4f}")

OLD_W = dict(sat=0.10,demand=0.14,gap=0.04,dead_health=0.10,moat=0.12,momentum=0.22,forced_buyer=0.13,rating_score=0.15)
NEW_W = dict(sat=0.10,demand=0.20,dead_health=0.12,momentum=0.28,forced_buyer=0.13,rating_score=0.17)
old_score = sum(wl[c]*OLD_W.get(c,0) for c in ['sat','demand','gap','dead_health','moat','momentum','forced_buyer','rating_score'] if c in wl.columns)
new_score = sum(wl[c]*NEW_W.get(c,0) for c in components)
old_auc = roc_auc_score(wl['label'], old_score)
new_auc = roc_auc_score(wl['label'], new_score)
print(f"\n=== FORMULA COMPARISON ===")
print(f"  Old 7-component: AUC={old_auc:.4f}")
print(f"  New 8-component: AUC={new_auc:.4f}  delta={new_auc-old_auc:+.4f}")

u,p = stats.mannwhitneyu(wl[wl['tier']=='WINNER']['viability'],wl[wl['tier']=='LOSER']['viability'],alternative='greater')
rb=1-2*u/(len(wl[wl['tier']=='WINNER'])*len(wl[wl['tier']=='LOSER']))
print(f"\n=== MANN-WHITNEY (WINNER > LOSER) ===")
print(f"  p={p:.6f}  rank-biserial r={rb:.4f}")

print("\n=== SCORE DISTRIBUTION BY TIER ===")
print(df.groupby('tier')['viability'].describe().round(1))

best_f1,best_t=0,42
for t in range(30,75):
    pred=(wl['viability']>=t).astype(int)
    f1=f1_score(wl['label'],pred,zero_division=0)
    if f1>best_f1: best_f1,best_t=f1,t
pred=(wl['viability']>=best_t).astype(int)
print(f"\n=== OPTIMAL THRESHOLD ===")
print(f"  t={best_t}  F1={best_f1:.4f}  P={precision_score(wl['label'],pred,zero_division=0):.4f}  R={recall_score(wl['label'],pred,zero_division=0):.4f}")

print("\n=== WIN RATE BY BAND ===")
for band,lo,hi in [('SCREEN OUT',0,41),('INVESTIGATE',42,46),('CONSIDER',47,51),('LAUNCH',52,100)]:
    sub=wl[(wl['viability']>=lo)&(wl['viability']<=hi)]
    if len(sub)==0: continue
    win_pct=sub[sub['tier']=='WINNER'].shape[0]/len(sub)*100
    print(f"  {band:12s} ({lo}-{hi}): n={len(sub):3d}  {win_pct:.0f}% are WINNER")
