# -*- coding: utf-8 -*-
"""JOB_DATA.csv 개인정보 마스킹.

공개 저장소에 두는 표본은 마스킹본만 둔다. 원본은 git 밖(.workspace/_private/)에 보관하고,
서비스에서 실제 담당자 연락처를 안내해야 할 때는 원본을 DB 로 적재해 접근통제 하에 사용한다.

마스킹 규칙
  이름   김현욱 -> 김*욱  /  김철 -> 김*  /  남궁민수 -> 남**수  /  Soojeong Kim -> S***** K**
  전화   010-2776-9672 -> 010-****-9672   (지역/사업자 국번과 끝 4자리 유지)
  이메일 gaeon.kim@kurlycorp.com -> ga***@kurlycorp.com   (도메인 유지)

이름 컬럼에는 기관명("부산광역시 사하구청")도 섞여 있다. 개인명 형태로 판별되는 값만 마스킹하고
나머지는 그대로 두되, 실행 후 리포트의 [미마스킹] 목록으로 사람이 확인한다.

사용:  python mask_pii.py            # 검사만 (파일 안 씀)
       python mask_pii.py --write    # dataset/JOB_DATA.csv 를 마스킹본으로 교체
"""
import csv, io, os, re, sys, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "dataset", "JOB_DATA.csv")
PRIVATE_DIR = os.path.join(HERE, ".workspace", "_private")   # .gitignore 의 .workspace/ 에 포함
ORIG = os.path.join(PRIVATE_DIR, "JOB_DATA.original.csv")

NAME_COLS = ["담당자명", "기업정보.대표자"]
PHONE_COLS = ["연락처"]
EMAIL_COLS = ["이메일"]
# 자유텍스트에도 전화/이메일이 박혀 있다
SCRUB_COLS = ["접수방법", "전형일정", "담당업무", "우대조건", "복리후생",
              "작업환경", "근무시간/요일", "제목", "근무지역", "홈페이지"]

TITLE = (r"직업훈련교사|사회복지사|직업\s*상담사|고용지원관|사무국장|상담사|지원관|"
         r"교사|과장|부장|팀장|대리|주임|사원|실장|원장|담당자|담당|선생님|"
         r"매니저|이사|대표|소장|국장|차장|계장|주무관|간사|팀원|센터장|본부장")

# 이름 자리에 들어오지만 개인명이 아닌 것들 — 직무/부서/지자체 토큰
NAME_STOP = {"인사", "채용", "직업", "사회", "장애", "장애인", "노인", "아동", "여성", "청년",
             "고용", "총무", "시설", "사무", "담당", "모집", "일반", "현장", "생산", "영업",
             "관리", "운영", "복지", "교육", "행정", "간호", "조리", "환경", "안전"}
# 기관명으로 끝나면 개인명이 아니다
# ※ 4자 이상에만 적용한다. '조병원' 처럼 3자 성명이 '병원' 으로 오판되는 것을 막기 위함.
#   '지사' 는 '복지사' 와 충돌해 제외.
RE_ORG_TAIL = re.compile(r"(청|센터|학교|행정실|재단|협회|공단|공사|병원|복지관|사업|지원팀|"
                         r"지원과|사업소|본부|지점|사업단|위원회)$")

RE_KOR_ONLY   = re.compile(r"^[가-힣]{2,4}$")     # 한국 성명은 2~4자. 5자 이상은 기관명일 확률이 높다
RE_KOR_TITLE  = re.compile(r"^([가-힣]{2,4})\s*[\(（]?\s*(?:%s)" % TITLE)
RE_ENG_NAME   = re.compile(r"^[A-Za-z][A-Za-z'\-]+(?:\s+[A-Za-z][A-Za-z'\-]+){1,3}$")
RE_ENG_KOR    = re.compile(r"^([A-Za-z][A-Za-z'\-\s]+?)\s*\(([가-힣]+)\)$")

RE_PHONE = re.compile(r"0\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{4}")
RE_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

NOT_A_VALUE = {"", "정보 없음", "해당 내용 없음", "무관", "-", "N/A", "없음"}


def mask_kor_name(n):
    if len(n) <= 1:
        return "*"
    if len(n) == 2:
        return n[0] + "*"
    return n[0] + "*" * (len(n) - 2) + n[-1]


def mask_eng_name(n):
    out = []
    for w in n.split():
        out.append(w[0] + "*" * max(len(w) - 1, 1))
    return " ".join(out)


