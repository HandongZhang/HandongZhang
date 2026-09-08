#%%
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split


df = pd.read_csv('cardio_train.csv', sep=';')
df['age_years'] = (df['age'] / 365.25).round(1)
df['bmi'] = df['weight'] / ((df['height'] / 100) ** 2)


df_clean = df[
    (df['ap_hi'] >= 80)
    & (df['ap_hi'] <= 220)
    & (df['ap_lo'] >= 50)
    & (df['ap_lo'] <= 140)
    & (df['ap_hi'] > df['ap_lo'])
    & (df['height'] >= 130)
    & (df['height'] <= 200)
    & (df['weight'] >= 30)
    & (df['weight'] <= 180)
].copy()


feature_cols = [
    'alco',
    'age_years',
    'gender',
    'bmi',
    'ap_hi',
    'ap_lo',
    'cholesterol',
    'gluc',
    'active',
]


# %%
def run_subgroup_analysis(data, group_name):
    X = data[feature_cols]
    y = data['cardio']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    # Logistic Regression
    lr = LogisticRegression(max_iter=1000, random_state=42)
    lr.fit(X_train, y_train)

    lr_coef_df = pd.DataFrame({
        'Feature': ['Intercept'] + feature_cols,
        'Coefficient': np.append(lr.intercept_, lr.coef_[0]),
        'Odds Ratio (OR)': np.exp(np.append(lr.intercept_, lr.coef_[0])),
    })

    # Random Forest
    rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    rf.fit(X_train, y_train)

    rf_imp_df = pd.DataFrame({
        'Feature': feature_cols,
        'Importance (%)': (rf.feature_importances_ * 100).round(2),
    }).sort_values(by='Importance (%)', ascending=False)

   
    y_pred_lr = lr.predict(X_test)
    y_pred_rf = rf.predict(X_test)

    metrics_df = pd.DataFrame(
        [
            [
                accuracy_score(y_test, y_pred_lr),
                precision_score(y_test, y_pred_lr),
                recall_score(y_test, y_pred_lr),
                f1_score(y_test, y_pred_lr),
            ],
            [
                accuracy_score(y_test, y_pred_rf),
                precision_score(y_test, y_pred_rf),
                recall_score(y_test, y_pred_rf),
                f1_score(y_test, y_pred_rf),
            ],
        ],
        columns=['Accuracy', 'Precision', 'Recall', 'F1-Score'],
        index=['Logistic Regression', 'Random Forest'],
    )

    return lr_coef_df, rf_imp_df, metrics_df


# %%
df_non_smokers = df_clean[df_clean['smoke'] == 0]
df_smokers = df_clean[df_clean['smoke'] == 1]

lr_ns, rf_ns, metrics_ns = run_subgroup_analysis(
    df_non_smokers, 'Non-Smokers'
)
lr_s, rf_s, metrics_s = run_subgroup_analysis(df_smokers, 'Smokers')

# %%
print('===================================================')
print('Logistic Coefficients & OR Comparison  ')
print('===================================================')
alco_comparison = pd.DataFrame({
    'Group': ['Non-Smokers', 'Smokers'],
    'Sample Size (N)': [len(df_non_smokers), len(df_smokers)],
    'Alco Coef': [
        lr_ns.loc[lr_ns['Feature'] == 'alco', 'Coefficient'].values[0],
        lr_s.loc[lr_s['Feature'] == 'alco', 'Coefficient'].values[0],
    ],
    'Alco Odds Ratio (OR)': [
        lr_ns.loc[lr_ns['Feature'] == 'alco', 'Odds Ratio (OR)'].values[0],
        lr_s.loc[lr_s['Feature'] == 'alco', 'Odds Ratio (OR)'].values[0],
    ],
})
print(alco_comparison.round(4).to_string(index=False))

print('\n===================================================')
print('Random Forest Importance Check')
print('===================================================')
rf_comparison = pd.merge(
    rf_ns, rf_s, on='Feature', suffixes=(' (non-smoker)', ' (smoker)')
)
print(rf_comparison.to_string(index=False))

