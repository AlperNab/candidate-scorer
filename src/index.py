#!/usr/bin/env python3
"""
candidate-scorer — CV + job description → match score with explainability
Scores: skills match, experience fit, seniority alignment, culture signals,
growth trajectory, red flags — bias-aware, GDPR-conscious
"""
import anthropic, base64, json, re, sys
from pathlib import Path

SYSTEM = """You are a fair, evidence-based talent assessment specialist.
Score this candidate against the job requirements with full explainability.

IMPORTANT — bias awareness:
- Never factor in age, gender, ethnicity, nationality, or family status
- Focus only on skills, experience, and demonstrated outcomes
- Note when you cannot assess something without more information
- Distinguish between "can definitely do this" vs "probably can learn this"

Return ONLY valid JSON — no markdown, no explanation.

{
  "candidate_name": "string or 'Candidate'",
  "job_title": "string",
  "overall_match_score": number_0_to_100,
  "recommendation": "strong_yes|yes|maybe|no|strong_no",
  "recommendation_reason": "one sentence",
  "scores": {
    "technical_skills": {
      "score": number_0_to_100,
      "matched": ["skills they have that are required"],
      "missing": ["required skills not in CV"],
      "bonus": ["extra skills not required but valuable"]
    },
    "experience_fit": {
      "score": number_0_to_100,
      "years_required": number_or_null,
      "years_candidate": number_or_null,
      "domain_overlap": "high|medium|low|none",
      "notes": "string"
    },
    "seniority_alignment": {
      "score": number_0_to_100,
      "required_level": "junior|mid|senior|lead|principal|executive",
      "candidate_level": "junior|mid|senior|lead|principal|executive",
      "verdict": "overqualified|good_fit|underqualified"
    },
    "growth_trajectory": {
      "score": number_0_to_100,
      "trend": "accelerating|steady|flat|declining",
      "evidence": ["specific career moves that indicate trajectory"]
    }
  },
  "strengths": [
    {"strength":"string","evidence":"specific CV evidence for this"}
  ],
  "concerns": [
    {
      "concern": "string",
      "severity": "dealbreaker|significant|minor",
      "evidence": "what in the CV raised this",
      "question_to_ask": "interview question to probe this"
    }
  ],
  "interview_questions": [
    {
      "question": "behavioral or technical question",
      "type": "behavioral|technical|situational|culture",
      "what_to_probe": "what you're assessing with this question",
      "good_answer_signals": ["what a strong answer would include"]
    }
  ],
  "skills_gap_assessment": {
    "critical_gaps": ["skills they must have — dealbreakers"],
    "trainable_gaps": ["gaps that can be bridged with ramp-up time"],
    "estimated_ramp_weeks": number
  },
  "red_flags": [
    {"flag":"string","severity":"high|medium|low","context":"why this is a flag"}
  ],
  "positive_signals": ["things the CV does well beyond the requirements"],
  "data_limitations": ["things you couldn't assess from the CV alone"],
  "bias_check": "confirmation that scoring was based on skills/experience only",
  "confidence": 0.0
}"""

def read_doc(path: Path):
    if str(path).endswith(".pdf"):
        data = base64.standard_b64encode(path.read_bytes()).decode("ascii")
        return [{"type":"document","source":{"type":"base64","media_type":"application/pdf","data":data}}]
    return [{"type":"text","text":path.read_text(encoding="utf-8",errors="replace")[:20000]}]

def score(cv_source: str, jd_source: str) -> dict:
    client = anthropic.Anthropic()
    cv_path, jd_path = Path(cv_source), Path(jd_source)

    content = []
    if cv_path.exists():
        content.extend(read_doc(cv_path))
        content.append({"type":"text","text":"\n[This is the candidate's CV above]\n\nJob description:\n"})
    else:
        content.append({"type":"text","text":f"Candidate CV:\n{cv_source[:15000]}\n\nJob description:\n"})

    if jd_path.exists():
        content.append({"type":"text","text":jd_path.read_text(encoding="utf-8",errors="replace")[:10000]})
    else:
        content.append({"type":"text","text":jd_source[:10000]})

    content.append({"type":"text","text":"\n\nScore this candidate against the job description."})

    resp = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=4096, system=SYSTEM,
        messages=[{"role":"user","content":content}]
    )
    raw = re.sub(r'^```(?:json)?\s*','',resp.content[0].text.strip(),flags=re.MULTILINE)
    raw = re.sub(r'\s*```$','',raw,flags=re.MULTILINE)
    return json.loads(raw)

