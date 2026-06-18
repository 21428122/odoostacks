import sys, pandas as pd, numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import calibration_curve
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_csv('data/backtest_v2.csv')
df['success'] = (df['total_purchases'] >= 100).astype(int)

br = df['success'].mean()
print(f"BASE RATE: P(success>=100 purchases) = {br:.4f} ({df['success'].sum()}/{len(df)})")

X = df[['viability']].values
y = df['success'].values
lr = LogisticRegression(random_state=42, max_iter=1000).fit(X, y)
print(f"\n=== LOGISTIC: P(success | viability score) ===")
for s in [35,40,42,44,46,47,48,50,52,55,60,65]:
    p = lr.predict_proba([[s]])[0][1]
    bar='|'*int(p*30)
    print(f"  Score {s:3d} -> {p*100:5.1f}%  {bar}")

y_prob = lr.predict_proba(X)[:,1]
frac_pos, mean_pred = calibration_curve(y, y_prob, n_bins=6)
print(f"\n=== CALIBRATION (predicted vs actual rate) ===")
for p,a in zip(mean_pred, frac_pos):
    print(f"  Predicted {p:.2f} -> Actual {a:.2f}  {'WELL' if abs(p-a)<0.05 else 'OFF'}")

components = ['sat','demand','dead_health','momentum','forced_buyer','rating_score']
sc = StandardScaler()
X_multi = sc.fit_transform(df[components].values)
cv_single = cross_val_score(LogisticRegression(random_state=42,max_iter=1000), X, y, cv=5, scoring='roc_auc')
cv_multi  = cross_val_score(LogisticRegression(random_state=42,max_iter=1000), X_multi, y, cv=5, scoring='roc_auc')
print(f"\n=== CROSS-VALIDATED AUC ===")
print(f"  viability score only:  {cv_single.mean():.4f} +/- {cv_single.std():.4f}")
print(f"  all 8 components:      {cv_multi.mean():.4f} +/- {cv_multi.std():.4f}")

lr_multi = LogisticRegression(random_state=42,max_iter=1000).fit(X_multi, y)
coefs = pd.Series(lr_multi.coef_[0], index=components).sort_values(ascending=False)
print(f"\n=== COMPONENT IMPORTANCE (standardised coef) ===")
print(coefs.round(4).to_string())

print(f"\n=== HIT RATE + LIFT BY BAND ===")
for band,lo,hi in [('SCREEN OUT',0,41),('INVESTIGATE',42,46),('CONSIDER',47,51),('LAUNCH',52,100)]:
    sub = df[(df['viability']>=lo)&(df['viability']<=hi)]
    if len(sub)==0: continue
    hr = sub['success'].mean()
    lift = hr/br if br>0 else 0
    print(f"  {band:12s} (n={len(sub):3d}): hit={hr:.3f}  lift={lift:.2f}x  (base={br:.3f})")

# DATEV-type: n=0 competition, forced_buyer=70, rating=50(new), momentum=70(migrator)
datev = np.array([[90,60,80,50,85,70,70,50]])
datev_std = sc.transform(datev)
p_datev = lr_multi.predict_proba(datev_std)[0][1]
print(f"\n=== DATEV APP PROBABILITY ESTIMATE ===")
print(f"  Features: sat=90(zero comp), demand=60, gap=80, dead_health=50, moat=85, momentum=70(migrator), forced_buyer=70, rating=50(new)")
print(f"  P(success>=100 purchases) = {p_datev:.3f} ({p_datev*100:.1f}%)")
print(f"  vs base rate {br*100:.1f}%  ->  lift = {p_datev/br:.2f}x")
