---
title: 부분분수
icon: /
oneline: 1/(n(n+1)) 을 1/n − 1/(n+1) 처럼 두 분수의 차로 쪼개는 것
related: [telescoping]
---

## graph

curve: 160 - 100*(1 - 0.5**n)
lines: [60]
label: S_n
label_at: right

## steps

| show | line | label | caption |
|------|------|-------|---------|
| 3  |   |   | 1/(1·2), 1/(2·3), 1/(3·4) … 를 부분분수로 쪼개요. |
| 8  |   |   | 각 항이 1/n − 1/(n+1) 로 바뀌어요. |
| 12 |   |   | 더하면 가운데 항들이 줄줄이 사라져요. |
| 12 | v | v | 첫 항과 끝 항만 남아 부분합이 정해져요. |
