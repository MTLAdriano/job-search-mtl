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
# 1. THE MUSE API
# ============================================================
log("\n[1] The Muse API...")
MUSE_SEARCHES = [
    {"category": "Marketing and PR", "location": "Montreal"},
    {"category": "Data and Analytics", "location": "Montreal"},
    {"category": "Marketing and PR", "location": "Canada"},
    {"category": "Data and Analytics", "location": "Canada"},
    {"category": "Marketing and PR", "location": "New York City, NY"},
    {"category": "Data and Analytics", "location": "New York City, NY"},
]
for s in MUSE_SEARCHES:
    try:
        r = requests.get("https://www.themuse.com/api/public/jobs", params={"category": s["category"], "location": s["location"], "page": 0, "descending": "true"}, headers=headers, timeout=15)
        data = r.json()
        results = data.get("results", [])
        log(f"  The Muse '{s['category']}' in {s['location']}: {len(results)} results")
        for job in results:
            loc = ", ".join([l.get("name","") for l in job.get("locations", [])])
            add_job({"id": "muse-"+str(job.get("id","")), "title": job.get("name",""), "company": job.get("company",{}).get("name",""), "location": loc, "description": job.get("contents",""), "salary_min": None, "salary_max": None, "url": job.get("refs",{}).get("landing_page",""), "created": job.get("publication_date",""), "category": s["category"], "source": "The Muse"})
    except Exception as e:
        log(f"  The Muse error: {e}")

# ============================================================
# 2. BUSINESS FRANCE VIE — scrape HTML public
# ============================================================
log("\n[2] Business France VIE...")
VIE_SEARCHES = [
    "https://mon-vie-via.businessfrance.fr/offres/recherche?continentDestination=Am%C3%A9rique+du+Nord&villeDestination=Montr%C3%A9al",
    "https://mon-vie-via.businessfrance.fr/offres/recherche?continentDestination=Am%C3%A9rique+du+Nord&villeDestination=New+York",
]
for vie_url in VIE_SEARCHES:
    try:
        r = requests.get(vie_url, headers=headers, timeout=15)
        log(f"  VIE page status: {r.status_code}, size: {len(r.text)}")
        # Try to find job data in the page
        import re
        # Look for JSON data embedded in the page
        matches = re.findall(r'"intitule"\s*:\s*"([^"]+)"', r.text)
        refs = re.findall(r'"reference"\s*:\s*"([^"]+)"', r.text)
        companies = re.findall(r'"raisonSociale"\s*:\s*"([^"]+)"', r.text)
        log(f"  Found {len(matches)} job titles")
        city = "Montreal" if "Montreal" in vie_url or "Montr" in vie_url else "New York"
        for i, title in enumerate(matches):
            ref = refs[i] if i < len(refs) else f"vie-{i}"
            co = companies[i] if i < len(companies) else ""
            add_job({"id": f"vie-{ref}", "title": title, "company": co, "location": f"{city}, Canada" if city == "Montreal" else f"{city}, USA", "description": "", "salary_min": None, "salary_max": None, "url": "https://mon-vie-via.businessfrance.fr/offres/recherche", "created": datetime.utcnow().isoformat()+"Z", "category": "VIE", "source": "Business France VIE"})
    except Exception as e:
        log(f"  VIE error: {e}")

# ============================================================
# 3. GREENHOUSE ATS — slugs corriges
# ============================================================
log("\n[3] Greenhouse ATS...")
GREENHOUSE_COMPANIES = [
    ("bhvr", "Behaviour Interactive"),
    ("electronicarts", "EA"),
    ("gameloftmontreal", "Gameloft Montreal"),
    ("warnermediagames", "WB Games"),
    ("cossettecom", "Cossette"),
    ("momentfactory", "Moment Factory"),
    ("ubisoft", "Ubisoft"),
]
keywords = ["marketing","crm","data","analyst","intelligence","coordinator","brand","insight","communication","player","media","content","strategy"]
for slug, name in GREENHOUSE_COMPANIES:
    try:
        r = requests.get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs", headers=headers, timeout=10)
        if r.status_code == 200:
            jobs = r.json().get("jobs", [])
            relevant = [j for j in jobs if any(k in j.get("title","").lower() for k in keywords)]
            log(f"  {name}: {len(jobs)} total, {len(relevant)} relevant")
            for job in relevant:
                add_job({"id": "gh-"+str(job.get("id","")), "title": job.get("title",""), "company": name, "location": job.get("location",{}).get("name",""), "description": job.get("content",""), "salary_min": None, "salary_max": None, "url": job.get("absolute_url",""), "created": job.get("updated_at",""), "category": "Gaming & Entertainment", "source": "Greenhouse"})
        else:
            log(f"  {name}: {r.status_code}")
    except Exception as e:
        log(f"  {name} error: {e}")

