# GitHub Pages 배포 가이드 (상세)

완전 초보자 기준으로 GitHub 계정 생성부터 공개 URL 확보까지 단계별 가이드.

---

## 0. 사전 준비

- [GitHub 계정](https://github.com/signup) (없으면 가입, 무료)
- Git 설치: 
  - **Mac**: `brew install git` 또는 [Xcode Command Line Tools](https://developer.apple.com/xcode/resources/)
  - **Windows**: [Git for Windows](https://git-scm.com/download/win)
  - 확인: 터미널에서 `git --version`
- 이 zip을 푼 폴더 경로 알기 (예: `~/Downloads/tge-dashboard/`)

---

## 1. 레포지토리 생성

### GitHub 웹에서

1. 우측 상단 `+` → **New repository**
2. **Repository name**: `tge-dashboard` (원하는 이름 OK, 단 소문자/하이픈 권장)
3. **Public** 선택 (GitHub Pages 무료 플랜은 public만 지원)
4. **Add a README**, **Add .gitignore**, **License** 셋 다 **체크하지 말기** (이미 로컬에 있음)
5. **Create repository** 클릭

생성되면 주소 확인: `https://github.com/londonpotato1/tge-dashboard`

---

## 2. 로컬에서 푸시

터미널에서 압축 푼 폴더로 이동:

```bash
cd ~/Downloads/tge-dashboard
```

Git 초기 설정 (한 번만):

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

레포 초기화 & 푸시:

```bash
git init
git add .
git commit -m "Initial commit: TGE & FDV Dashboard"
git branch -M main
git remote add origin https://github.com/londonpotato1/tge-dashboard.git
git push -u origin main
```

처음 푸시할 때 GitHub 로그인 요청이 뜨면:
- **Username**: GitHub 아이디
- **Password**: GitHub 비밀번호 말고 **Personal Access Token** 사용
  - 토큰 발급: Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token → `repo` 권한 체크 → Generate
  - 토큰을 복사해서 비밀번호 자리에 붙여넣기

또는 SSH 키 세팅을 추천합니다: [GitHub SSH 가이드](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)

---

## 3. GitHub Pages 활성화

1. 레포 페이지 이동: `https://github.com/londonpotato1/tge-dashboard`
2. 상단 탭 **Settings** 클릭
3. 좌측 메뉴 **Pages** 클릭
4. **Build and deployment** 섹션:
   - **Source**: `Deploy from a branch`
   - **Branch**: `main` 선택 → `/ (root)` → **Save**
5. 1-2분 대기 후 페이지 새로고침하면 상단에 
   ```
   Your site is live at https://londonpotato1.github.io/tge-dashboard/
   ```
   메시지 표시됨

이 URL로 접속 확인!

---

## 4. 이후 업데이트하기

`data/projects.json`이나 `index.html` 수정 후:

```bash
git add .
git commit -m "Update: 프로젝트 데이터 업데이트"
git push
```

1-2분 후 자동 반영됩니다.

### 진행 상황 확인

레포 페이지의 **Actions** 탭에서 `pages build and deployment` 워크플로가 성공했는지 확인 가능.

---

## 5. 커스텀 도메인 연결 (선택)

본인 도메인 `tge.example.com` 사용하려면:

### GitHub 쪽

1. Settings → Pages → **Custom domain**에 `tge.example.com` 입력 → Save
2. 루트 폴더에 `CNAME` 파일이 자동 생성됨 (레포에 커밋됨)

### DNS 쪽 (도메인 등록업체 콘솔)

| Type  | Name | Value |
|-------|------|-------|
| CNAME | tge  | `londonpotato1.github.io` |

DNS 전파에 최대 24시간. 확인:
```bash
dig tge.example.com +short
```

### HTTPS 강제

GitHub 쪽 설정 완료 후 Settings → Pages → **Enforce HTTPS** 체크.

---

## 문제 해결

### "데이터 로딩 실패" 메시지가 뜸

- `data/projects.json` 파일이 레포에 잘 푸시되었는지 확인
- 브라우저 개발자 도구 (F12) → Network 탭에서 404 확인

### 스타일이 깨짐

- 브라우저 캐시 강제 새로고침: `Cmd+Shift+R` (Mac) / `Ctrl+Shift+R` (Win)
- Pages 배포는 CDN 캐시가 있어 몇 분 걸림

### 로컬에서 index.html을 더블클릭하면 데이터 안 뜸

`file://` 프로토콜에선 fetch가 CORS로 막힘. 로컬 서버 필요:

```bash
# Python 3 (대부분 기본 설치됨)
cd ~/Downloads/tge-dashboard
python3 -m http.server 8000
```

브라우저에서 `http://localhost:8000` 접속.

### Git push가 `rejected` 거부됨

레포 생성 시 README나 LICENSE 체크했으면 이미 원격에 파일이 있어서 충돌:

```bash
git pull --rebase origin main
git push
```

---

## 자동 업데이트 (선택, 고급)

CryptoDep나 Polymarket에서 데이터 자동 갱신하고 싶으면 GitHub Actions로 cron 워크플로 가능. 이 zip에는 미포함 (수동 업데이트가 더 안전).

관심 있으시면 말씀하세요 — Python 스크립트 + `.github/workflows/update.yml` 추가해드립니다.
