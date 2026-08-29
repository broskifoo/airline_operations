# Data Profile Report: BTS DB1B 2024 Q1

**Source**: DB1B Market (10% sample) & Coupon (10% sample)
**Quarter**: 2024 Q1

---

## DB1B Market 2024 Q1

**Sample Rows**: 50,000
**Columns**: 42

### Columns & Types

| Column | Type | Missing % | Unique |
|--------|------|-----------|--------|
| ItinID | int64 | 0.00% | 29,335 |
| MktID | int64 | 0.00% | 50,000 |
| MktCoupons | int64 | 0.00% | 4 |
| Year | int64 | 0.00% | 1 |
| Quarter | int64 | 0.00% | 1 |
| OriginAirportID | int64 | 0.00% | 104 |
| OriginAirportSeqID | int64 | 0.00% | 104 |
| OriginCityMarketID | int64 | 0.00% | 90 |
| Origin | object | 0.00% | 104 |
| OriginCountry | object | 0.00% | 1 |
| OriginStateFips | int64 | 0.00% | 43 |
| OriginState | object | 0.00% | 43 |
| OriginStateName | object | 0.00% | 43 |
| OriginWac | int64 | 0.00% | 43 |
| DestAirportID | int64 | 0.00% | 107 |
| DestAirportSeqID | int64 | 0.00% | 107 |
| DestCityMarketID | int64 | 0.00% | 93 |
| Dest | object | 0.00% | 107 |
| DestCountry | object | 0.00% | 1 |
| DestStateFips | int64 | 0.00% | 43 |
| DestState | object | 0.00% | 43 |
| DestStateName | object | 0.00% | 43 |
| DestWac | int64 | 0.00% | 43 |
| AirportGroup | object | 0.00% | 2,755 |
| WacGroup | object | 0.00% | 1,406 |
| TkCarrierChange | float64 | 0.00% | 2 |
| TkCarrierGroup | object | 0.00% | 12 |
| OpCarrierChange | float64 | 0.00% | 2 |
| OpCarrierGroup | object | 0.00% | 12 |
| RPCarrier | object | 0.00% | 1 |
| TkCarrier | object | 0.00% | 3 |
| OpCarrier | object | 0.00% | 3 |
| BulkFare | float64 | 0.00% | 1 |
| Passengers | float64 | 0.00% | 76 |
| MktFare | float64 | 0.00% | 11,686 |
| MktDistance | float64 | 0.00% | 1,380 |
| MktDistanceGroup | int64 | 0.00% | 11 |
| MktMilesFlown | float64 | 0.00% | 1,313 |
| NonStopMiles | float64 | 0.00% | 553 |
| ItinGeoType | int64 | 0.00% | 2 |
| MktGeoType | int64 | 0.00% | 2 |
| Unnamed: 41 | float64 | 100.00% | 0 |

### Numeric Column Statistics


**ItinID**:
- Mean: 202414846899.88
- Std: 8710.01
- Min: 202414832047.00
- Max: 202414861966.00

**MktID**:
- Mean: 20241484689989.76
- Std: 871001.03
- Min: 20241483204701.00
- Max: 20241486196601.00

**MktCoupons**:
- Mean: 1.47
- Std: 0.52
- Min: 1.00
- Max: 4.00

**Year**:
- Mean: 2024.00
- Std: 0.00
- Min: 2024.00
- Max: 2024.00

**Quarter**:
- Mean: 1.00
- Std: 0.00
- Min: 1.00
- Max: 1.00

**OriginAirportID**:
- Mean: 11813.51
- Std: 1619.09
- Min: 10140.00
- Max: 15624.00

**OriginAirportSeqID**:
- Mean: 1181354.25
- Std: 161908.55
- Min: 1014005.00
- Max: 1562404.00

**OriginCityMarketID**:
- Mean: 31360.08
- Std: 1142.63
- Min: 30140.00
- Max: 34986.00

**OriginStateFips**:
- Mean: 26.12
- Std: 14.91
- Min: 1.00
- Max: 72.00

**OriginWac**:
- Mean: 51.18
- Std: 28.53
- Min: 2.00
- Max: 93.00

**DestAirportID**:
- Mean: 12274.02
- Std: 1739.27
- Min: 10140.00
- Max: 15624.00

**DestAirportSeqID**:
- Mean: 1227405.08
- Std: 173926.55
- Min: 1014005.00
- Max: 1562404.00

**DestCityMarketID**:
- Mean: 31591.68
- Std: 1280.00
- Min: 30140.00
- Max: 35096.00

**DestStateFips**:
- Mean: 24.87
- Std: 15.68
- Min: 1.00
- Max: 72.00

