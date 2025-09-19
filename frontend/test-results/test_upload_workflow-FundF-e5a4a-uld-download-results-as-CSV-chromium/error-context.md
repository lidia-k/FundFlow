# Page snapshot

```yaml
- generic [ref=e2]:
  - generic [ref=e3]:
    - generic [ref=e4]:
      - banner [ref=e5]:
        - generic [ref=e7]:
          - generic [ref=e8]:
            - img [ref=e9]
            - heading "FundFlow" [level=1] [ref=e11]
          - navigation [ref=e12]:
            - link "Dashboard" [ref=e13] [cursor=pointer]:
              - /url: /
              - img [ref=e14] [cursor=pointer]
              - text: Dashboard
            - link "Upload" [ref=e16] [cursor=pointer]:
              - /url: /upload
              - img [ref=e17] [cursor=pointer]
              - text: Upload
      - main [ref=e19]:
        - generic [ref=e20]:
          - paragraph [ref=e21]: Results not found
          - link "Back to Dashboard" [ref=e22] [cursor=pointer]:
            - /url: /
      - contentinfo [ref=e23]:
        - generic [ref=e25]:
          - paragraph [ref=e26]: © 2025 FundFlow. All rights reserved.
          - paragraph [ref=e27]: Version 1.2.0 (Prototype)
    - region "Notifications (F8)":
      - list
  - generic:
    - status [ref=e33]: Failed to load calculation results
    - status [ref=e39]: Failed to load calculation results
```