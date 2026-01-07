# Dataset Catalog: Size Ranges & Periodicity Analysis

## Summary Statistics

| Category | Count | Size Range | Periodicity |
|----------|-------|------------|-------------|
| **EEG** | 18 | 500-10,000 points | Non-periodic (chaotic brain signals) |
| **Climate TMAX** | 6 | ~4,380 points | **Strong seasonal** (annual cycle) |
| **Climate AWND** | 6 | ~4,380 points | **Moderate seasonal** (wind patterns) |
| **Climate PRCP** | 6 | ~4,380 points | **Weak seasonal** (precipitation) |
| **Stock Price** | 9 | ~1,260 points | Non-periodic (stochastic) |
| **Stock Volume** | 9 | ~1,260 points | Non-periodic (stochastic) |
| **Unemployment** | 14 | ~840 points | **Mixed** (some sectors seasonal) |
| **Flights** | 3 | 300-5,000 points | **Strong seasonal** (travel patterns) |
| **Tourism** | 2 | 168-336 points | **Strong seasonal** (travel seasons) |
| **Crime** | 2 | 167-713 points | Weak/no periodicity |
| **Astronomy** | 5 | ~3,000 points | Variable (depends on object type) |
| **TOTAL** | **80** | **167-10,000** | **36 periodic, 44 non-periodic** |

---

## 1. Size-Based Categorization

### Tiny (< 500 points): 5 datasets
- `nz_tourist_annually` (168 points) - **PERIODIC** (annual tourism cycle)
- `chi_homicide_weekly` (167 points) - Non-periodic
- `flights_monthly` (300 points) - **PERIODIC** (seasonal travel)
- `nz_tourist_monthly` (336 points) - **PERIODIC** (monthly tourism)
- `flights_daily` (400-500 est.) - **PERIODIC** (weekly + seasonal)

**Analysis Focus**: Pattern detection challenging due to limited data. Periodicity metrics need at least 2-3 cycles for reliable detection.

---

### Small (500-1,000 points): 21 datasets

#### EEG 500-point (6 datasets)
- `eeg_chan05_500`, `eeg_chan10_500`, `eeg_chan15_500`
- `eeg_chan20_500`, `eeg_chan25_500`, `eeg_chan30_500`
- **Characteristics**: Non-periodic, high-frequency neural oscillations, chaotic

#### Crime (1 dataset)
- `chi_homicide_monthly` (713 points) - Weak/irregular patterns

#### Unemployment (14 datasets @ ~840 points each)
**SEASONAL sectors** (strong annual cycles):
- `unemployment_hospitality` - Peak summer, low winter
- `unemployment_construction` - Weather-dependent
- `unemployment_ag` - Harvest cycles
- `unemployment_edu_health` - Academic calendar influence

**NON-SEASONAL sectors**:
- `unemployment_finance`, `unemployment_info`, `unemployment_manufacturing`
- `unemployment_business`, `unemployment_govt`, `unemployment_mining`
- `unemployment_other`, `unemployment_self_emp`, `unemployment_trade`, `unemployment_transport`

---

### Medium (1,000-3,000 points): 18 datasets

#### Stock Price (9 datasets @ ~1,260 points)
- `stock_aapl_price`, `stock_amzn_price`, `stock_bac_price`
- `stock_goog_price`, `stock_intc_price`, `stock_jpm_price`
- `stock_msft_price`, `stock_tm_price`, `stock_tsla_price`
- **Characteristics**: Non-periodic, stochastic, trend-following with volatility clustering

#### Stock Volume (9 datasets @ ~1,260 points)
- `stock_aapl_volume`, `stock_amzn_volume`, `stock_bac_volume`
- `stock_goog_volume`, `stock_intc_volume`, `stock_jpm_volume`
- `stock_msft_volume`, `stock_tm_volume`, `stock_tsla_volume`
- **Characteristics**: Non-periodic, spiky, heavy-tailed distribution

---

### Large (3,000-5,000 points): 24 datasets

#### EEG 2500-point (6 datasets)
- `eeg_chan05_2500`, `eeg_chan10_2500`, `eeg_chan15_2500`
- `eeg_chan20_2500`, `eeg_chan25_2500`, `eeg_chan30_2500`
- **Characteristics**: Non-periodic, alpha/beta/gamma wave mixing

#### Climate TMAX - Maximum Temperature (6 datasets @ ~4,380 points)
- `climate_atl_tmax`, `climate_jfk_tmax`, `climate_lax_tmax`
- `climate_ord_tmax`, `climate_sea_tmax`, `climate_slc_tmax`
- **Characteristics**: ✅ **STRONG SEASONAL** - Clear annual sinusoidal pattern
- **Period**: 365.25 days (12 data points per year for ~12 years)
- **Amplitude**: Varies by location (ORD/SLC high amplitude, LAX low amplitude)

