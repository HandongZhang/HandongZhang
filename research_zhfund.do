log using research_0, replace

import excel using "E:\HuaweiMoveData\Users\Zhd\Desktop\宏观数据.xlsx", sheet("中国_制造业PMI") firstrow clear

rename 指标名称 time

tsset time, daily



tsline 中国制造业PMI, xtitle(time)
graph export "E:\HuaweiMoveData\Users\Zhd\Desktop\pmi", replace

rename 中国工业增加值规模以上工业企业当月同比12月合并 工业增加值
tsline 工业增加值, xtitle(time)
graph export "E:\HuaweiMoveData\Users\Zhd\Desktop\工业增加值", replace

rename 中国固定资产投资完成额累计同比 固定资产


**********CPI公布对于当月市场波动************
import excel using "E:\HuaweiMoveData\Users\Zhd\Desktop\中债国债收益率曲线.xlsx", sheet("Sheet1") firstrow clear
tempfile master1
save `master1'
import excel using "E:\HuaweiMoveData\Users\Zhd\Desktop\银行间质押式回购（资金数据）", sheet("Sheet1") firstrow clear

merge 1:1 指标名称 using `master1' 
keep if _merge == 3   
drop _merge    

*****************
tempfile master2
save `master2'

import excel using "E:\HuaweiMoveData\Users\Zhd\Desktop\农产品批发价格200指数_20260616_230606.xlsx", sheet("Sheet1") firstrow clear

merge 1:1 指标名称 using `master2'
keep if _merge == 3
drop _merge
*********************

rename 指标名称 time
gen double time_num = date(time, "DMY")
format time_num %td
drop time
rename time_num time
tsset time, daily

gen t_order = _n

tsset t_order
drop if time<td(15dec2014)

*收益率差值分析*
gen diff1_3 = 中债国债到期收益率3年-中债国债到期收益率1年
gen diff3_5 = 中债国债到期收益率5年-中债国债到期收益率3年
gen diff5_10 = 中债国债到期收益率10年-中债国债到期收益率5年
gen diff10_30 = 中债国债到期收益率30年-中债国债到期收益率10年


rename 农产品批发价格200指数 农产品

tsline 农产品/100 中债国债到期收益率1年 DR007

**预测一年期**
*ardl 中债国债到期收益率1年 DR007 农index,maxlag(7) aic ec
*estat ectest

gen 农_index=农产品批发价格200指数/100
gen d_国债 = D.中债国债到期收益率1年
gen d_农index = D.农index


* 最优滞后阶数选择（针对这些平稳变量）*
varsoc d_国债 DR007 d_农index, maxlag(8)

var d_国债 DR007 d_农index,lags(1/8)
varstable, graph

fcast compute f_, step(10)
tsline d_国债 f_d_国债 if t_order>=4800, title("1年期国债利率 VAR 预测")
********************************************
**3/5/10国债预测**
*tsline 中债国债到期收益率1年 中债国债到期收益率3年 中债国债到期收益率5年 中债国债到期收益率10年 中债国债到期收益率30年, xtitle(time)





dfuller 中债国债到期收益率1年
dfuller 中债国债到期收益率5年
dfuller 中债国债到期收益率10年


varsoc 中债国债到期收益率1年 中债国债到期收益率5年 中债国债到期收益率10年, maxlag(5)
vecrank 中债国债到期收益率1年 中债国债到期收益率5年 中债国债到期收益率10年,lags(3) max ic 

rename 中债国债到期收益率5年 rate1
rename 中债国债到期收益率10年 rate5
rename 中债国债到期收益率30年 rate10

vec rate1 rate5 rate10, rank(2) lags(3)

vecstable,graph

fcast compute f_, step(10)
tsline rate3 f_rate5 if t_order>=2600, title("5年期国债利率 VECM 预测")














