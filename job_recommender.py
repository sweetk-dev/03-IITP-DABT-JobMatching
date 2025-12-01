import os
import time
import pandas as pd
import numpy as np
import warnings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

## 환경 설정 
pd.set_option('display.max_rows', None)  # 모든 행을 출력
pd.set_option('display.max_columns', None)  # 모든 열을 출력
pd.set_option('display.max_colwidth', None)  # 열의 너비 제한 없애기

warnings.filterwarnings("ignore", category=FutureWarning)

USER_DATA_PATH = "./USER_DATA.csv"
JOB_DATA_PATH = "./JOB_DATA.csv"

JOB_FEATURES = ["직무", "담당업무"]
USER_FEATURES = ["희망직종"]

## 결과 저장
BASE_DIR = "."
RESULTS_DIR = os.path.join(BASE_DIR, "results")
RUN_DIR = os.path.join(BASE_DIR, "run")

os.makedirs(RESULTS_DIR, exist_ok=True)

## 데이터 로드 및 전처리
def load_data(user_path: str, job_path: str):
    # csv에서 user, job 데이터 로드 
    user_df = pd.read_csv(user_path)
    job_df = pd.read_csv(job_path)

    # ID 부여
    user_df['UserID'] = range(len(user_df))
    job_df['JobID'] = range(len(job_df))

    # 전체가 NaN인 행 제거
    user_df.dropna(how='all', inplace=True)
    job_df.dropna(how='all', inplace=True)

    # NaN -> 'N/A'로 채우기
    user_df.fillna('N/A', inplace=True)
    job_df.fillna('N/A', inplace=True)

    return user_df, job_df

def build_merged_text(user_df: pd.DataFrame, job_df: pd.DataFrame):
    # 추천에 사용할 텍스트 컬럼(Job_Merge) 생성
    user_features_concat = user_df[USER_FEATURES].apply(
        lambda x: ' '.join(x.astype(str)), axis=1
    )
    job_features_concat = job_df[JOB_FEATURES].apply(
        lambda x: ' '.join(x.astype(str)), axis=1
    )

    user_df['Job_Merge'] = user_features_concat
    job_df['Job_Merge'] = job_features_concat
    
    # print(f"jobs: {job_df.shape}", f"user_df: {user_df.shape}")

    corpus_merge  = job_df['Job_Merge'].tolist() + user_df['Job_Merge'].tolist()
    return user_df, job_df, corpus_merge

def build_vectorizer(corpus: list[str]) -> TfidfVectorizer:
    # TF-IDF 벡터라이저 학습
    vectorizer = TfidfVectorizer()
    corpus_matrix = vectorizer.fit_transform(corpus)
    # print(f"corpus_matrix: {corpus_matrix.shape}")
    return vectorizer

## 추천 함수
def get_recommend(
        userid: int,
        num_jobs: int,
        user_df: pd.DataFrame,
        job_df: pd.DataFrame,
        vectorizer: TfidfVectorizer,
) -> pd.DataFrame | None:
    # 특정 사용자(userid)에 대해 상위 num_jobs개의 채용공고를 추천

    # 해당 유저 인덱스 탐색
    user_index_list = user_df.index[user_df['UserID'] == userid].tolist()
    if not user_index_list:
        print(f"[WARN] UserID {userid}를 찾을 수 없습니다.")
        return None
    
    user_index = user_index_list[0]
    user_text = user_df.loc[user_index, 'Job_Merge']

    # TF-IDF 벡터 변환
    user_vector = vectorizer.transform([user_text])
    job_matrix = vectorizer.transform(job_df['Job_Merge'])

    # 코사인 유사도 계산 
    cosine_sim = cosine_similarity(user_vector, job_matrix)
    # print(f"cosine_sim: {cosine_sim.shape}")

    # 상위 num_jobs개 인덱스 추출
    top_indices = np.argsort(cosine_sim[0])[::-1][:num_jobs]

    if top_indices.size == 0:
        print("No recommendations found based on similarity score.")
        return None
    
    # 디버깅용 유사도 출력s
    index_similarity_pairs = [(i, cosine_sim[0][i]) for i in range(len(cosine_sim[0]))]
    sorted_index_similarity_pairs = sorted(
        index_similarity_pairs, key=lambda x: x[1], reverse=True
    )
    # for index, similarity in sorted_index_similarity_pairs[:num_jobs]:
    #     print(f"직무 인덱스: {index}, 유사도: {similarity}")

    recommended_jobs = job_df.iloc[top_indices]
    return recommended_jobs