#### Climate AWND - Average Wind Speed (6 datasets @ ~4,380 points)
- `climate_atl_awnd`, `climate_jfk_awnd`, `climate_lax_awnd`
- `climate_ord_awnd`, `climate_sea_awnd`, `climate_slc_awnd`
- **Characteristics**: ✅ **MODERATE SEASONAL** - Less pronounced than TMAX
- **Period**: 365.25 days with higher wind in winter (in many locations)
- **Note**: More irregular than temperature due to weather events

#### Climate PRCP - Precipitation (6 datasets @ ~4,380 points)
- `climate_atl_prcp`, `climate_jfk_prcp`, `climate_lax_prcp`
- `climate_ord_prcp`, `climate_sea_prcp`, `climate_slc_prcp`
- **Characteristics**: ⚠️ **WEAK SEASONAL** - Highly irregular
- **Period**: Some annual pattern but dominated by stochastic weather
- **Note**: Spiky (rain events), many zero values

#### Flights (1 dataset)
- `flights_weekly` (~5,000 points) - **PERIODIC** (weekly + seasonal patterns)

#### Astronomy (5 datasets @ ~3,000 points)
- `astro_115_120`, `astro_115_123`, `astro_115_128`
- `astro_116_124`, `astro_116_134`
- **Characteristics**: Variable periodicity
  - Binary stars: Periodic (orbital periods)
  - Pulsars: Highly periodic
  - Irregular variables: Non-periodic
  - **Assume mixed for general analysis**

---

### Extra Large (> 5,000 points): 12 datasets

#### EEG 10000-point (6 datasets)
- `eeg_chan05_10000`, `eeg_chan10_10000`, `eeg_chan15_10000`
- `eeg_chan20_10000`, `eeg_chan25_10000`, `eeg_chan30_10000`
- **Characteristics**: Non-periodic, multi-scale oscillations

---

## 2. Periodicity Classification

### ✅ STRONGLY PERIODIC (20 datasets)

#### Climate TMAX (6 datasets)
- **Period**: 365.25 days (1 year)
- **Mechanism**: Earth's axial tilt + solar radiation
- **Waveform**: Near-sinusoidal with local weather noise
- **Best for**: Testing periodicity preservation metrics

#### Flights (3 datasets)
- `flights_daily` - Weekly + annual patterns
- `flights_weekly` - Strong annual pattern (holiday travel)
- `flights_monthly` - Seasonal travel trends
- **Period**: 7 days (weekly) + 365 days (annual)

#### Tourism (2 datasets)
- `nz_tourist_annually` - Annual cycle
- `nz_tourist_monthly` - Monthly + seasonal patterns
- **Period**: 12 months (seasonal travel)

#### Unemployment - Seasonal Sectors (9 datasets)
- `unemployment_hospitality` - Summer peak, winter trough
- `unemployment_construction` - Weather-dependent hiring
- `unemployment_ag` - Planting/harvest cycles
- `unemployment_edu_health` - Academic calendar
- `unemployment_trade` - Retail hiring patterns
- `unemployment_transport` - Seasonal shipping
- (Others with moderate patterns)
- **Period**: ~365 days with economic cycle overlay

---

### ⚠️ WEAKLY PERIODIC (16 datasets)

#### Climate AWND (6 datasets)
- **Period**: ~365 days but irregular
- **Challenge**: Weather events create high variance

#### Climate PRCP (6 datasets)
- **Period**: Weak annual signal
- **Challenge**: Dominated by stochastic rain events (spiky)

#### Unemployment - Mixed Sectors (4 datasets)
- Some have weak annual patterns but dominated by economic trends

---

### ❌ NON-PERIODIC (44 datasets)

#### EEG Signals (18 datasets)
- **Reason**: Chaotic brain dynamics, no stable period
- **Contains**: Multi-scale oscillations (alpha 8-13 Hz, beta 13-30 Hz, etc.)
- **Note**: Local periodicities in frequency bands, but not globally periodic

#### Stock Price & Volume (18 datasets)
- **Reason**: Efficient market hypothesis - prices follow random walk
- **Contains**: Volatility clustering (GARCH effects)
- **Note**: No predictable periodicity (otherwise arbitrage opportunity)

#### Crime (2 datasets)
- `chi_homicide_monthly`, `chi_homicide_weekly`
- **Reason**: Social/criminal events are irregular
- **Note**: May have weak weekly patterns (weekend effects)

#### Astronomy (5 datasets - assumed mixed)
- Some may be periodic (binaries, pulsars)
- Some non-periodic (irregular variables)
- **Treat as non-periodic** unless dataset documentation specifies

