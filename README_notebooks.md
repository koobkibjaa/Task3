# Task 3 – Thai Rainfall Station Data Downloader

Jupyter notebooks that download daily rainfall and weather observations from two Thai sources and save them as one CSV per day:

| Notebook | Source | Output |
|---|---|---|
| [02_Station_Thaiwater.ipynb](02_Station_Thaiwater.ipynb) | [ThaiWater](https://www.thaiwater.net) (National Hydroinformatics Data Center) | Daily rainfall for every ThaiWater telemetry station |
| [02_Station_TMD.ipynb](02_Station_TMD.ipynb) | [TMD](https://www.tmd.go.th) (Thai Meteorological Department) | Daily rainfall, max/min temperature and max wind for TMD stations |

## Requirements

- Python 3 with Jupyter
- `pandas`, `requests` (the first cell of each notebook runs `pip install`)
- `psycopg2` is imported but not used yet. It is there for loading the data into PostgreSQL later.

```bash
pip install pandas requests psycopg2
```

## 02_Station_Thaiwater.ipynb

### 1. Build the station list (cell 3)

This cell reads `api_url` (`https://api-v3.thaiwater.net/api/v1/thaiwater30/public/rain_yearly`, about 4,000 stations) and writes `thaiwater_station.csv`:

```
station_id, station_name, lat, lon, agency_name, province, amphoe, tumbon
```

A few station names contain characters that TIS-620 can't store (Lao script, non-breaking spaces). Those characters are written as `?`.

### 2. Download daily rainfall (cell 4)

For every station in `thaiwater_station.csv` and each month of `year`, this cell calls:

```
https://api-v3.thaiwater.net/api/v1/thaiwater30/public/rain_monthly_graph?station_id=<id>&month=<m>&year=<yyyy>
```

It appends each daily value to `thaiwater_daily/<YYYY-MM-DD>.csv`:

```
station_id, station_name, lat, lon, agency_name, province, amphoe, tumbon, date, rain(mm)
```

**Before running:**
- Set `year` (currently `2026`). The cell loops over all 12 months, so it also writes files for future dates, which are left empty. It creates the `thaiwater_daily/` folder itself.
- Re-running is safe. For each date file, the cell overwrites the row of every station it fetched, adds stations that are missing, and keeps the other rows. Months are the outer loop, so each daily file is written once per month.
- Only about 1/3 of the listed stations still report data, so most rows have an empty `rain(mm)`.

### 3. Today's daily rainfall, with yesterday as fallback (cell 5)

Run cell 1, then cell 5. You can skip cells 3 and 4. Cell 5 makes one call to:

```
https://api-v3.thaiwater.net/api/v1/thaiwater30/public/rain_today
```

That call returns each station's latest daily rainfall value. For each station, cell 5 uses the value dated today if there is one, or the value dated yesterday if not. Stations whose data is older than yesterday are skipped. The result is saved to `thaiwater_today/<YYYY-MM-DD>.csv`, and running the cell again on the same day overwrites that file with fresh data:

```
station_id, station_name, lat, lon, agency_name, province, amphoe, tumbon, date, datetime, rain(mm), data_from
```

- `data_from` is `today` or `yesterday`.
- `datetime` is the time of the station's last reading. A "today" value taken before the day's cut-off time may still be growing, so run the cell later in the morning for complete values.

## 02_Station_TMD.ipynb

This notebook needs an existing station lookup file, `tmd_station.csv` (TIS-620 encoded, with the columns `station_id, station_name_th, station_name_en, province, lat, lon`). For each day from `start_date` to `end_date`, cell 4 calls:

```
https://www.tmd.go.th/api/WeatherObservationDailyStation/weather-station-daily?DateTime=<YYYY-MM-DD>%2017:00&Culture=th-TH
```

It joins each record to the station file by Thai station name and writes `tmd_daily_all_2024/tmd_<YYYY-MM-DD>.csv`:

```
station_id, station_name_th, station_name_en, province, lat, lon, date,
rain(mm), maxTemp(c), minTemp(c), maxWindDirection, maxWindSpeed(km/h)
```

**Before running:**
- The paths are hard-coded to `D:/PhD-Semester-2/Code-Download/loadTMDStation_clean/`. Change `station_file` (cell 2) and `data_file` (cell 4) to match your machine.
- Create the output folder (`tmd_daily_all_2024/`).
- Set `start_date` / `end_date`. `daterange()` **does not include** `end_date`, so `date(2024, 12, 31)` stops at Dec 30. Use `date(2025, 1, 1)` to get the whole year.

## Notes and gotchas

- **Encoding:** all CSVs are written in `tis-620` (Thai). Open them with `pd.read_csv(path, encoding="tis-620")`. If you open them as UTF-8, the Thai text shows up garbled.
- **Re-running:** the ThaiWater daily cell updates rows by station and date, so running it twice does not duplicate rows. The TMD daily cell overwrites each date file.
- **TMD station matching:** `df.loc[...].iloc[0]` raises an `IndexError` if the API returns a station name that is not in `tmd_station.csv`.
- **Rate/length:** the ThaiWater loop makes 12 requests per station (hundreds of stations in total), so it takes a long time. It has no retry or delay. Requests that fail (non-200) are skipped without a message.
- `my test thaiwater.py` is an empty scratch file.

## Project layout

```
Task3/
├── 02_Station_Thaiwater.ipynb   # ThaiWater station list + daily rainfall
├── 02_Station_TMD.ipynb         # TMD daily weather observations
├── my test thaiwater.py         # scratch (empty)
├── thaiwater_station.csv        # generated by the ThaiWater notebook
└── thaiwater_daily/             # generated: one CSV per day
```
