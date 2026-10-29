log using ECON483_FinProj, replace

import fred IR IQ

gen time = mofd(daten)
tsset time, monthly
drop if time<tm(1988m12)

*missing dta IR*
ipolate IR time, gen(IR_i)
replace IR=IR_i if missing(IR)
drop IR_i

ipolate IQ time, gen(IQ_i)
replace IQ=IQ_i if missing(IQ)
drop IQ_i

dfuller ann_ch_ir,lag(12)

*annualized change*
gen ann_ch_ir=(IR-L.IR)/L.IR*12*100

gen ann_ch_iq=(IQ-L.IQ)/L.IQ*12*100

*regression*
reg ann_ch_ir L.ann_ch_ir if time>=tm(1990m1)
estimates store ir1

reg ann_ch_ir L(1/2).ann_ch_ir if time>=tm(1990m1)
estimates store ir2

reg ann_ch_ir L(1/3).ann_ch_ir if time>=tm(1990m1)
estimates store ir3

reg ann_ch_ir L(1/4).ann_ch_ir if time>=tm(1990m1)
estimates store ir4

reg ann_ch_ir L(1/5).ann_ch_ir if time>=tm(1990m1)
estimates store ir5

reg ann_ch_ir L(1/6).ann_ch_ir if time>=tm(1990m1)
estimates store ir6

reg ann_ch_ir L(1/7).ann_ch_ir if time>=tm(1990m1)
estimates store ir7

reg ann_ch_ir L(1/8).ann_ch_ir if time>=tm(1990m1)
estimates store ir8

reg ann_ch_ir L(1/9).ann_ch_ir if time>=tm(1990m1)
estimates store ir9

reg ann_ch_ir L(1/10).ann_ch_ir if time>=tm(1990m1)
estimates store ir10

reg ann_ch_ir L(1/11).ann_ch_ir if time>=tm(1990m1)
estimates store ir11

reg ann_ch_ir L(1/12).ann_ch_ir if time>=tm(1990m1)
estimates store ir12
estimates stats ir1 ir2 ir3 ir4 ir5 ir6 ir7 ir8 ir9 ir10 ir11 ir12

*Choose ir12, w/ lowest AIC*

*Decide indicating variable*
reg ann_ch_ir L(1/12).ann_ch_ir L.ann_ch_iq if time>=tm(1990m1)
estimates store mix1

reg ann_ch_ir L(1/12).ann_ch_ir L(1/2).ann_ch_iq if time>=tm(1990m1)
estimates store mix2

reg ann_ch_ir L(1/12).ann_ch_ir L(1/3).ann_ch_iq if time>=tm(1990m1)
estimates store mix3

reg ann_ch_ir L(1/12).ann_ch_ir L(1/4).ann_ch_iq if time>=tm(1990m1)
estimates store mix4

reg ann_ch_ir L(1/12).ann_ch_ir L(1/5).ann_ch_iq if time>=tm(1990m1)
estimates store mix5

reg ann_ch_ir L(1/12).ann_ch_ir L(1/6).ann_ch_iq if time>=tm(1990m1)
estimates store mix6

reg ann_ch_ir L(1/12).ann_ch_ir L(1/6).ann_ch_iq if time>=tm(1990m1)
estimates store mix6

reg ann_ch_ir L(1/12).ann_ch_ir L(1/7).ann_ch_iq if time>=tm(1990m1)
estimates store mix7

reg ann_ch_ir L(1/12).ann_ch_ir L(1/8).ann_ch_iq if time>=tm(1990m1)
estimates store mix8

reg ann_ch_ir L(1/12).ann_ch_ir L(1/9).ann_ch_iq if time>=tm(1990m1)
estimates store mix9

reg ann_ch_ir L(1/12).ann_ch_ir L(1/10).ann_ch_iq if time>=tm(1990m1)
estimates store mix10

reg ann_ch_ir L(1/12).ann_ch_ir L(1/11).ann_ch_iq if time>=tm(1990m1)
estimates store mix11

reg ann_ch_ir L(1/12).ann_ch_ir L(1/12).ann_ch_iq if time>=tm(1990m1)
estimates store mix12

estimates stats mix1 mix2 mix3 mix4 mix5 mix6 mix7 mix8 mix9 mix10 mix11 mix12

*Choose mix2*
*1 period ahead*
tsappend, add(6)
reg ann_ch_ir L(1/12).ann_ch_ir L(1/2).ann_ch_iq
predict res, residual
tsline res
 
