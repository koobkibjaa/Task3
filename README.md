# Task 3 – Thai Rainfall Data Pipeline

This project downloads rainfall and weather data from two Thai data sources and saves the data as CSV files:

- **ThaiWater** ([thaiwater.net](https://www.thaiwater.net)) runs about 4,000 rain stations. You get rainfall only.
- **TMD** ([tmd.go.th](https://www.tmd.go.th)) is the Thai Meteorological Department. It runs about 130 weather stations. You get rainfall, temperature and wind.

Apache Airflow runs the downloads automatically every morning. You can also run them by hand from the command line.

---

## 1. Folders and files

```
Task3/
├── dags/                    Airflow DAGs (when to run, and in which order)
│   ├── thaiwater_dag.py       thaiwater_today + thaiwater_daily
│   ├── tmd_dag.py             tmd_today + tmd_daily
│   └── practice_dag.py        practice only, not used
│
├── thaiwater/               Code for ThaiWater
├── tmd/                     Code for TMD (same file names, same jobs)
│
├── thaiwater_station.csv    Station list (ThaiWater)
├── tmd_station.csv          Station list (TMD)
│
├── thaiwater_today/         ★ OUTPUT
├── thaiwater_daily/         ★ OUTPUT
├── tmd_today/               ★ OUTPUT
├── tmd_daily/               ★ OUTPUT
│
├── data/                    Working files, not final results
│   ├── raw/                   API data as it arrives (JSON)
│   └── staging/               CSV files waiting to be checked
│
├── docker-compose.yaml      Runs Airflow in Docker (optional)
├── *.ipynb, *.py (in root)  Old notebooks and scripts (see README_notebooks.md)
└── README.md
```

**Your results are in the 4 folders marked ★.** You can delete the files in `data/`. The pipeline makes new ones on the next run.

### Files inside `thaiwater/` and `tmd/`

Each run has 4 steps. Each step is one file and one Airflow task:

```
fetch  →  transform  →  validate  →  save
```

| File | What it does |
|---|---|
| `fetch_station.py` | Downloads the station list from the API. |
| `fetch_today.py` | Downloads the latest data for all stations. It makes one API call. |
| `fetch_daily.py` | Downloads daily data from earlier days. |
| `transform.py` | Changes the raw JSON data into a CSV file. |
| `validate.py` | Checks the CSV file. If the file has a big problem, the task stops with an error. Big problems are: an empty file, missing columns, duplicate rows or bad dates. If the file only has strange values, the task writes a warning and continues. Strange values are: a station outside Thailand, negative rain, or more than 500 mm of rain. |
| `save.py` | Copies the checked CSV file into an output folder. |
| `pipeline.py` | Runs all 4 steps together. Use it from the command line. |
| `config.py` | Settings: API URLs, folder paths and column names. |
| `api.py` | Sends the HTTP requests. If the server has an error, it tries again up to 3 times. |
| `storage.py` | Reads and writes JSON and CSV files. It writes to a `.tmp` file first, so a crash never leaves a half-written file. |

---

## 2. How to use

### Option A: Airflow on your own machine (WSL)

1. Start Airflow: place this in VS code terminal
    source ~/airflow-env/bin/activate
    airflow standalone

2. Open http://localhost:8080. Find the 4 DAGs and switch them **on**. After that, they run every morning.
3. To run a DAG now, click **Trigger**.



## 3. How the data is collected

Each DAG uses **the date it runs**. If you click Trigger, it uses the time when you click.

| DAG | Runs automatically | Which days it downloads | Output |
|---|---|---|---|
| **thaiwater_today** | Every day at 07:00 | The **latest values** when it runs: rain in the last 24 hours and in the last 1 hour | 1 file per run: `thaiwater_today/rain_24h_<date_time>.csv` (~4,600 stations) |
| **thaiwater_daily** | Every day at 07:30 | **From the 1st of the month to today.** Example: a run on 11 Oct gets 1–11 Oct. | 1 file per day: `thaiwater_daily/<YYYY-MM-DD>.csv` (~4,000 stations) |
| **tmd_today** | Every day at 07:00 | The **latest values** when it runs. The API updates them every 3 hours. It only keeps stations with data from today or yesterday. | 1 file per run: `tmd_today/<date_time>.csv` (~127 stations) |
| **tmd_daily** | Every day at 08:00 | **From the 1st of the month to 2 days ago.** Example: a run on 11 Oct gets 1–9 Oct. | 1 file per day: `tmd_daily/tmd_<YYYY-MM-DD>.csv` (~129 stations) |

**"today" and "daily" are different:**

- A **today** file shows the latest values at the time of the run. The file name has the date and the time, so a new run never replaces an older file.
- A **daily** file holds one full day of data. Every morning the DAG downloads the whole month again and **replaces** the old files. If a value was missing or not complete before, it is fixed on the next run. Running again never adds duplicate rows.



### Columns

| Output | Columns |
|---|---|
| `thaiwater_today` | station_id, station_name, lat, lon, agency_name, province, amphoe, tumbon, datetime, rain_24h(mm), rain_1h(mm) |
| `thaiwater_daily` | station_id, station_name, lat, lon, agency_name, province, amphoe, tumbon, date, rain(mm) |
| `tmd_today` | station_id, station_name_th, station_name_en, province, lat, lon, date, datetime, rain(mm), rain_3hr(mm), temp(c), windDirection, windSpeed(km/h), data_from |
| `tmd_daily` | station_id, station_name_th, station_name_en, province, lat, lon, date, rain(mm), maxTemp(c), minTemp(c), maxWindDirection, maxWindSpeed(km/h) |

---

## 4. Good to know

- **Thai text:** all CSV files use the **TIS-620** encoding. In Python, use `pd.read_csv(path, encoding="tis-620")`. In VS Code, choose *Reopen with Encoding → Thai (TIS-620)*.
- **Empty rain values are normal.** Many ThaiWater stations (about 900 each day) send no data.
- **TMD station names:** `tmd_daily` matches stations by their Thai name. About 8 stations do not match, so their lat/lon is empty. The `transform` log lists these stations.
- **`thaiwater_daily` is slow.** It calls the API once for each station, about 4,000 calls. If one call fails, the whole task fails and starts again.
- **Known issue:** in `thaiwater_daily`, the value for the last day of each month may stay incomplete. On the 1st of the next month, the DAG downloads the new month and not the old one.
- **Do not run `airflow dags test` while `airflow standalone` is running.** They use the same database, so the two processes run the same tasks and the run fails. Use **Trigger** in the web page instead.
