## FundFlow TDD v1.1 (개정판)

### **주요 변경 사항 (Key Changes)**

- **아키텍처 단순화:** '실시간 규제 모니터링'을 위한 웹 스크래핑, NLP 관련 **마이크로서비스가 아키텍처에서 완전히 제거**되었습니다.
    
- **핵심 모듈 변경:** 가장 중요한 기술적 과제가 **'EY 엑셀 데이터 파서 및 버전 관리 시스템'**으로 변경되었습니다.
    
- **플랫폼 전략 확정:** **`fundflow.com` 독립 사이트를 먼저 구축**하고, 시장 반응에 따라 단계적으로 **Salesforce와 연동하는 하이브리드 전략**을 채택했습니다.
    
- **데이터베이스 설계:** `state_tax_rules` 테이블에 `source_provider (e.g., 'EY')`, `source_version` 등 데이터 출처를 명확히 하는 컬럼이 추가되었습니다.
    

## **Technical Design Document: FundFlow**

**AI-Powered PE Back-Office Automation Platform**

Version: 1.1 (EY 데이터 및 하이브리드 플랫폼 전략 적용)

Date: 2025년 8월 26일

Authors: Chris (Product Lead), 민우 (Technical Co-founder)

### **1. 시스템 아키텍처 개요 (System Architecture Overview)**

#### **1.1. 상위 수준 아키텍처 (High-Level Architecture)**

FundFlow는 PE 펀드의 SALT(State and Local Tax) 계산을 자동화하는 AI 기반 플랫폼으로, **모듈형 모놀리스(Modular Monolith) + 이벤트 기반(Event-driven)** 하이브리드 아키텍처를 채택합니다. 이 구조는 MVP 단계의 빠른 개발 속도와 향후 마이크로서비스로의 확장성을 동시에 확보합니다.

#### **1.2. 기술 스택 (Technology Stack)**

- **Backend Framework:** Python 3.11 + FastAPI + Pydantic
    
- **Excel Processing:** pandas + openpyxl + xlsxwriter
    
- **Calculation Engine:** NumPy + pandas (vectorized SALT calculations)
    
- **Task Queue:** Celery + Redis
    
- **Database:** PostgreSQL + Redis (cache)
    
- **Cloud:** AWS (ECS Fargate + RDS + S3 + ElastiCache)
    
- **Frontend:** React + TypeScript (Phase 1)
    
- **Monitoring:** DataDog + AWS CloudWatch
    

#### **1.3. 설계 원칙 (Design Principles)**

1. **성능 최우선 (Performance First):** 100MB 엑셀 파일 1분 이내 처리 목표
    
2. **SOC 2 준수 (SOC 2 Ready):** 보안과 감사 추적을 처음부터 설계에 포함
    
3. **모듈형 아키텍처 (Modular Architecture):** 향후 마이크로서비스 전환 가능한 내부 모듈화
    
4. **무결점 안정성 (Error Resilience):** PE 펀드 특성상 99.9% 가용성 및 제로 오류 목표
    

### **2. 엑셀 처리 파이프라인 (Excel Processing Pipeline)**

#### **2.1. 파이프라인 아키텍처**

FundFlow의 핵심 기능인 Excel 처리는 다음 파이프라인을 통해 수행됩니다. 이는 API 응답성을 유지하고 대용량 파일 처리를 안정적으로 수행하기 위함입니다.

`파일 업로드 (React)` → `S3 저장 및 작업 큐잉 (FastAPI)` → `비동기 처리 (Celery)` → `결과 생성 및 저장 (S3)`

#### **2.2. 엑셀 처리 기술 선정**

리서치 결과에 기반하여, 다음과 같은 최적화된 라이브러리 조합을 사용합니다.

- **읽기:** `pandas` + `openpyxl` (read-only mode) 조합으로 기본 `read_excel()` 대비 **최대 10배 성능 향상** 및 **50배 메모리 절약**
    
- **쓰기:** `xlsxwriter`를 사용하여 `openpyxl` 대비 **4배 높은 메모리 효율**로 원본 서식을 보존하며 결과 파일 생성
    

#### **2.3. 파일 처리 워크플로우**

1. **업로드 및 검증:** 사용자가 React 프론트엔드에서 100MB 이하의 엑셀 파일을 업로드하면, FastAPI 엔드포인트는 파일 형식과 크기를 검증합니다.
    
2. **S3 저장 및 작업 생성:** 검증된 파일은 즉시 S3 버킷에 업로드되고, 관련 메타데이터(사용자 ID, 파일 경로 등)와 함께 PostgreSQL `salt_jobs` 테이블에 새로운 작업 레코드가 생성됩니다.
    
