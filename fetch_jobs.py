import requests
import json
import os
from datetime import datetime

headers = {"User-Agent": "Mozilla/5.0 (compatible; JobSearchBot/1.0)"}

all_jobs = []
seen_ids = set()

def add_job(job):
    jid = job.get("id", "")
    if jid and jid not in seen_ids:
        seen_ids.add(jid)
        all_jobs.append(job)

def log(msg):
    print(msg, flush=True)

# ============================================================
# 1. THE MUSE API — gratuit, sans cle
# ============================================================
log("\n[1] The Muse API...")
MUSE_SEARCHES = [
    {"category": "Marketing and PR", "location": "Montreal"},
    {"category": "Data and Analytics", "location": "Montreal"},
    {"category": "Marketing and PR", "location": "Canada"},
    {"category": "Data and Analytics", "location": "Canada"},
]
for s in MUSE_SEARCHES:
    try:
        url = "https://www.themuse.com/api/public/jobs"
        params = {"category": s["category"], "location": s["location"], "page": 0, "descending": "true"}
        r = requests.get(url, params=params, headers=headers, timeout=15)
        data = r.json()
        results = data.get("results", [])
        log(f"  The Muse '{s['category']}' in {s['location']}: {len(results)} results")
        for job in results:
            co = job.get("company", {}).get("name", "")
            loc = ", ".join([l.get("name","") for l in job.get("locations", [])])
            add_job({
                "id": "muse-" + str(job.get("id","")),
                "title": job.get("name", ""),
                "company": co,
                "location": loc,
                "description": job.get("contents", ""),
                "salary_min": None,
                "salary_max": None,
                "url": job.get("refs", {}).get("landing_page", ""),
                "created": job.get("publication_date", ""),
                "category": s["category"],
                "source": "The Muse"
            })
    except Exception as e:
        log(f"  The Muse error: {e}")

# ============================================================
# 2. BUSINESS FRANCE — VIE
# ============================================================
log("\n[2] Business France VIE...")

VIE_CITIES = [
    {"ville": "Montreal", "pays": "Canada"},
    {"ville": "New York", "pays": "Etats-Unis"},
]