**DestWac**:
- Mean: 54.34
- Std: 27.77
- Min: 2.00
- Max: 93.00

**TkCarrierChange**:
- Mean: 0.00
- Std: 0.06
- Min: 0.00
- Max: 1.00

**OpCarrierChange**:
- Mean: 0.00
- Std: 0.06
- Min: 0.00
- Max: 1.00

**BulkFare**:
- Mean: 0.00
- Std: 0.00
- Min: 0.00
- Max: 0.00

**Passengers**:
- Mean: 1.60
- Std: 4.87
- Min: 1.00
- Max: 300.00

**MktFare**:
- Mean: 213.82
- Std: 123.12
- Min: 0.00
- Max: 975.30

**MktDistance**:
- Mean: 1251.42
- Std: 672.07
- Min: 220.00
- Max: 5137.00

**MktDistanceGroup**:
- Mean: 3.01
- Std: 1.34
- Min: 1.00
- Max: 11.00

**MktMilesFlown**:
- Mean: 1250.67
- Std: 671.83
- Min: 0.00
- Max: 5137.00

**NonStopMiles**:
- Mean: 1184.56
- Std: 645.55
- Min: 220.00
- Max: 4744.00

**ItinGeoType**:
- Mean: 1.97
- Std: 0.16
- Min: 1.00
- Max: 2.00

**MktGeoType**:
- Mean: 1.97
- Std: 0.16
- Min: 1.00
- Max: 2.00

**Unnamed: 41**:
- Mean: nan
- Std: nan
- Min: nan
- Max: nan

### Top Categorical Values


**Origin**:
  - BUF: 7,785
  - BNA: 7,514
  - BOI: 6,708
  - BOS: 6,258
  - BUR: 1,903

**OriginCountry**:
  - US: 50,000

**OriginState**:
  - NY: 7,845
  - TN: 7,538
  - ID: 6,708
  - MA: 6,258
  - FL: 5,512

**OriginStateName**:
  - New York: 7,845
  - Tennessee: 7,538
  - Idaho: 6,708
  - Massachusetts: 6,258
  - Florida: 5,512

**Dest**:
  - BNA: 5,932
  - BUF: 5,571
  - BOI: 4,819
  - BOS: 3,654
  - PHX: 2,200

**DestCountry**:
  - US: 50,000

**DestState**:
  - FL: 7,330
  - TN: 5,981
  - CA: 5,904
  - NY: 5,720
  - ID: 4,819

**DestStateName**:
  - Florida: 7,330
  - Tennessee: 5,981
  - California: 5,904
  - New York: 5,720
  - Idaho: 4,819

**AirportGroup**:
  - BUF:MCO: 1,100
  - BNA:PHX: 1,007
  - MCO:BUF: 874
  - BNA:TPA: 841
  - PHX:BNA: 766

**WacGroup**:
  - 22:33: 2,538
  - 54:33: 2,016
  - 33:22: 1,999
  - 33:54: 1,504
  - 22:35:33: 1,044

---

## DB1B Coupon 2024 Q1

**Sample Rows**: 50,000
**Columns**: 37

### Columns & Types

| Column | Type | Missing % | Unique |
|--------|------|-----------|--------|
| ItinID | int64 | 0.00% | 50,000 |
| MktID | int64 | 0.00% | 50,000 |
| SeqNum | int64 | 0.00% | 1 |
| Coupons | int64 | 0.00% | 1 |
| Year | int64 | 0.00% | 1 |
| OriginAirportID | int64 | 0.00% | 352 |
| OriginAirportSeqID | int64 | 0.00% | 352 |
| OriginCityMarketID | int64 | 0.00% | 331 |
| Quarter | int64 | 0.00% | 1 |
| Origin | object | 0.00% | 352 |
| OriginCountry | object | 0.00% | 1 |
| OriginStateFips | int64 | 0.00% | 52 |
| OriginState | object | 0.00% | 52 |
| OriginStateName | object | 0.00% | 52 |
| OriginWac | int64 | 0.00% | 52 |
| DestAirportID | int64 | 0.00% | 123 |
| DestAirportSeqID | int64 | 0.00% | 123 |
| DestCityMarketID | int64 | 0.00% | 106 |
| Dest | object | 0.00% | 123 |
| DestCountry | object | 0.00% | 1 |
| DestStateFips | int64 | 0.00% | 45 |
| DestState | object | 0.00% | 45 |
| DestStateName | object | 0.00% | 45 |
| DestWac | int64 | 0.00% | 45 |
| Break | object | 96.72% | 1 |
| CouponType | object | 0.00% | 2 |
| TkCarrier | object | 0.00% | 17 |
| OpCarrier | object | 0.00% | 28 |
| RPCarrier | object | 0.00% | 22 |
| Passengers | float64 | 0.00% | 10 |
| FareClass | object | 0.00% | 6 |
| Distance | float64 | 0.00% | 1,335 |
| DistanceGroup | int64 | 0.00% | 11 |
| Gateway | float64 | 0.00% | 1 |
| ItinGeoType | int64 | 0.00% | 2 |
| CouponGeoType | int64 | 0.00% | 2 |
| Unnamed: 36 | float64 | 100.00% | 0 |