3. **비동기 처리:** Celery에 새로운 계산 작업이 전달되어 Redis 큐에 쌓입니다. API는 사용자에게 즉시 `job_id`를 반환합니다.
    
4. **백그라운드 실행:** ECS Fargate에서 실행되는 Celery 워커가 큐에서 작업을 가져와 S3의 파일을 다운로드하고, 최적화된 방식으로 읽어 SALT 계산을 수행합니다.
    
5. **결과 저장 및 알림:** 계산이 완료되면 결과 엑셀 파일이 S3에 저장되고, `salt_jobs` 테이블의 상태가 'completed'로 업데이트되며, WebSocket을 통해 사용자에게 실시간 알림이 전송됩니다.
    

### **3. SALT 계산 엔진 (SALT Calculation Engine)**

#### **3.1. 핵심 설계 변경**

'EY 데이터 우선' 전략에 따라, 자체적으로 세법을 해석하는 대신 **EY에서 제공하는 정제된 엑셀 데이터를 '규칙의 원천(Source of Rules)'으로 사용**합니다.

#### **3.2. 데이터 모델 및 알고리즘**

- **데이터 임포트:** EY 엑셀을 시스템에 업로드하면, 파서는 `state_tax_rules` 테이블에 주별 배분 공식(Apportionment Formula), 세율, 특수 규칙(Throwback/Throwout) 등을 버전 정보와 함께 저장합니다.
    
- **계산 알고리즘:**
    
    1. 고객의 포트폴리오 데이터를 불러옵니다.
        
    2. `state_tax_rules` 테이블에서 현재 유효한 EY 규칙 세트를 가져옵니다.
        
    3. **NumPy 벡터화 연산**을 사용하여 50개 주의 배분 비율을 병렬로 빠르게 계산합니다.
        
    4. 계산된 비율을 각 포트폴리오 회사의 재무 데이터와 LP 지분율에 적용하여 최종 할당액을 도출합니다.
        

### **4. AWS 클라우드 인프라 (AWS Cloud Infrastructure)**

FundFlow는 AWS 클라우드에서 **고가용성(High Availability) + 보안 최우선(Security First)** 원칙으로 설계됩니다.

- **컴퓨팅 (Compute):** **AWS ECS Fargate**를 사용하여 서버 관리 없이 컨테이너를 실행합니다. API 서버와 Celery 워커는 별도의 서비스로 구성되며, 트래픽과 작업량에 따라 독립적으로 자동 확장(Auto-Scaling)됩니다.
    
- **데이터베이스 (Database):** **AWS RDS PostgreSQL**을 **Multi-AZ** 구성으로 사용하여 데이터베이스 장애 시 자동 복구를 지원합니다.
    
- **캐시 & 큐 (Cache & Queue):** **AWS ElastiCache for Redis**를 사용하여 Celery 작업 큐와 자주 사용되는 세법 규칙 등을 캐싱합니다.
    
- **스토리지 (Storage):** **Amazon S3**를 사용하여 업로드된 엑셀 파일과 결과 파일을 안전하게 저장하며, 버전 관리를 활성화합니다.
    

### **5. SOC 2 보안 프레임워크 (SOC 2 Security Framework)**

MVP 단계부터 PE 업계 표준인 **SOC 2 Type II** 컴플라이언스를 준수하도록 설계합니다.

- **감사 추적 (Audit Trail):** 모든 사용자 활동(로그인, 파일 업로드/다운로드, 계산 실행)과 시스템 이벤트를 `audit_logs` 테이블에 기록합니다.
    
- **접근 제어 (Access Controls):** **역할 기반 접근 제어(RBAC)**를 구현하여 'Admin', 'Tax Director', 'Viewer' 등 역할별로 명확한 권한을 부여합니다.
    
- **데이터 암호화 (Data Encryption):** S3와 RDS에 저장되는 모든 데이터는 **저장 시 암호화(Encryption at Rest)**되며, 모든 API 통신은 **전송 중 암호화(Encryption in Transit)**를 위해 TLS 1.3을 강제합니다.
    
- **네트워크 보안:** 모든 인프라는 Private Subnet 내에서 실행되는 **AWS VPC**로 구성되며, Security Group을 통해 엄격한 접근 제어를 적용합니다.
    

### **6. API 설계 (API Design)**

API는 OpenAPI 3.0 표준을 따르며, 비동기 작업 처리에 최적화되어 있습니다.

- **/api/v1/files/upload:** 엑셀 파일을 업로드하고 즉시 `job_id`를 반환합니다. (202 Accepted)
    
- **/api/v1/jobs/{job_id}/status:** 특정 작업의 진행 상태(queued, processing, completed, failed)를 확인합니다.
    
