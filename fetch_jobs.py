import requests
import json
import os
import re
from datetime import datetime

headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
all_jobs = []
seen_ids = set()

def add_job(job):
    jid = job.get("id", "")
    if jid and jid not in seen_ids:
        seen_ids.add(jid)
        all_jobs.append(job)

def log(msg):
    print(msg, flush=True)

def fetch_smartrecruiters(slug, company_name, filter_keywords=None):
    try:
        params = {"limit": 100}
        r = requests.get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings", params=params, headers=headers, timeout=15)
        if r.status_code == 200:
            jobs = r.json().get("content", [])
            if filter_keywords:
                jobs = [j for j in jobs if any(k in j.get("name","").lower() for k in filter_keywords)]
            log(f"  {company_name} (SR/{slug}): {len(jobs)} offres")
            for job in jobs:
                loc = f"{job.get('location',{}).get('city','')}, {job.get('location',{}).get('country','')}"
                add_job({"id": f"sr-{job.get('id','')}", "title": job.get("name",""), "company": company_name, "location": loc, "description": "", "salary_min": None, "salary_max": None, "url": f"https://careers.smartrecruiters.com/{slug}/{job.get('id','')}", "created": job.get("releasedDate",""), "category": "Gaming & Entertainment", "source": company_name})
        else:
            log(f"  {company_name} (SR/{slug}): {r.status_code}")
    except Exception as e:
        log(f"  {company_name} SR error: {e}")

def fetch_lever(slug, company_name, filter_keywords=None):
    try:
        r = requests.get(f"https://api.lever.co/v0/postings/{slug}?mode=json", headers=headers, timeout=10)
        if r.status_code == 200:
            jobs = r.json() if isinstance(r.json(), list) else []
            if filter_keywords:
                jobs = [j for j in jobs if any(k in j.get("text","").lower() for k in filter_keywords)]
            log(f"  {company_name} (Lever/{slug}): {len(jobs)} offres")
            for job in jobs:
                cats = job.get("categories", {})
                loc = cats.get("location", "")
                ts = job.get("createdAt", 0)
                created = datetime.utcfromtimestamp(ts/1000).isoformat()+"Z" if ts else ""
                add_job({"id": f"lv-{job.get('id','')}", "title": job.get("text",""), "company": company_name, "location": loc, "description": job.get("descriptionPlain","")[:500], "salary_min": None, "salary_max": None, "url": job.get("hostedUrl",""), "created": created, "category": "Gaming & Entertainment", "source": company_name})
        else:
            log(f"  {company_name} (Lever/{slug}): {r.status_code}")
    except Exception as e:
        log(f"  {company_name} Lever error: {e}")

# ============================================================
# 1. GAMELOFT — SmartRecruiters (fonctionne !)
# ============================================================
log("\n[1] Gameloft...")
fetch_smartrecruiters("Gameloft", "Gameloft Montreal")

# ============================================================
# 2. CIRQUE DU SOLEIL — Lever (fonctionne !)
# ============================================================
log("\n[2] Cirque du Soleil...")
fetch_lever("cirquedusoleil", "Cirque du Soleil")

# ============================================================
# 3. RODEO FX — SmartRecruiters (fonctionne !)
# ============================================================
log("\n[3] Rodeo FX...")
fetch_smartrecruiters("RodeoFX", "Rodeo FX")

# ============================================================
# 4. UBISOFT — SmartRecruiters SANS filtre Montreal
# ============================================================
log("\n[4] Ubisoft (toutes offres)...")
fetch_smartrecruiters("Ubisoft", "Ubisoft")

# ============================================================
# 5. BEHAVIOUR INTERACTIVE — SmartRecruiters SANS filtre
# ============================================================
log("\n[5] Behaviour Interactive (toutes offres)...")
fetch_smartrecruiters("BehaviourInteractive", "Behaviour Interactive")