# ============================================================
# 4. LEVER ATS — slugs corriges
# ============================================================
log("\n[4] Lever ATS...")
LEVER_COMPANIES = [
    ("ubisoft-montreal", "Ubisoft Montreal"),
    ("moment-factory", "Moment Factory"),
    ("keywordsstudios", "Keywords Studios"),
    ("behaviour", "Behaviour Interactive"),
    ("gameloft", "Gameloft"),
]
for slug, name in LEVER_COMPANIES:
    try:
        r = requests.get(f"https://api.lever.co/v0/postings/{slug}?mode=json", headers=headers, timeout=10)
        if r.status_code == 200:
            jobs = r.json() if isinstance(r.json(), list) else []
            relevant = [j for j in jobs if any(k in j.get("text","").lower() for k in keywords)]
            log(f"  {name}: {len(jobs)} total, {len(relevant)} relevant")
            for job in relevant:
                cats = job.get("categories", {})
                loc = cats.get("location", "")
                ts = job.get("createdAt", 0)
                created = datetime.utcfromtimestamp(ts/1000).isoformat()+"Z" if ts else ""
                add_job({"id": "lv-"+str(job.get("id","")), "title": job.get("text",""), "company": name, "location": loc, "description": job.get("descriptionPlain",""), "salary_min": None, "salary_max": None, "url": job.get("hostedUrl",""), "created": created, "category": "Gaming & Entertainment", "source": "Lever"})
        else:
            log(f"  {name}: {r.status_code}")
    except Exception as e:
        log(f"  {name} error: {e}")

# ============================================================
# 5. WORKDAY — Ubisoft direct
# ============================================================
log("\n[5] Ubisoft careers direct...")
try:
    r = requests.get("https://www.ubisoft.com/api/v1/jobs?locations=Canada&pageSize=50&pageIndex=0", headers=headers, timeout=15)
    if r.status_code == 200:
        data = r.json()
        jobs = data.get("jobs", data.get("items", data.get("results", [])))
        log(f"  Ubisoft direct: {len(jobs)} jobs")
        for job in jobs[:20]:
            title = job.get("title", job.get("name", ""))
            if any(k in title.lower() for k in keywords):
                add_job({"id": "ubi-"+str(job.get("id", title)), "title": title, "company": "Ubisoft Montreal", "location": job.get("location", "Montreal, Canada"), "description": job.get("description", ""), "salary_min": None, "salary_max": None, "url": job.get("url", "https://www.ubisoft.com/en-gb/company/careers"), "created": job.get("postedDate", ""), "category": "Gaming", "source": "Ubisoft"})
    else:
        log(f"  Ubisoft direct: {r.status_code}")
except Exception as e:
    log(f"  Ubisoft error: {e}")

# ============================================================
# 6. ADZUNA (si plan debloque)
# ============================================================
APP_ID = os.environ.get("ADZUNA_APP_ID", "")
APP_KEY = os.environ.get("ADZUNA_APP_KEY", "")
if APP_ID and APP_KEY:
    log("\n[6] Adzuna API...")
    for s in [{"what": "marketing analyst", "where": "Montreal"}, {"what": "CRM marketing", "where": "Montreal"}, {"what": "data analyst", "where": "Montreal"}]:
        try:
            r = requests.get("https://api.adzuna.com/v1/api/jobs/ca/search/1", params={"app_id": APP_ID, "app_key": APP_KEY, "results_per_page": 10, "what": s["what"], "where": s["where"], "sort_by": "date"}, headers=headers, timeout=15)
            if r.status_code == 200:
                results = r.json().get("results", [])
                log(f"  Adzuna '{s['what']}': {len(results)}")
                for job in results:
                    add_job({"id": "az-"+str(job.get("id","")), "title": job.get("title",""), "company": job.get("company",{}).get("display_name",""), "location": job.get("location",{}).get("display_name",""), "description": job.get("description",""), "salary_min": job.get("salary_min"), "salary_max": job.get("salary_max"), "url": job.get("redirect_url",""), "created": job.get("created",""), "category": job.get("category",{}).get("label",""), "source": "Adzuna"})
            else:
                log(f"  Adzuna {r.status_code}: {r.text[:80]}")
        except Exception as e:
            log(f"  Adzuna error: {e}")

# ============================================================
# SAVE
# ============================================================
log(f"\nTotal unique jobs: {len(all_jobs)}")
all_jobs.sort(key=lambda j: j.get("created","") or "", reverse=True)
output = {"updated": datetime.utcnow().isoformat()+"Z", "count": len(all_jobs), "jobs": all_jobs}
os.makedirs("data", exist_ok=True)
with open("data/jobs.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
log(f"Saved {len(all_jobs)} jobs to data/jobs.json")
