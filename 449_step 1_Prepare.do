* import data*
import delimited "E:\HuaweiMoveData\Users\Zhd\Desktop\Raw Data\post_merger_1\T_DB1B_MARKET_2012Q1.csv", clear

* market *
egen market = group(origin_city_market_id dest_city_market_id)

* average*
gen fare_weighted = market_fare * passengers

* carrier-level *
collapse (sum) passengers fare_weighted, by(year quarter market reporting_carrier)

* rename *
rename passengers pax

*avg mkt level *
gen market_fare = fare_weighted / pax

* total passengers *
bysort year quarter market: egen total = sum(pax)

* share *
gen share = pax / total

* HHI *
gen share2 = share^2
bysort year quarter market: egen HHI = sum(share2)

* market-level *
collapse (mean) market_fare HHI total, by(year quarter market)

* standard HHI *
gen HHI_10000 = HHI * 10000

gen time = yq(year, quarter)
format time %tq

sort market time

save "E:\HuaweiMoveData\Users\Zhd\Desktop\Cleaned Data\post_merger1_clean\HHI_2012Q1_clean.dta"