# ============================================================
# 6. EA — SmartRecruiters SANS filtre
# ============================================================
log("\n[6] EA (toutes offres)...")
fetch_smartrecruiters("ElectronicArts", "EA")

# ============================================================
# 7. WB GAMES — SmartRecruiters SANS filtre
# ============================================================
log("\n[7] WB Games (toutes offres)...")
fetch_smartrecruiters("WarnerMediaGames", "WB Games")
fetch_smartrecruiters("WarnerbrosDiscovery", "WB Games")

# ============================================================
# 8. RADIO-CANADA — essai avec bon slug
# ============================================================
log("\n[8] Radio-Canada...")
for slug in ["RadioCanadaCBC", "CBC-Radio-Canada", "CBCRadioCanada", "cbc-radio-canada"]:
    fetch_smartrecruiters(slug, "Radio-Canada")
fetch_lever("cbc", "Radio-Canada")
fetch_lever("cbcradiocanada", "Radio-Canada")

# ============================================================
# 9. SID LEE — Greenhouse fonctionne !
# ============================================================
log("\n[9] Sid Lee...")
try:
    r = requests.get("https://boards-api.greenhouse.io/v1/boards/sidlee/jobs", headers=headers, timeout=10)
    if r.status_code == 200:
        jobs = r.json().get("jobs", [])
        log(f"  Sid Lee (Greenhouse): {len(jobs)} offres")
        for job in jobs:
            add_job({"id": f"gh-{job.get('id','')}", "title": job.get("title",""), "company": "Sid Lee", "location": job.get("location",{}).get("name","Montreal"), "description": "", "salary_min": None, "salary_max": None, "url": job.get("absolute_url",""), "created": job.get("updated_at",""), "category": "Agence", "source": "Sid Lee"})
    else:
        log(f"  Sid Lee (Greenhouse): {r.status_code}")
except Exception as e:
    log(f"  Sid Lee error: {e}")
fetch_smartrecruiters("SidLee", "Sid Lee")
fetch_lever("sidlee", "Sid Lee")

# ============================================================
# 10. LG2 — essai slugs alternatifs
# ============================================================
log("\n[10] lg2...")
for slug in ["lg2agency", "lg2-agency", "agence-lg2"]:
    fetch_lever(slug, "lg2")
for slug in ["lg2", "lg2Agency", "lg2agence"]:
    fetch_smartrecruiters(slug, "lg2")

# ============================================================
# 11. MOMENT FACTORY
# ============================================================
log("\n[11] Moment Factory...")
fetch_smartrecruiters("MomentFactory", "Moment Factory")
fetch_lever("moment-factory", "Moment Factory")

# ============================================================
# 12. KEYWORDS STUDIOS
# ============================================================
log("\n[12] Keywords Studios...")
fetch_smartrecruiters("KeywordsStudios", "Keywords Studios")
fetch_lever("keywords-studios", "Keywords Studios")

# ============================================================
# 13. BUSINESS FRANCE VIE — essai avec regex corrige
# ============================================================
log("\n[13] Business France VIE...")
for city, pays in [("Montr%C3%A9al", "Canada"), ("New+York", "USA")]:
    try:
        url = f"https://mon-vie-via.businessfrance.fr/offres/recherche?villeDestination={city}"
        r = requests.get(url, headers=headers, timeout=20)
        log(f"  VIE {city}: {r.status_code}, {len(r.text)} chars")
        if r.status_code == 200:
            # Try multiple patterns
            patterns = [
                r'data-intitule="([^"]+)"',
                r'"poste"\s*:\s*"([^"]+)"',
                r'class="job-title[^"]*"[^>]*>\s*([^<]+)',
                r'itemprop="title"[^>]*>([^<]+)',
            ]
            found = []
            for pat in patterns:
                found = re.findall(pat, r.text)
                if found:
                    log(f"  VIE {city}: {len(found)} offres avec pattern {pat[:30]}")
                    break
            if not found:
                # Try to find any JSON in the page
                json_matches = re.findall(r'\{[^{}]*"intitule"[^{}]*\}', r.text)
                log(f"  VIE {city}: {len(json_matches)} JSON blocks found")
                for jm in json_matches[:20]:
                    try:
                        data = json.loads(jm)
                        title = data.get("intitule","")
                        if title:
                            add_job({"id": f"vie-{city}-{title}", "title": title, "company": data.get("entreprise",""), "location": city.replace("%C3%A9", "é").replace("+", " "), "description": "", "salary_min": None, "salary_max": None, "url": "https://mon-vie-via.businessfrance.fr", "created": datetime.utcnow().isoformat()+"Z", "category": "VIE", "source": "Business France VIE"})
                    except: pass
    except Exception as e:
        log(f"  VIE {city} error: {e}")

