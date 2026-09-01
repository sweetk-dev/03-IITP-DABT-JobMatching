# Job Recommendation

This repository provides a job recommendation script that matches users to job postings using TF-IDF and cosine similarity.  
User preferences (e.g., desired job type) are compared against job descriptions to recommend the most relevant job postings.


## Installation

```bash
pip install python==3.11.14
pip install pandas==2.3.3
pip install numpy==2.3.4
pip install matplotlib==3.10.6
pip install scikit-learn==1.7.2
pip install sentence-transformers==5.1.2
pip install transformers==4.49.0
pip install safetensors==0.5.3
pip install pyarrow==22.0.0
pip install PyQt6==6.9.1
pip install torch==2.9.0+cu128
pip install torchvision==0.24.0+cu128
```

## Data
* `dataset/USER_DATA.csv`: This file contains user information and preference data. Each user is assigned a unique internal UserID during loading.
* `dataset/JOB_DATA.csv`: This file contains job postings used for recommendation. Each job is assigned a unique internal JobID.

Personal data in `JOB_DATA.csv` (contact names, phone numbers, e-mail addresses) is masked.
See `dataset/README.md` for the masking rules and `mask_pii.py` for the implementation.



## Usage

### Basic Command
```bash
python job_recommender.py
```

## 라이선스

이 프로젝트는 MIT 라이선스로 배포됩니다. 전문은 [LICENSE](LICENSE) 파일을 참고하십시오.

본 연구는 정부(과학기술정보통신부)의 재원으로 정보통신기획평가원의 지원을 받아 수행된 연구입니다.
(연구개발과제번호 RS-2024-003976, 데이터 기반 장애인 데이터 탐색·활용 해결기술 개발)