def fetch_vie(ville):
    try:
        url = "https://mon-vie-via.businessfrance.fr/api/v1/offres"
        params = {
            "limit": 100,
            "offset": 0,
            "villeDestination": ville,
            "famille": "Commerce - Vente - Distribution,Marketing - Communication,Etudes - Conseil - Audit,Digital - Internet - E-commerce"
        }
        r = requests.get(url, params=params, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            results = data.get("content", data.get("offres", data.get("items", [])))
            if isinstance(results, dict):
                results = results.get("content", results.get("items", []))
            if not isinstance(results, list):
                results = []
            log(f"  VIE {ville}: {len(results)} offres")
            return results
        else:
            log(f"  VIE {ville}: status {r.status_code}")
            return []
    except Exception as e:
        log(f"  VIE {ville} error: {e}")
        return []

for city in VIE_CITIES:
    results = fetch_vie(city["ville"])
    for job in results:
        title = job.get("intitule", job.get("titre", job.get("poste", "")))
        co = job.get("entreprise", {})
        if isinstance(co, dict):
            co = co.get("nom", co.get("name", ""))
        loc = city["ville"] + ", " + city["pays"]
        url_job = job.get("url", job.get("lien", "https://mon-vie-via.businessfrance.fr"))
        jid = str(job.get("id", job.get("reference", title + city["ville"])))
        add_job({
            "id": "vie-" + jid,
            "title": title,
            "company": co if isinstance(co, str) else "",
            "location": loc,
            "description": job.get("description", job.get("mission", job.get("descriptifMission", ""))),
            "salary_min": None,
            "salary_max": None,
            "url": url_job,
            "created": job.get("datePublication", job.get("date", "")),
            "category": "VIE",
            "source": "Business France VIE"
        })

log("\n[3] Greenhouse ATS (sites carrieres directs)...")
GREENHOUSE_COMPANIES = [
    ("behaviour-interactive", "Behaviour Interactive"),
    ("eacanada", "EA Canada"),
    ("gameloft", "Gameloft"),
    ("warnermediagames", "Warner Media Games"),
    ("cossette", "Cossette"),
]
for slug, company_name in GREENHOUSE_COMPANIES:
    try:
        url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            jobs = data.get("jobs", [])
            # Filter relevant jobs
            keywords = ["marketing","crm","data","analyst","intelligence","coordinator","brand","insight","communication"]
            relevant = [j for j in jobs if any(k in j.get("title","").lower() for k in keywords)]
            log(f"  {company_name}: {len(jobs)} total, {len(relevant)} relevant")
            for job in relevant:
                loc = job.get("location", {}).get("name", "")
                add_job({
                    "id": "gh-" + str(job.get("id","")),
                    "title": job.get("title", ""),
                    "company": company_name,
                    "location": loc,
                    "description": job.get("content", ""),
                    "salary_min": None,
                    "salary_max": None,
                    "url": job.get("absolute_url", ""),
                    "created": job.get("updated_at", ""),
                    "category": "Gaming & Entertainment",
                    "source": "Greenhouse"
                })
        else:
            log(f"  {company_name}: status {r.status_code}")
    except Exception as e:
        log(f"  {company_name} error: {e}")

# ============================================================
# 4. LEVER API — autres entreprises gaming/media
# ============================================================
log("\n[4] Lever ATS...")
LEVER_COMPANIES = [
    ("ubisoft", "Ubisoft"),
    ("momentfactory", "Moment Factory"),
    ("keywords-studios", "Keywords Studios"),
]
for slug, company_name in LEVER_COMPANIES:
    try:
        url = f"https://api.lever.co/v0/postings/{slug}"
        params = {"mode": "json", "commitment": "Full-time"}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            jobs = r.json()
            if isinstance(jobs, list):
                keywords = ["marketing","crm","data","analyst","intelligence","coordinator","brand","insight","communication","player"]
                relevant = [j for j in jobs if any(k in j.get("text","").lower() for k in keywords)]
                log(f"  {company_name}: {len(jobs)} total, {len(relevant)} relevant")
                for job in relevant:
                    cats = job.get("categories", {})
                    loc = cats.get("location", cats.get("allLocations", [""])[0] if cats.get("allLocations") else "")
                    add_job({
                        "id": "lv-" + str(job.get("id","")),
                        "title": job.get("text", ""),
                        "company": company_name,
                        "location": loc,
                        "description": job.get("descriptionPlain", job.get("description", "")),
                        "salary_min": None,
                        "salary_max": None,
                        "url": job.get("hostedUrl", job.get("applyUrl", "")),
                        "created": datetime.utcfromtimestamp(job.get("createdAt",0)/1000).isoformat()+"Z" if job.get("createdAt") else "",
                        "category": "Gaming & Entertainment",
                        "source": "Lever"
                    })
            else:
                log(f"  {company_name}: unexpected response")
        else:
            log(f"  {company_name}: status {r.status_code}")
    except Exception as e:
        log(f"  {company_name} error: {e}")

# ============================================================
# 5. ADZUNA (si cles disponibles)
# ============================================================
APP_ID = os.environ.get("ADZUNA_APP_ID", "")
APP_KEY = os.environ.get("ADZUNA_APP_KEY", "")
if APP_ID and APP_KEY:
    log("\n[5] Adzuna API...")
    ADZUNA_SEARCHES = [
        {"what": "marketing analyst", "where": "Montreal"},
        {"what": "CRM marketing", "where": "Montreal"},
        {"what": "data analyst marketing", "where": "Montreal"},
    ]
    for s in ADZUNA_SEARCHES:
        try:
            url = "https://api.adzuna.com/v1/api/jobs/ca/search/1"
            params = {"app_id": APP_ID, "app_key": APP_KEY, "results_per_page": 10, "what": s["what"], "where": s["where"], "sort_by": "date"}
            r = requests.get(url, params=params, headers=headers, timeout=15)
            if r.status_code == 200:
                data = r.json()
                results = data.get("results", [])
                log(f"  Adzuna '{s['what']}': {len(results)} results")
                for job in results:
                    add_job({
                        "id": "az-" + str(job.get("id","")),
                        "title": job.get("title",""),
                        "company": job.get("company",{}).get("display_name",""),
                        "location": job.get("location",{}).get("display_name",""),
                        "description": job.get("description",""),
                        "salary_min": job.get("salary_min"),
                        "salary_max": job.get("salary_max"),
                        "url": job.get("redirect_url",""),
                        "created": job.get("created",""),
                        "category": job.get("category",{}).get("label",""),
                        "source": "Adzuna"
                    })
            else:
                log(f"  Adzuna status {r.status_code}: {r.text[:100]}")
        except Exception as e:
            log(f"  Adzuna error: {e}")

# ============================================================
# SAVE
# ============================================================
log(f"\nTotal unique jobs: {len(all_jobs)}")

# Sort by date
def get_date(j):
    try: return j.get("created","") or ""
    except: return ""
all_jobs.sort(key=get_date, reverse=True)

output = {
    "updated": datetime.utcnow().isoformat() + "Z",
    "count": len(all_jobs),
    "sources": ["The Muse", "Business France VIE", "Greenhouse", "Lever", "Adzuna"],
    "jobs": all_jobs
}

os.makedirs("data", exist_ok=True)
with open("data/jobs.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

log(f"Saved {len(all_jobs)} jobs to data/jobs.json")
