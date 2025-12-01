# 03-IITP-DABT-JobMatching

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
* `USER_DATA.csv`: This file contains user information and preference data. Each user is assigned a unique internal UserID during loading.
* `JOB_DATA.csv`: This file contains job postings used for recommendation. Each job is assigned a unique internal JobID.



## Usage

### Basic Command
```bash
python job_recommender.py
```