### Numeric Column Statistics


**ItinID**:
- Mean: 169340983996.13
- Std: 70860912948.06
- Min: 202415500.00
- Max: 202415987302.00

**MktID**:
- Mean: 16934098399613.70
- Std: 7086091294805.73
- Min: 20241550001.00
- Max: 20241598730201.00

**SeqNum**:
- Mean: 1.00
- Std: 0.00
- Min: 1.00
- Max: 1.00

**Coupons**:
- Mean: 4.00
- Std: 0.00
- Min: 4.00
- Max: 4.00

**Year**:
- Mean: 2024.00
- Std: 0.00
- Min: 2024.00
- Max: 2024.00

**OriginAirportID**:
- Mean: 12823.60
- Std: 1611.43
- Min: 10135.00
- Max: 16869.00

**OriginAirportSeqID**:
- Mean: 1282363.84
- Std: 161142.46
- Min: 1013506.00
- Max: 1686902.00

**OriginCityMarketID**:
- Mean: 32146.88
- Std: 1457.45
- Min: 30009.00
- Max: 36101.00

**Quarter**:
- Mean: 1.00
- Std: 0.00
- Min: 1.00
- Max: 1.00

**OriginStateFips**:
- Mean: 29.02
- Std: 16.42
- Min: 1.00
- Max: 78.00

**OriginWac**:
- Mean: 54.40
- Std: 25.20
- Min: 1.00
- Max: 93.00

**DestAirportID**:
- Mean: 12016.19
- Std: 1427.47
- Min: 10140.00
- Max: 15919.00

**DestAirportSeqID**:
- Mean: 1201623.67
- Std: 142746.36
- Min: 1014005.00
- Max: 1591905.00

**DestCityMarketID**:
- Mean: 30992.71
- Std: 947.23
- Min: 30113.00
- Max: 35412.00

**DestStateFips**:
- Mean: 27.44
- Std: 16.51
- Min: 1.00
- Max: 78.00

**DestWac**:
- Mean: 56.56
- Std: 23.20
- Min: 1.00
- Max: 93.00

**Passengers**:
- Mean: 1.04
- Std: 0.29
- Min: 1.00
- Max: 11.00

**Distance**:
- Mean: 736.11
- Std: 574.04
- Min: 67.00
- Max: 5095.00

**DistanceGroup**:
- Mean: 1.97
- Std: 1.16
- Min: 1.00
- Max: 11.00

**Gateway**:
- Mean: 0.00
- Std: 0.00
- Min: 0.00
- Max: 0.00

**ItinGeoType**:
- Mean: 1.91
- Std: 0.28
- Min: 1.00
- Max: 2.00

**CouponGeoType**:
- Mean: 1.98
- Std: 0.15
- Min: 1.00
- Max: 2.00

**Unnamed: 36**:
- Mean: nan
- Std: nan
- Min: nan
- Max: nan

### Top Categorical Values


**Origin**:
  - RDU: 903
  - BOS: 882
  - DTW: 768
  - MSP: 743
  - PDX: 735

**OriginCountry**:
  - US: 50,000

**OriginState**:
  - CA: 4,727
  - FL: 3,760
  - TX: 3,528
  - NY: 2,214
  - VA: 2,081

**OriginStateName**:
  - California: 4,727
  - Florida: 3,760
  - Texas: 3,528
  - New York: 2,214
  - Virginia: 2,081

**Dest**:
  - ATL: 7,732
  - DFW: 6,205
  - CLT: 5,878
  - DEN: 5,516
  - ORD: 3,652

**DestCountry**:
  - US: 50,000

**DestState**:
  - TX: 9,324
  - GA: 7,734
  - NC: 5,902
  - CO: 5,523
  - IL: 4,527

**DestStateName**:
  - Texas: 9,324
  - Georgia: 7,734
  - North Carolina: 5,902
  - Colorado: 5,523
  - Illinois: 4,527

**Break**:
  - X: 1,639

**CouponType**:
  - A: 49,942
  - D: 58

---