print('\n===================================================')
print('Metrics comparison')
print('===================================================')
print('Non-Smokers')
print(metrics_ns.round(4))
print('\n(Smokers) Metrics')
print(metrics_s.round(4))



# %%
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import seaborn as sns


plt.style.use(
    'seaborn-v0_8-whitegrid'
    if 'seaborn-v0_8-whitegrid' in plt.style.available
    else 'default'
)
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

# pltting
plt.figure(figsize=(8, 6))
sns.violinplot(
    data=df_clean,
    x='smoke',
    y='ap_hi',
    hue='alco',
    split=True,
    inner='quartile',
    palette={0: '#5B9BD5', 1: '#ED7D31'},
)

plt.title(
    'Systolic BP (ap_hi) Distribution across Smoke & Alco',
    fontsize=13,
    fontweight='bold',
    pad=15,
)
plt.xlabel('Smoking Status', fontsize=11, fontweight='bold')
plt.ylabel('Systolic Blood Pressure (mmHg)', fontsize=11, fontweight='bold')
plt.xticks([0, 1], ['Non-Smokers', 'Smokers'])

blue_patch = mpatches.Patch(color='#5B9BD5', label='No Alcohol')
orange_patch = mpatches.Patch(color='#ED7D31', label='Alcohol')
plt.legend(
    handles=[blue_patch, orange_patch],
    title='Drinking (alco)',
    loc='upper right',
)

plt.tight_layout()
plt.savefig('violin_1_ap_hi.png', dpi=300)
plt.show()
# %%
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import seaborn as sns

plt.style.use(
    'seaborn-v0_8-whitegrid'
    if 'seaborn-v0_8-whitegrid' in plt.style.available
    else 'default'
)
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

plt.figure(figsize=(8, 6))
sns.violinplot(
    data=df_clean,
    x='smoke',
    y='ap_lo',
    hue='alco',
    split=True,
    inner='quartile',
    palette={0: '#5B9BD5', 1: '#ED7D31'},
)

plt.title(
    'Diastolic BP (ap_lo) Distribution across Smoke & Alco',
    fontsize=13,
    fontweight='bold',
    pad=15,
)
plt.xlabel('Smoking Status', fontsize=11, fontweight='bold')
plt.ylabel('Diastolic Blood Pressure (mmHg)', fontsize=11, fontweight='bold')
plt.xticks([0, 1], ['Non-Smokers', 'Smokers'])

blue_patch = mpatches.Patch(color='#5B9BD5', label='No Alcohol')
orange_patch = mpatches.Patch(color='#ED7D31', label='Alcohol')
plt.legend(
    handles=[blue_patch, orange_patch],
    title='Drinking (alco)',
    loc='upper right',
)

plt.tight_layout()
plt.savefig('violin_2_ap_lo.png', dpi=300)
plt.show()

# %%
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import seaborn as sns

plt.style.use(
    'seaborn-v0_8-whitegrid'
    if 'seaborn-v0_8-whitegrid' in plt.style.available
    else 'default'
)
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

plt.figure(figsize=(8, 6))
sns.violinplot(
    data=df_clean,
    x='smoke',
    y='cholesterol',
    hue='alco',
    split=True,
    inner='quartile',
    palette={0: '#5B9BD5', 1: '#ED7D31'},
)

plt.title(
    'Cholesterol Level Distribution across Smoke & Alco',
    fontsize=13,
    fontweight='bold',
    pad=15,
)
plt.xlabel('Smoking Status', fontsize=11, fontweight='bold')
plt.ylabel('Cholesterol Level (1: Normal, 2: Above, 3: High)', fontsize=11)
plt.xticks([0, 1], ['Non-Smokers', 'Smokers'])

blue_patch = mpatches.Patch(color='#5B9BD5', label='No Alcohol')
orange_patch = mpatches.Patch(color='#ED7D31', label='Alcohol')
plt.legend(
    handles=[blue_patch, orange_patch],
    title='Drinking (alco)',
    loc='upper right',
)

plt.tight_layout()
plt.savefig('violin_3_cholesterol.png', dpi=300)
plt.show()
# %%
