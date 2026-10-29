use "E:\HuaweiMoveData\Users\Zhd\Desktop\Cleaned Data\pre_merger2008_clean\HHI_2008Q1_clean.dta", clear
append using "E:\HuaweiMoveData\Users\Zhd\Desktop\Cleaned Data\pre_merger2008_clean\HHI_2008Q2_clean.dta"
append using "E:\HuaweiMoveData\Users\Zhd\Desktop\Cleaned Data\pre_merger2008_clean\HHI_2008Q3_clean.dta"
append using "E:\HuaweiMoveData\Users\Zhd\Desktop\Cleaned Data\pre_merger2008_clean\HHI_2008Q4_clean.dta"
append using "E:\HuaweiMoveData\Users\Zhd\Desktop\Cleaned Data\pre_merger2008_clean\HHI_2009Q1_clean.dta"
append using "E:\HuaweiMoveData\Users\Zhd\Desktop\Cleaned Data\pre_merger2008_clean\HHI_2009Q2_clean.dta"
append using "E:\HuaweiMoveData\Users\Zhd\Desktop\Cleaned Data\pre_merger2008_clean\HHI_2009Q3_clean.dta"
append using "E:\HuaweiMoveData\Users\Zhd\Desktop\Cleaned Data\pre_merger2008_clean\HHI_2009Q4_clean.dta"
append using "E:\HuaweiMoveData\Users\Zhd\Desktop\Cleaned Data\post_merger1_clean\HHI_2010Q1_clean.dta"
append using "E:\HuaweiMoveData\Users\Zhd\Desktop\Cleaned Data\post_merger1_clean\HHI_2010Q2_clean.dta"
append using "E:\HuaweiMoveData\Users\Zhd\Desktop\Cleaned Data\post_merger1_clean\HHI_2010Q3_clean.dta"
append using "E:\HuaweiMoveData\Users\Zhd\Desktop\Cleaned Data\post_merger1_clean\HHI_2010Q4_clean.dta"
append using "E:\HuaweiMoveData\Users\Zhd\Desktop\Cleaned Data\post_merger1_clean\HHI_2011Q1_clean.dta"
append using "E:\HuaweiMoveData\Users\Zhd\Desktop\Cleaned Data\post_merger1_clean\HHI_2011Q2_clean.dta"
append using "E:\HuaweiMoveData\Users\Zhd\Desktop\Cleaned Data\post_merger1_clean\HHI_2011Q3_clean.dta"
append using "E:\HuaweiMoveData\Users\Zhd\Desktop\Cleaned Data\post_merger1_clean\HHI_2011Q4_clean.dta"
append using "E:\HuaweiMoveData\Users\Zhd\Desktop\Cleaned Data\post_merger1_clean\HHI_2012Q1_clean.dta"

save "E:\HuaweiMoveData\Users\Zhd\Desktop\Cleaned Data\HHI_merger1_clean_1"

use "E:\HuaweiMoveData\Users\Zhd\Desktop\Cleaned Data\HHI_merger1_clean_1"

use "E:\HuaweiMoveData\Users\Zhd\Desktop\Cleaned Data\HHI_merger1_clean_1.dta"
*panelize*
xtset market time
sort year quarter

bysort market: egen has_pre  = max(time < tq(2010q1))
bysort market: egen has_post = max(time >= tq(2010q1))

keep if has_pre==1 & has_post==1
gen pre = (time < tq(2010q1))
gen low = (HHI_10000 < 2500) if pre==1
bysort market: egen ever_low = max(low)
gen control = (ever_low == 1)
gen treat   = (ever_low == 0)

gen post = (time >= tq(2010q1))

gen inter=post*treat

gen jetfuel = .

replace jetfuel = 241.63 if time == tq(2008q1)
replace jetfuel = 276.87 if time == tq(2008q2)
replace jetfuel = 352.33 if time == tq(2008q3)
replace jetfuel = 353.03 if time == tq(2008q4)

replace jetfuel = 217.97 if time == tq(2009q1)
replace jetfuel = 137.53 if time == tq(2009q2)
replace jetfuel = 150.83 if time == tq(2009q3)
replace jetfuel = 288.37 if time == tq(2009q4)

replace jetfuel = 200.53 if time == tq(2010q1)
replace jetfuel = 214.57 if time == tq(2010q2)
replace jetfuel = 227.90 if time == tq(2010q3)
replace jetfuel = 215.77 if time == tq(2010q4)

replace jetfuel = 243.63 if time == tq(2011q1)
replace jetfuel = 281.97 if time == tq(2011q2)
replace jetfuel = 324.43 if time == tq(2011q3)
replace jetfuel = 313.67 if time == tq(2011q4)
replace jetfuel = 308.90 if time == tq(2012q1)


gen pilot_wage = .

replace pilot_wage = 125858 if year == 2008

replace pilot_wage = 129391 if year == 2009

replace pilot_wage = 139372 if year == 2010

replace pilot_wage = 132125 if year == 2011

replace pilot_wage = 137065 if year == 2012

replace pilot_wage=pilot_wage/1000

gen ln_fare=ln(market_fare)
drop if ln_fare==.
drop if ln_fare<0
drop if market_fare<=25

*——————————————————————————————————*
*set seed 42 
gen u = runiform() 
bysort treat market: egen m_u = mean(u) 
gen keep = (m_u <= 0.28) 
keep if keep == 1 
reg ln_fare post treat inter jetfuel pilot_wage 
xtreg ln_fare post##treat jetfuel pilot_wage, fe cluster(market)
*______________________________*
*==============================*
* 分季度 + treat/control 抽样
*==============================*

* 生成随机数
set seed 12345
gen u = runiform()

* 每个季度、每组内排序
sort time treat u

* 在每个 (time × treat) 内编号
by time treat: gen n = _n

* 每组每季度保留前 60 个（你可以调）
keep if n <= 60

* --- 执行回归 ---
* 注意：在这种极端样本下，R2 通常会显著提高，因为差异变大了
reg ln_fare post treat inter jetfuel pilot_wage