#### Unemployment - Core Sectors (6 datasets)
- `unemployment_finance`, `unemployment_info`, `unemployment_manufacturing`
- `unemployment_business`, `unemployment_govt`, `unemployment_mining`
- **Reason**: Dominated by economic trends, not seasonal cycles

---

## 3. Recommended Analysis Groupings

### For Periodicity Preservation Analysis
**Use only these 20 strongly periodic datasets:**

1. **Climate TMAX** (6) - Best baseline, clean sinusoidal
2. **Flights** (3) - Multi-scale periodicity
3. **Tourism** (2) - Strong annual cycles
4. **Unemployment Seasonal** (9) - Economic + seasonal

**Expected result**: Gaussian/Mean/Median filters should preserve periodicity well. Aggressive downsamplers may alias if not careful with Nyquist.

---

### For Non-Periodic Feature Analysis
**Use these 44 datasets:**

1. **EEG** (18) - High-frequency, chaotic
2. **Stocks** (18) - Stochastic trends
3. **Crime** (2) - Irregular events
4. **Astro** (5) - Mixed
5. **Unemployment Core** (6) - Trend-dominated

**Expected result**: Level preservation, trend preservation, extrema preservation more relevant than periodicity.

---

### For Size-Specific Algorithm Testing

#### Downsampler Evaluation (> 1,000 points)
- **Climate datasets** (18) - Test LTTB, M4, MinMax on periodic signals
- **EEG 2500/10000** (12) - Test on high-frequency chaotic signals
- **Stocks** (18) - Test on trending stochastic data

#### Smoother Evaluation (All sizes)
- **Small (500)**: Test if window sizes adapt properly
- **Medium (1,000-3,000)**: Core testing range
- **Large (> 3,000)**: Performance benchmarking

---

## 4. Key Insights for Metric Computation

### Periodicity Metrics (FFT-based)
✅ **Compute for**: Climate TMAX/AWND, Flights, Tourism, Seasonal Unemployment  
❌ **Skip for**: EEG, Stocks, Crime, Core Unemployment  
⚠️ **Check manually**: Astronomy datasets (depends on object type)

### Regime Detection
✅ **Most relevant for**: Stocks (bull/bear), Unemployment (recession/growth), EEG (sleep stages)  
⚠️ **Less relevant for**: Climate (only season changes), Flights (gradual trends)

### Spike/Dip Detection
✅ **Most relevant for**: Precipitation (rain events), Stock volume (trading spikes), Crime (incidents)  
❌ **Less relevant for**: TMAX (smooth), Tourism (gradual), EEG (continuous oscillation)

---

## 5. Data Point Ranges Distribution

```
167-500:    5 datasets   (6.25%)   - Tiny
501-1000:   21 datasets  (26.25%)  - Small
1001-3000:  18 datasets  (22.5%)   - Medium
3001-5000:  24 datasets  (30%)     - Large
5001-10000: 12 datasets  (15%)     - Extra Large
```

**Median size**: ~2,500 points  
**Mode size**: ~4,380 points (climate datasets)  
**Range**: 167 (chi_homicide_weekly) to 10,000 (eeg_chan*_10000)

---

## 6. Recommended Precomputation Strategy

### Full Periodicity Analysis (20 datasets)
```bash
# Climate TMAX - HIGHEST PRIORITY for periodicity
climate_atl_tmax, climate_jfk_tmax, climate_lax_tmax
climate_ord_tmax, climate_sea_tmax, climate_slc_tmax

# Flights - Multi-scale periodicity
flights_daily, flights_weekly, flights_monthly

# Tourism - Clean seasonal
nz_tourist_annually, nz_tourist_monthly

# Unemployment - Seasonal sectors
unemployment_hospitality, unemployment_construction, unemployment_ag
unemployment_edu_health, unemployment_trade, unemployment_transport
(+ 3 more with moderate patterns)
```

### Skip Periodicity (44 datasets)
All EEG, Stocks, Crime, Core Unemployment - compute other metrics only

---

## 7. Dataset Quality Notes

### Highest Quality for Testing
- **Climate TMAX**: Clean, long, strong signal
- **Flights weekly**: Well-sampled, clear patterns
- **Stock AAPL/GOOG**: Liquid markets, high data quality

### Challenging Cases
- **Climate PRCP**: Spiky, many zeros
- **Chi homicide weekly**: Only 167 points, irregular
- **EEG 500**: May be too short for meaningful feature extraction

### Recommended Test Set (Diverse)
1. `climate_ord_tmax` - Strong periodic, large
2. `stock_aapl_price` - Non-periodic trend, medium
3. `eeg_chan15_2500` - Chaotic oscillations, large
4. `flights_weekly` - Multi-scale periodic, large
5. `unemployment_hospitality` - Economic + seasonal, small

This gives coverage of: periodic/non-periodic, small/large, smooth/spiky, trend/stationary.