## 결과 출력 및 저장 
def show_results(userid: int, user_df: pd.DataFrame, recommended_jobs: pd.DataFrame):
    # 사용자 정보와 추천 결과 출력
    user_view = user_df.loc[user_df['UserID'] == userid,
            ['No', '희망직종', '희망직종분류', '경력', '경력사항', '최종학력', '전공', '성별', '나이', '주소지', '자격증/어학', '장애유형', '장애등급', '특기사항', '비고']
        ].set_index('No')
    
    print("\n[사용자 정보]")
    display(user_view)

    user_info_path = os.path.join(RESULTS_DIR, f"user_{userid}_info.csv")
    user_view.to_csv(user_info_path, index=True, encoding='utf-8-sig')
    print(f"[저장 완료] 사용자 정보 csv: {user_info_path}")

    if recommended_jobs is None or recommended_jobs.empty:
        print("\n[추천 결과 없음]")
        return
    
    recommended_jobs = recommended_jobs.copy()
    recommended_jobs['No'] = recommended_jobs.index + 2
    
    recommend_view = recommended_jobs[
            ['No', '제목', '직무', '담당업무', '분류', '직급', '직책', '경력유무', '학력', '전공', '성별', '연령', '근무지역', '우대조건', '작업환경', '장애인채용구분', '장애인편의시설', '적합장애유형', '부적합장애유형', '고용형태', '근무형태', '근무기간', '근무시간/요일', '급여조건', '복리후생', '기업정보.업종', '기업정보.기업형태']
        ].set_index('No')
    print("\n[추천 채용공고]")
    display(recommend_view)

    recommend_path = os.path.join(RESULTS_DIR, f"user{userid}_recommendations.csv")
    recommend_view.to_csv(recommend_path, index=True, encoding='utf-8-sig')
    print(f"[저장 완료] 추천 결과 csv: {recommend_path}")

    # Precision 계산
    user_category = user_df.loc[user_df['UserID'] == userid, '희망직종분류'].iloc[0]
    user_category_str = str(user_category)
    
    mask_contains = recommended_jobs['분류'].astype(str).str.contains(user_category_str, na=False)
    
    matched_count = mask_contains.sum()
    total_count = len(recommended_jobs)
    precision = matched_count / total_count * 100

    print("\n[매칭 통계]")
    print(f"- 사용자 희망직종분류: {user_category_str}")
    print(f"- 매칭 결과: {matched_count} / {total_count}")
    print(f"- Precision: {precision}%")

    precision_path = os.path.join(RESULTS_DIR, f"precision_results.csv")

    precision_row = pd.DataFrame([{
        "UserID": userid,
        "user_category": user_category_str,
        "matched_count": matched_count,
        "total_count": total_count,
        "precision": precision,
    }])

    # 파일이 이미 있으면 append, 없으면 새로 생성 + 헤더 포함
    if os.path.exists(precision_path):
        precision_row.to_csv(
            precision_path,
            mode="a",
            header=False,
            index=False,
            encoding="utf-8-sig",
        )
    else:
        precision_row.to_csv(
            precision_path,
            mode="w",
            header=True,
            index=False,
            encoding="utf-8-sig",
        )

    print(f"[저장 완료] 매칭 통계 csv: {precision_path}")

## 실행
if __name__ == "__main__":
    num_jobs = 5
    
    for userid in range(0, 6):
        # 1) 데이터 로드
        user_df, job_df = load_data(USER_DATA_PATH, JOB_DATA_PATH)

        # 2) 텍스트 병합 및 코퍼스 생성
        user_df, job_df, corpus = build_merged_text(user_df, job_df)

        # 3) TF-IDF 벡터라이저 생성
        vectorizer = build_vectorizer(corpus)

        # 4) 추천 실행
        recommended_jobs = get_recommend(
            userid=userid,
            num_jobs=num_jobs,
            user_df=user_df,
            job_df=job_df,
            vectorizer=vectorizer,
        )

        # 5) 결과 출력
        if recommended_jobs is not None:
            show_results(userid, user_df, recommended_jobs)
    
