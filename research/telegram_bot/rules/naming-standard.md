# Data naming standard (user 2026-08-01)

> All data fields **displayed·input·passed on screen/API**: names follow a **consistent naming standard**, apply to code vars·form `id`/`name`·DTO keys. (If a public standard vocabulary can be adopted, use it as baseline. e.g. a common dictionary like MOIS(행정안전부) 공통표준용어.)

## Principles
1. **논리명(Korean label) ↔ 물리명(EN abbrev) ↔ code var/field key** = 3-tier mapping managed as standard dictionary.
   - Standard 물리명 mostly defined UPPER_SNAKE (e.g. `USER_NM`, `RSVT_DE`).
   - **Code var·form id/name = 물리명 → camelCase**(e.g. `USER_NM`→`userNm`, `RSVT_DE`→`rsvtDe`).
   - Snake-convention codebases (Python etc) → snake_case (e.g. `user_nm`).
2. **Dictionary managed as in-project naming module**(e.g. web → `src/lib/naming.ts`, Python → separate const/schema module).
   - Columns: 한글라벨·표준약어·변환명·domain(type)·설명. Screen labels·fields reference this dict.
   - Keep rationale of adopted standard vocabulary(dict·mapping table) as project doc. (Reference if exists.)
3. **Form/input fields**: use standard converted name as-is. Validation schema(zod/pydantic etc) keys same.
4. **Data object keys**: mock·DTO·component props·API response field names also unified standard name (no dup·no arbitrary abbrev).
5. **Neologism not in standard**: combine nearest standard words; if none, register in dict as in-house standard extension then display.

## Application scope
- **All displayed·passed data**(list columns·detail·form input·search/filter keys·API fields) apply.
- New screens/modules: standard from start. Existing: gradual migration(on refactor).
- View column defs, form/validation schema, mock fields must use standard-dict keys.

## Verify
- Form id/name·code vars match standard-dict abbrev (review/lint). No arbitrary naming(e.g. `name1`, `email_addr`, `날짜`).

Rationale: adopt consistent data naming standard. If a public standard vocabulary(e.g. MOIS 공통표준용어) can be baseline, manage that dict as project doc.
User: "screen data column names follow standard, apply to var·form id/name".
