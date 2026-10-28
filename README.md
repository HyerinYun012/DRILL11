# DRILL11

`pico2d`와 `transitions` 상태 머신을 사용한 캐릭터 애니메이션 실습 프로젝트입니다.

## 실행

Python 환경에 `pico2d`와 `transitions`를 설치한 뒤 다음 명령을 실행합니다.

```bash
python DRILL11.py
```

## 조작법

| 키 | 동작 |
|---|---|
| `←` / `→` | 해당 방향으로 일반 달리기 |
| `A` | `IDLE` 상태에서 AutoRun 시작 |
| `Space` | `SLEEP` 상태에서 깨우기 |
| `Escape` | 프로그램 종료 |

AutoRun은 일반 달리기보다 3배 빠르고 캐릭터가 1.5배 크게 표시됩니다. 화면 좌우 끝에서 자동으로 방향을 바꾸며, 5초 후 `IDLE`로 돌아갑니다. AutoRun 중 방향키를 누르면 즉시 해당 방향의 일반 달리기로 전환됩니다.

## 테스트

단위 테스트는 `pico2d`와 `transitions`를 테스트 대역으로 교체하므로 Python 표준 라이브러리만으로 실행할 수 있습니다.

```bash
python -m unittest test_boy.py
```

상세 요구사항과 상태 다이어그램은 [`PRD.md`](PRD.md)를 참고하세요.