- **/api/v1/results/{job_id}/download:** 완료된 작업의 결과 파일을 안전하게 다운로드할 수 있는 임시 URL을 제공합니다.
    
- **/ws/jobs/{user_id}:** WebSocket을 통해 작업 상태 변경을 실시간으로 클라이언트에 푸시합니다.
    

### **7. 데이터베이스 설계 (Database Design)**

PostgreSQL 15를 사용하며, PE 펀드 운영에 최적화된 정규화된 스키마를 설계합니다.

- **핵심 테이블:** `users`, `funds`, `limited_partners`, `portfolio_companies`, `salt_jobs`, `salt_calculations`, `state_tax_rules`, `audit_logs` 등
    
- **성능 최적화:** 주요 조회 경로에 복합 인덱스(Composite Indexes)를 생성하고, 대용량 `audit_logs` 테이블은 월별 파티셔닝을 적용합니다.
    
- **데이터 무결성:** `state_tax_rules` 테이블에 `source_provider` ('EY'), `source_document_version` 컬럼을 추가하여 데이터의 출처와 버전을 명확히 추적합니다.
    

### **8. 성능 및 확장성 (Performance & Scalability)**

- **성능 목표:** 100MB 엑셀 파일 60초 내 처리, API 응답 시간 P95 기준 500ms 이하.
    
- **확장성 전략:**
    
    - **컴퓨팅:** Redis 큐 길이를 기반으로 Celery 워커 ECS 작업을 자동 확장합니다.
        
    - **데이터베이스:** 초기에는 Multi-AZ로 안정성을 확보하고, 향후 읽기 전용 복제본(Read Replicas)을 추가하여 읽기 성능을 확장합니다.
        

### **9. Salesforce 통합 전략 (Salesforce Integration Strategy)**

리스크를 최소화하고 시장 커버리지를 극대화하기 위해 단계적 접근법을 채택합니다.

- **Phase 1 (MVP):** `fundflow.com` 독립 플랫폼 개발에 집중합니다.
    
- **Phase 2 (연동):** **Salesforce Connected App**을 개발하여 API 기반으로 데이터 동기화를 구현합니다. 사용자는 Salesforce 내에서 FundFlow를 호출하고 결과를 받아볼 수 있습니다.
    
- **Phase 3 (네이티브 앱 - 선택):** 시장 수요가 충분할 경우, **Lightning Web Components (LWC)**를 사용하여 Salesforce에 완전히 내장된 네이티브 앱을 개발합니다.
    

### **10. 모니터링 및 관측 가능성 (Monitoring & Observability)**

- **로깅:** 모든 로그는 JSON 형식으로 구조화하여 **AWS CloudWatch**로 전송합니다.
    
- **메트릭:** **DataDog**을 사용하여 핵심 애플리케이션 및 인프라 메트릭(작업 처리 시간, 큐 길이, CPU/메모리 사용량 등)을 수집하고 대시보드를 구성합니다.
    
- **알림:** 작업 실패, 성능 저하, 보안 이벤트 등 주요 이슈 발생 시 **Slack 및 PagerDuty**로 자동 알림을 발송합니다.
    

### **11. 배포 및 DevOps (Deployment & DevOps)**

**GitHub Actions**를 사용하여 완전 자동화된 CI/CD 파이프라인을 구축합니다.

1. **CI (Continuous Integration):** `develop` 브랜치에 푸시될 때마다 자동으로 코드 린팅, 단위 테스트, 통합 테스트를 실행합니다.
    
2. **CD (Continuous Deployment):** `main` 브랜치에 병합되면, Docker 이미지를 빌드하여 **Amazon ECR**에 푸시하고, 자동으로 Staging 환경에 배포합니다.
    
3. **Production 배포:** Staging 환경에서 자동화된 스모크 테스트 통과 후, 수동 승인을 통해 Production 환경에 **Blue/Green 방식**으로 무중단 배포를 진행합니다.
    

### **12. 테스트 전략 (Testing Strategy)**

- **단위 테스트 (`pytest`):** 모든 핵심 로직(특히 계산 엔진)에 대해 90% 이상의 코드 커버리지를 목표로 합니다.
    
- **통합 테스트:** API, Celery, Redis, PostgreSQL 간의 상호작용을 테스트합니다.
    
- **성능 테스트:** 다양한 크기(10MB, 50MB, 100MB)의 샘플 엑셀 파일로 부하 테스트를 수행하여 성능 목표 달성 여부를 검증합니다.
    
- **보안 테스트:** 정기적인 취약점 스캔 및 모의 해킹을 수행합니다.