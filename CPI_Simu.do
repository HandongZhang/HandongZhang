import excel using "E:\HuaweiMoveData\Users\Zhd\Desktop\CPI_detail1.xlsx", firstrow clear

* 1. 将字符串日期转换为 Stata 月度数值
gen month = monthly(日期, "YM")

* 2. 为这个新变量设置月度显示格式（显示为 2005m1 等）
format month %tm

* 3. 设定时间序列
tsset month, monthly


* 假设原始变量顺序与你列出的一致，按顺序重命名
rename (gas_weighted_avg CPI总指数周环比 现货价PTA 现货价铜 现货价热轧卷板 现货价锡 现货价螺纹钢 平均批发价28种重点监测蔬菜 平均批发价6种重点监测水果 平均批发价猪肉) (gas cpi pta copper hr_coil tin rebar veg fruit pork)

	   
foreach var in gas pta copper hr_coil tin rebar veg fruit pork {
    gen d_`var' = log(`var' / L.`var')
	}

* 生成通胀的月度变化（加速度），确保平稳
gen d_cpi = cpi - L.cpi

* 4. 生成自变量的滞后1期和滞后2期（捕捉价格传导时滞）
foreach var in gas pta copper hr_coil tin rebar veg fruit pork {
    gen d_`var'_l1 = L.d_`var'
    gen d_`var'_l2 = L2.d_`var'
}

* 运行LASSO线性回归，使用10折交叉验证选择最优lambda
lasso linear d_cpi d_gas d_gas_l1 d_gas_l2 d_pta d_pta_l1 d_pta_l2 d_copper d_copper_l1 d_copper_l2 d_hr_coil d_hr_coil_l1 d_hr_coil_l2 d_tin d_tin_l1 d_tin_l2 d_rebar d_rebar_l1 d_rebar_l2 d_veg d_veg_l1 d_veg_l2 d_fruit d_fruit_l1 d_fruit_l2 d_pork d_pork_l1 d_pork_l2, selection(cv)

* 查看最终被选中的变量及其系数（非零系数）
lassocoef

* 查看交叉验证的均方误差图（判断lambda选取是否合理）
cvplot

* 查看所有lambda取值下的系数变化路径
coefpath

* 将筛选后的模型预测值存下来，用于后续检验
predict y_hat



