def mask_name_value(v):
    """개인명으로 판별되면 (마스킹값, True), 아니면 (원값, False)."""
    v = v.strip()
    if v in NOT_A_VALUE:
        return v, False
    # 순서 주의: "이름+직함" 이 가장 강한 개인명 신호이므로 기관명 판정보다 먼저 본다
    m = RE_KOR_TITLE.match(v)
    if m and m.group(1) not in NAME_STOP:
        return v.replace(m.group(1), mask_kor_name(m.group(1)), 1), True
    if len(v) >= 4 and RE_ORG_TAIL.search(v):
        return v, False
    m = RE_ENG_KOR.match(v)
    if m:
        return "%s(%s)" % (mask_eng_name(m.group(1).strip()), mask_kor_name(m.group(2))), True
    if RE_KOR_ONLY.match(v) and v not in NAME_STOP:
        return mask_kor_name(v), True
    if RE_ENG_NAME.match(v):
        return mask_eng_name(v), True
    return v, False


def mask_phone_token(t):
    """앞 국번과 끝 4자리를 남기고 가운데를 가린다."""
    parts = re.split(r"([-.\s])", t)
    digits = [i for i, p in enumerate(parts) if p.isdigit()]
    if len(digits) < 2:
        d = re.sub(r"\D", "", t)
        return d[:3] + "*" * max(len(d) - 7, 0) + d[-4:] if len(d) > 7 else "*" * len(d)
    for i in digits[1:-1]:
        parts[i] = "*" * len(parts[i])
    return "".join(parts)


def mask_email_token(t):
    local, _, dom = t.partition("@")
    keep = 2 if len(local) > 2 else 1
    return local[:keep] + "***@" + dom


def scrub_text(v):
    n = 0
    def _p(m):
        nonlocal n; n += 1; return mask_phone_token(m.group(0))
    def _e(m):
        nonlocal n; n += 1; return mask_email_token(m.group(0))
    v = RE_EMAIL.sub(_e, v)
    v = RE_PHONE.sub(_p, v)
    return v, n


def main():
    write = "--write" in sys.argv
    rows = list(csv.DictReader(io.open(SRC, encoding="utf-8-sig")))
    cols = list(rows[0].keys())

    stat = {"name": 0, "name_skipped": [], "phone": 0, "email": 0, "scrub": 0}

    for r in rows:
        for c in NAME_COLS:
            v = (r.get(c) or "").strip()
            if not v:
                continue
            nv, done = mask_name_value(v)
            r[c] = nv
            if done:
                stat["name"] += 1
            elif v not in stat["name_skipped"]:
                stat["name_skipped"].append(v)
        for c in PHONE_COLS:
            v = r.get(c) or ""
            if v.strip() in NOT_A_VALUE:
                continue
            nv, n = scrub_text(v)
            r[c] = nv; stat["phone"] += n
        for c in EMAIL_COLS:
            v = r.get(c) or ""
            if v.strip() in NOT_A_VALUE:
                continue
            nv, n = scrub_text(v)
            r[c] = nv; stat["email"] += n
        for c in SCRUB_COLS:
            v = r.get(c) or ""
            if not v:
                continue
            nv, n = scrub_text(v)
            r[c] = nv; stat["scrub"] += n

    # 잔존 검증 — 마스킹 후 남은 원문 전화/이메일
    res_p = res_e = 0
    for r in rows:
        for v in r.values():
            if not v:
                continue
            res_e += len([t for t in RE_EMAIL.findall(v) if "***@" not in t])
            res_p += len([t for t in RE_PHONE.findall(v) if "*" not in t])

    print("행 %d / 컬럼 %d" % (len(rows), len(cols)))
    print("  이름 마스킹      %d건" % stat["name"])
    print("  전화 마스킹      %d건 (연락처 컬럼)" % stat["phone"])
    print("  이메일 마스킹    %d건 (이메일 컬럼)" % stat["email"])
    print("  자유텍스트 스크럽 %d건" % stat["scrub"])
    print("  [잔존] 원문 전화 %d건 / 원문 이메일 %d건" % (res_p, res_e))
    if stat["name_skipped"]:
        print("\n  [미마스킹] 개인명으로 판별되지 않은 값 %d종 — 육안 확인 대상:"
              % len(stat["name_skipped"]))
        for v in stat["name_skipped"][:25]:
            print("    -", v)
        if len(stat["name_skipped"]) > 25:
            print("    ... 외 %d종" % (len(stat["name_skipped"]) - 25))

    if not write:
        print("\n(검사만 수행. 실제 교체는 --write)")
        return

    os.makedirs(PRIVATE_DIR, exist_ok=True)
    if not os.path.exists(ORIG):
        shutil.copy2(SRC, ORIG)
        print("\n원본 보관: .workspace/_private/JOB_DATA.original.csv (git 미추적)")
    tmp = SRC + ".tmp"
    with io.open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader(); w.writerows(rows)
    os.replace(tmp, SRC)
    print("교체 완료: dataset/JOB_DATA.csv")


if __name__ == "__main__":
    main()
