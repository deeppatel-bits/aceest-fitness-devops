# ACEest Fitness & Gym — DevOps CI/CD Pipeline

## Assignment 2 | Introduction to DevOps (CSIZG514/SEZG514) | BITS Pilani S1-2025

---

## GitHub Repository
https://github.com/deeppatel-bits/aceest-fitness-devops

## Container Registry (Docker Images)
https://github.com/deeppatel-bits?tab=packages

---

## Jenkins Pipeline
- Tool: Jenkins 2.555.1 (running via Docker)
- Build #7: ✅ SUCCESS
- Tests: 39 passed, 0 failed
- Pipeline stages: Checkout → Install Dependencies → Run Tests → Build Docker Image → Push to Registry → Deploy

---

## Docker Images (GHCR)
- ghcr.io/deeppatel-bits/aceest-fitness:latest
- ghcr.io/deeppatel-bits/aceest-fitness:v3.2.4
- ghcr.io/deeppatel-bits/aceest-fitness:v2.2.4
- ghcr.io/deeppatel-bits/aceest-fitness:v1.1
- ghcr.io/deeppatel-bits/aceest-fitness:v1.0

---

## Kubernetes Deployment Strategies
| Strategy | File |
|---|---|
| Rolling Update | k8s/deployment.yaml |
| Blue-Green | k8s/blue-green.yaml |
| Canary | k8s/canary.yaml |
| Shadow | k8s/shadow.yaml |
| A/B Testing | k8s/ab-testing.yaml |

---

## Code Quality
- Pylint Score: 7.12/10
- Radon Cyclomatic Complexity: Grade A (all 17 functions)
- Full report: sonarqube_report.docx

---

## Project Structure
```
aceest-fitness-devops/
├── app/                  # Flask application + all version files
├── tests/                # 39 Pytest unit tests
├── k8s/                  # Kubernetes deployment manifests
├── Dockerfile            # Multi-stage Docker build
├── Jenkinsfile           # CI/CD pipeline definition
├── requirements.txt      # Python dependencies
├── sonarqube_report.docx # Code quality report
└── README.md             # This file
```