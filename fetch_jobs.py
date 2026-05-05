import requests
import json
import os
from datetime import datetime

APP_ID = os.environ.get("ADZUNA_APP_ID", "")
APP_KEY = os.environ.get("ADZUNA_APP_KEY", "")

if not APP_ID or not APP_KEY:
    print("Error: ADZUNA_APP_ID and ADZUNA_APP_KEY must be set as GitHub Secrets")
    exit(1)

SEARCHES = [
    {"what": "CRM analyst marketing", "where": "Montreal"},
    {"what": "market intelligence data analyst", "where": "Montreal"},
    {"what": "player engagement gaming marketing", "where": "Montreal"},
    {"what": "marketing analyst entertainment gaming", "where": "Montreal"},
    {"what": "data analyst entertainment media", "where": "Montreal"},
]

def fetch_jobs(what, where):
    url = "https://api.adzuna.com/v1/api/jobs/ca/search/1"
    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "results_per_page": 10,
        "what": what,
        "where": where,
        "sort_by": "date",
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json().get("results", [])
    except Exception as e:
        print(f"Error fetching '{what}': {e}")
        return []

all_jobs = []
seen_ids = set()

for search in SEARCHES:
    jobs = fetch_jobs(search["what"], search["where"])
    for job in jobs:
        job_id = job.get("id", "")
        if job_id and job_id not in seen_ids:
            seen_ids.add(job_id)
            all_jobs.append({
                "id": job_id,
                "title": job.get("title", ""),
                "company": job.get("company", {}).get("display_name", ""),
                "location": job.get("location", {}).get("display_name", ""),
                "description": job.get("description", ""),
                "salary_min": job.get("salary_min"),
                "salary_max": job.get("salary_max"),
                "url": job.get("redirect_url", ""),
                "created": job.get("created", ""),
                "category": job.get("category", {}).get("label", ""),
            })

output = {
    "updated": datetime.utcnow().isoformat() + "Z",
    "count": len(all_jobs),
    "jobs": all_jobs
}

os.makedirs("data", exist_ok=True)
with open("data/jobs.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"✅ Saved {len(all_jobs)} jobs to data/jobs.json")
