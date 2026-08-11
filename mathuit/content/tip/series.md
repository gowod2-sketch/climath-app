---
title: 무한급수
icon: sum
oneline: 수열의 모든 항을 끝없이 더한 것
related: [partial, sumval]
---

## graph

curve: 160-100*(1-Math.pow(0.5,n))
lines: [60]
label: 합 S
label_at: right

## steps

| show | line | label | caption |
|------|------|-------|---------|
| 3 |  |  | 항을 하나씩 더해 부분합을 만들어요. |
| 12 |  |  | 더할수록 부분합이 천천히 늘어요. |
| 12 | v | v | 부분합이 S에 수렴하면 급수가 수렴. |
