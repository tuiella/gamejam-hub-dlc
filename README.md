# GameJam Hub DLC

GameJam Hub에서 내려받는 콘텐츠 팩입니다. 호스트가 **설정 → 콘텐츠(DLC)**에서 내려받으면
팀 전원의 **새 문서** 창에 템플릿이 추가됩니다. 팀원은 인터넷 없이 LAN으로 받습니다.

팩에는 **데이터만** 들어갑니다(문서·시트·도식·무드보드 템플릿). 실행 코드는 넣지 않습니다.
허브는 `index.json`에 적힌 SHA-256과 크기가 맞을 때만 설치합니다.

## 템플릿 추가하기

1. `src/<팩 이름>/`에 파일을 넣습니다.

   | 파일 | 템플릿 |
   |---|---|
   | `이름.md` | 문서. 첫 줄에 `<!-- hint: 한 줄 설명 -->`을 쓰면 설명이 붙습니다 |
   | `이름.sheet.csv` | 기획용 시트. 첫 행은 머리글, `=C2/D2`처럼 `=`로 시작하면 수식. 설명은 `이름.sheet.hint` |
   | `이름.diagram.json` | 도식 (`"hint"` 필드에 설명) |
   | `이름.moodboard.json` | 무드보드 (`"hint"` 필드에 설명) |

2. 팩 정보는 `src/<팩>/pack.json`에 있습니다. 내용을 바꾸면 `version`을 올리세요.
3. 빌드하고 올립니다.

   ```bash
   python build.py
   git add -A && git commit -m "템플릿 추가" && git push
   ```

`packs/`와 `index.json`은 `build.py`가 만듭니다. 직접 고치지 마세요.
