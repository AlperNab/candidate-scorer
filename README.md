# Candidate Scorer

This folder has been upgraded into a **standalone real GUI project**.

Run the project GUI:

```bash
./run_gui.sh
```

Windows:

```powershell
.\run_gui_windows.ps1
```

Default local URL: `http://127.0.0.1:9104`

This project includes its own FastAPI backend, browser GUI, provider settings, local/cloud LLM routing, encrypted API-key storage, file uploads, job history, exports, and a project-specific plugin configuration.

See `PROJECT_IMPLEMENTATION.md` and `project_config.json` for the applied project-specific features and customization controls.

---

## Original README

# candidate-scorer

> **CV + job description → match score with full explainability.** Skills match, experience fit, seniority alignment, growth trajectory, interview questions, bias-aware scoring.

[![PyPI](https://img.shields.io/pypi/v/candidate-scorer?style=flat)](https://pypi.org/project/candidate-scorer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Quickstart

```bash
pip install candidate-scorer
python -m candidate_scorer resume.pdf job_description.txt
python -m candidate_scorer cv.pdf jd.txt --json
```

## Scoring dimensions

| Dimension | What it measures |
|-----------|-----------------|
| Technical skills | Skills matched, missing, bonus |
| Experience fit | Years, domain overlap |
| Seniority alignment | Over/under/good fit |
| Growth trajectory | Accelerating, steady, flat, declining |

## Bias-aware design

Scores based on skills and demonstrated outcomes only. Never factors in age,
gender, ethnicity, nationality, or family status. Includes explicit bias check
in every output.

## License
MIT © [Alper Nabil Gabra Zakher](https://github.com/AlperNab)