# ============================================================
# 14. THE MUSE — backup avec filtre strict
# ============================================================
log("\n[14] The Muse (backup)...")
kw = ["marketing","crm","data analyst","market intelligence","brand manager","digital marketing","media planner","communications manager"]
for s in [{"category": "Marketing and PR", "location": "Canada"}, {"category": "Data and Analytics", "location": "Canada"}, {"category": "Marketing and PR", "location": "New York City, NY"}]:
    try:
        r = requests.get("https://www.themuse.com/api/public/jobs", params={"category": s["category"], "location": s["location"], "page": 0}, headers=headers, timeout=15)
        results = r.json().get("results", [])
        relevant = [j for j in results if any(k in j.get("name","").lower() for k in kw)]
        log(f"  The Muse '{s['category']}' {s['location']}: {len(relevant)} relevant")
        for job in relevant:
            loc = ", ".join([l.get("name","") for l in job.get("locations", [])])
            add_job({"id": "muse-"+str(job.get("id","")), "title": job.get("name",""), "company": job.get("company",{}).get("name",""), "location": loc, "description": job.get("contents","")[:500], "salary_min": None, "salary_max": None, "url": job.get("refs",{}).get("landing_page",""), "created": job.get("publication_date",""), "category": s["category"], "source": "The Muse"})
    except Exception as e:
        log(f"  The Muse error: {e}")

# ============================================================
# 15. ADZUNA
# ============================================================
APP_ID = os.environ.get("ADZUNA_APP_ID", "")
APP_KEY = os.environ.get("ADZUNA_APP_KEY", "")
if APP_ID and APP_KEY:
    log("\n[15] Adzuna...")
    for s in [{"what": "marketing analyst", "where": "Montreal"}, {"what": "CRM", "where": "Montreal"}]:
        try:
            r = requests.get("https://api.adzuna.com/v1/api/jobs/ca/search/1", params={"app_id": APP_ID, "app_key": APP_KEY, "results_per_page": 10, "what": s["what"], "where": s["where"]}, headers=headers, timeout=15)
            if r.status_code == 200:
                for job in r.json().get("results",[]):
                    add_job({"id": "az-"+str(job.get("id","")), "title": job.get("title",""), "company": job.get("company",{}).get("display_name",""), "location": job.get("location",{}).get("display_name",""), "description": job.get("description",""), "salary_min": job.get("salary_min"), "salary_max": job.get("salary_max"), "url": job.get("redirect_url",""), "created": job.get("created",""), "category": "Marketing", "source": "Adzuna"})
            else:
                log(f"  Adzuna {r.status_code}")
        except Exception as e:
            log(f"  Adzuna error: {e}")

# ============================================================
# SAVE
# ============================================================
log(f"\n{'='*50}")
log(f"Total: {len(all_jobs)} offres uniques")
all_jobs.sort(key=lambda j: j.get("created","") or "", reverse=True)
os.makedirs("data", exist_ok=True)
with open("data/jobs.json", "w", encoding="utf-8") as f:
    json.dump({"updated": datetime.utcnow().isoformat()+"Z", "count": len(all_jobs), "jobs": all_jobs}, f, ensure_ascii=False, indent=2)
log(f"Saved to data/jobs.json")
