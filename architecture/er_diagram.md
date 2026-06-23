# Er Diagram

```mermaid
erDiagram
    USERS ||--o{ SUBSCRIPTIONS : owns
    PLANS ||--o{ SUBSCRIPTIONS : prices
    SUBSCRIPTIONS ||--o{ PAYMENTS : bills
    USERS ||--o{ PRODUCT_USAGE : generates
    USERS ||--o{ SUPPORT_TICKETS : opens
    SUBSCRIPTIONS ||--o{ CHURN_EVENTS : may_churn
```