predict ann_ch_pre1 if time>tm(2026m2)
predict sd1, stdf

*50%*
gen UCI_ann1_50 = ann_ch_pre1+0.67*sd1
gen LCI_ann1_50 = ann_ch_pre1-0.67*sd1

*80%*
gen UCI_ann1_80 = ann_ch_pre1+1.28*sd1
gen LCI_ann1_80 = ann_ch_pre1-1.28*sd1

*2 period ahead*
reg ann_ch_ir L(2/13).ann_ch_ir L(2/3).ann_ch_iq

predict ann_ch_pre2 if time>tm(2026m3)
predict sd2, stdf

*50%
gen UCI_ann2_50 = ann_ch_pre2+0.67*sd2
gen LCI_ann2_50 = ann_ch_pre2-0.67*sd2

*80%*
gen UCI_ann2_80 = ann_ch_pre2+1.28*sd2
gen LCI_ann2_80 = ann_ch_pre2-1.28*sd2

*3 period ahead*
reg ann_ch_ir L(3/14).ann_ch_ir L(3/4).ann_ch_iq

predict ann_ch_pre3 if time>tm(2026m4)
predict sd3, stdf

*50%
gen UCI_ann3_50 = ann_ch_pre3+0.67*sd3
gen LCI_ann3_50 = ann_ch_pre3-0.67*sd3

*80%*
gen UCI_ann3_80 = ann_ch_pre3+1.28*sd3
gen LCI_ann3_80 = ann_ch_pre3-1.28*sd3

*4 period ahead*
reg ann_ch_ir L(4/15).ann_ch_ir L(4/5).ann_ch_iq

predict ann_ch_pre4 if time>tm(2026m5)
predict sd4, stdf

*50%
gen UCI_ann4_50 = ann_ch_pre4+0.67*sd4
gen LCI_ann4_50 = ann_ch_pre4-0.67*sd4

*80%*
gen UCI_ann4_80 = ann_ch_pre4+1.28*sd4
gen LCI_ann4_80 = ann_ch_pre4-1.28*sd4

*5 period ahead*
reg ann_ch_ir L(5/16).ann_ch_ir L(5/6).ann_ch_iq

predict ann_ch_pre5 if time>tm(2026m6)
predict sd5, stdf

*50%
gen UCI_ann5_50 = ann_ch_pre5+0.67*sd5
gen LCI_ann5_50 = ann_ch_pre5-0.67*sd5

*80%*
gen UCI_ann5_80 = ann_ch_pre5+1.28*sd5
gen LCI_ann5_80 = ann_ch_pre5-1.28*sd5

*6 period ahead*
reg ann_ch_ir L(6/17).ann_ch_ir L(6/7).ann_ch_iq

predict ann_ch_pre6 if time>tm(2026m7)
predict sd6, stdf

*50%
gen UCI_ann6_50 = ann_ch_pre6+0.67*sd6
gen LCI_ann6_50 = ann_ch_pre6-0.67*sd6

*80%*
gen UCI_ann6_80 = ann_ch_pre6+1.28*sd6
gen LCI_ann6_80 = ann_ch_pre6-1.28*sd6

egen ann_ch_pre = rowfirst(ann_ch_pre1 ann_ch_pre2 ann_ch_pre3 ann_ch_pre4 ann_ch_pre5 ann_ch_pre6)
egen Uann_ch_50 = rowfirst(UCI_ann1_50 UCI_ann2_50 UCI_ann3_50 UCI_ann4_50 UCI_ann5_50 UCI_ann6_50)
egen Lann_ch_50 = rowfirst(LCI_ann1_50 LCI_ann2_50 LCI_ann3_50 LCI_ann4_50 LCI_ann5_50 LCI_ann6_50)

egen Uann_ch_80 = rowfirst(UCI_ann1_80 UCI_ann2_80 UCI_ann3_80 UCI_ann4_80 UCI_ann5_80 UCI_ann6_80)
egen Lann_ch_80 = rowfirst(LCI_ann1_80 LCI_ann2_80 LCI_ann3_80 LCI_ann4_80 LCI_ann5_80 LCI_ann6_80)

tsline ann_ch_ir ann_ch_pre Uann_ch_50 Lann_ch_50 Uann_ch_80 Lann_ch_80 if time>=tm(2025m5)
