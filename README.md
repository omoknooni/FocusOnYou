# FocusOnYou

Automatic Person Tracking Video Service  
[Project Description](https://omoknooni.tistory.com/78)

## Architecture
![architecture.png](./mdImg/architecture.png)

## Requirement
- AWS CLI
- `>= Terraform v1.11`
- `>= nodejs v22.12`

## Deploy with Terraform cloud
Terraform을 사용해서 deploy 가능  
(현재 이 프로젝트는 Terraform cloud를 사용했음)  

### 1. 인증구간을 위한 Cognito userpool, 도메인, app-client 생성
- User pool : Cognito를 통해 관리할 사용자 목록
- 도메인 : Cognito 인증을 수행하는 도메인
- app-client : app을 userpool에 연결하기 위한 클라이언트
### 2. 정적호스팅 버킷 생성  
클라이언트가 접근할 프론트엔드용 버킷 생성 (반드시 프로젝트 리소스들과 동일한 리전에 생성)  
- 버킷정책 허용 (GetObject)
- 버킷 퍼블릭 액세스 허용
### 3. 백엔드 API 서버 + 미디어 버킷 등 AWS 리소스 프로비저닝  
deploy의 terraform code에 따라 프로비저닝  
정적호스팅 버킷의 이름은 미리 지정해둠  
### 4. 정적호스팅 버킷을 위한 프론트엔드 react 빌드  
미리 지정해둔 정적호스팅 버킷명을 비롯한 정보들을 frontend/.env에 지정 후 빌드
```
REACT_APP_COGNITO_REGION=
REACT_APP_COGNITO_USER_POOL_ID=
REACT_APP_COGNITO_APP_CLIENT_ID=
REACT_APP_COGNITO_DOMAIN=
REACT_APP_REDIRECT_SIGN_IN=[로그인 이후 리다이렉트될 경로]
REACT_APP_REDIRECT_SIGN_OUT=[로그아웃 이후 리다이렉트될 경로]
REACT_APP_API_URL=[백엔드 API서버 URL]
```
### 5. 빌드 결과물 정적호스팅 버킷에 업로드