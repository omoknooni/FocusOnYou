# Focus On You - Frontend
AWS Amplify와 Cognito를 활용한 인증 기능을 갖춘 React 기반 프론트엔드 애플리케이션입니다.  
FocusOnYou의 메인 workload를 트리거하기 위한 파일업로드, Job의 실행현황, 결과물들을 확인하기 위함
## 기능 개요

- AWS Cognito를 통한 사용자 인증 (로그인/로그아웃)
- 인증된 사용자만 접근 가능한 보호된 라우트
- 이미지와 비디오 업로드 기능
- 작업 목록 조회 및 상세 정보 확인

## 프로젝트 구조

```
frontend/
├── public/                # 정적 파일
├── src/
│   ├── components/        # 재사용 가능한 컴포넌트
│   │   ├── NavBar.jsx     # 네비게이션 바
│   │   ├── RequireAuth.jsx # 인증 필요 라우트 보호
│   │   └── Logout.jsx     # 로그아웃 처리
│   ├── contexts/
│   │   └── AuthContext.js # 인증 상태 관리
│   ├── pages/             # 페이지 컴포넌트
│   │   ├── Home.jsx       # 홈 페이지
│   │   ├── Login.jsx      # 로그인 페이지
│   │   ├── Upload.jsx     # 파일 업로드 페이지
│   │   ├── JobsList.jsx   # 작업 목록 페이지
│   │   └── JobDetail.jsx  # 작업 상세 페이지
│   ├── services/
│   │   └── api.js         # API 호출 설정
│   ├── App.js             # 라우트 설정
│   └── index.js           # 앱 진입점
└── .env                   # 환경 변수
```

## 라우트 구성

| 경로 | 컴포넌트 | 설명 | 인증 필요 |
|------|---------|------|----------|
| `/` | `Home` | 홈 페이지 | 아니오 |
| `/login` | `Login` | 로그인 페이지 | 아니오 |
| `/logout` | `Logout` | 로그아웃 처리 | 아니오 |
| `/upload` | `Upload` | 파일 업로드 | 예 |
| `/jobs` | `JobsList` | 작업 목록 | 예 |
| `/jobs/:jobId` | `JobDetail` | 작업 상세 정보 | 예 |

## 인증 로직

- `AuthContext.js`에서 AWS Amplify Auth API를 사용하여 인증 상태 관리
- 로그인 시 JWT 토큰을 받아 API 요청 헤더에 포함
- 인증이 필요한 라우트는 `RequireAuth` 컴포넌트로 보호

## 환경 설정

프로젝트 실행 전 `.env` 파일을 생성하고 다음 환경 변수를 설정해야 합니다:

```
REACT_APP_COGNITO_REGION=       # Cognito 리전 (예: us-east-1)
REACT_APP_COGNITO_USER_POOL_ID= # Cognito 사용자 풀 ID
REACT_APP_COGNITO_APP_CLIENT_ID= # Cognito 앱 클라이언트 ID
REACT_APP_COGNITO_DOMAIN=       # Cognito 호스팅 UI 도메인 (http 스킴 미포함)
REACT_APP_REDIRECT_SIGN_IN=     # 로그인 후 리디렉션 URL
REACT_APP_REDIRECT_SIGN_OUT=    # 로그아웃 후 리디렉션 URL
REACT_APP_API_URL=              # 백엔드 API URL
```

`.env.example` 파일을 복사하여 `.env` 파일을 생성하고 적절한 값을 입력하세요.

## 빌드 및 실행

### 개발 환경

```bash
# 의존성 설치
yarn install

# 개발 서버 실행
yarn start
```

### 프로덕션 빌드

```bash
yarn build

# 빌드된 파일은 build/ 디렉토리에 생성됩니다
# 이 파일들을 S3 버킷에 업로드하여 정적 웹사이트로 호스팅할 수 있습니다
```

## AWS Amplify 구성

`index.js`에서 Amplify를 다음과 같이 구성합니다:

```javascript
Amplify.configure({
  Auth: {
    Cognito: {
      region: process.env.REACT_APP_COGNITO_REGION,
      userPoolId: process.env.REACT_APP_COGNITO_USER_POOL_ID,
      userPoolClientId: process.env.REACT_APP_COGNITO_APP_CLIENT_ID,
      loginWith: {
        oauth: {
          domain: process.env.REACT_APP_COGNITO_DOMAIN,
          scopes: ['openid', 'email', 'profile'],
          redirectSignIn: [process.env.REACT_APP_REDIRECT_SIGN_IN],
          redirectSignOut: [process.env.REACT_APP_REDIRECT_SIGN_OUT],
          responseType: 'code'
        }
      }
    }
  }
});
```

## 백엔드 연동

- 백엔드 API는 FastAPI로 구현되어 있으며, 인증된 사용자만 접근 가능
- API 요청 시 JWT 토큰을 Authorization 헤더에 포함하여 전송
- 파일 업로드는 S3 presigned URL을 통해 직접 S3에 업로드