REC_ICON = {"strong_yes":"🟢🟢","yes":"🟢","maybe":"🟡","no":"🔴","strong_no":"🔴🔴"}
SEV_ICON = {"dealbreaker":"🚫","significant":"🔴","minor":"🟡"}

def print_report(r: dict):
    scores = r.get("scores",{})
    overall = r.get("overall_match_score",0)
    rec = r.get("recommendation","maybe")

    print(f"\n{'═'*60}")
    print(f"  CANDIDATE SCORE — {r.get('candidate_name','?')}")
    print(f"  Role: {r.get('job_title','?')}")
    print(f"  Score: {overall}/100 | {REC_ICON.get(rec,'')} {rec.upper().replace('_',' ')}")
    print(f"{'═'*60}")
    print(f"\n  {r.get('recommendation_reason','')}")

    print(f"\n  DIMENSION SCORES")
    dim_map = [("technical_skills","Technical skills"),("experience_fit","Experience"),
               ("seniority_alignment","Seniority"),("growth_trajectory","Growth trajectory")]
    for key, label in dim_map:
        s = scores.get(key,{}).get("score",0)
        bar = "█"*(s//10) + "░"*(10-s//10)
        print(f"  {label:<22} {bar} {s}/100")

    tech = scores.get("technical_skills",{})
    if tech.get("matched"):
        print(f"\n  ✓ Has: {', '.join(tech['matched'][:6])}")
    if tech.get("missing"):
        print(f"  ✗ Missing: {', '.join(tech['missing'][:4])}")
    if tech.get("bonus"):
        print(f"  + Bonus: {', '.join(tech['bonus'][:3])}")

    exp = scores.get("experience_fit",{})
    sen = scores.get("seniority_alignment",{})
    print(f"\n  Experience: {exp.get('years_candidate','?')}y (need {exp.get('years_required','?')}y) | Domain: {exp.get('domain_overlap','?')}")
    print(f"  Seniority: {sen.get('candidate_level','?')} vs {sen.get('required_level','?')} → {sen.get('verdict','?')}")

    concerns = r.get("concerns",[])
    if concerns:
        print(f"\n{'─'*60}\n  CONCERNS")
        for c in sorted(concerns, key=lambda x: ["dealbreaker","significant","minor"].index(x.get("severity","minor"))):
            print(f"\n  {SEV_ICON.get(c.get('severity','minor'),'')} {c.get('concern','')}")
            if c.get("question_to_ask"): print(f"     Ask: \"{c['question_to_ask']}\"")

    iq = r.get("interview_questions",[])
    if iq:
        print(f"\n{'─'*60}\n  INTERVIEW QUESTIONS")
        for q in iq[:4]:
            print(f"\n  [{q.get('type','?').upper()}] {q.get('question','')}")
            signals = q.get("good_answer_signals",[])
            if signals: print(f"  Look for: {signals[0]}")

    gaps = r.get("skills_gap_assessment",{})
    if gaps.get("trainable_gaps"):
        print(f"\n  Trainable gaps (~{gaps.get('estimated_ramp_weeks','?')}w ramp): {', '.join(gaps['trainable_gaps'][:3])}")

    print(f"\n  {r.get('bias_check','')}")
    print(f"  Confidence: {int(r.get('confidence',0)*100)}%")
    print(f"{'═'*60}\n")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Score a candidate CV against a job description")
    p.add_argument("cv", help="CV file (.pdf, .txt) or raw text")
    p.add_argument("jd", help="Job description file or raw text")
    p.add_argument("--json",action="store_true")
    a = p.parse_args()
    r = score(a.cv, a.jd)
    if a.json: print(json.dumps(r,indent=2,ensure_ascii=False))
    else: print_report(r)
