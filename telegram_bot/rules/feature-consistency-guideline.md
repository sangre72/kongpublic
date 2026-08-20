# Feature Consistency · Per-Role Feature Matrix (MUST)

> Always applies as dev base guideline. With security guideline(if any) = **done condition**.

Applies to all feature work in this project(entry point·service·API·data access).

---

## 1. What feature consistency means

**All paths·roles handling the same business(entity) provide the same feature set symmetrically.**

| Symmetry axis | Meaning | Violation example |
|---------|------|---------|
| **CRUD symmetry** | Create's input·attachment also viewable·changeable in Update | attachment in create only, none in update |
| **Path symmetry** | multiple entry paths(screen·API etc.) same authz·same fields | API only authenticated, screen update has authz hole |
| **Role symmetry** | roles differ only in *allowed scope*, *feature structure* consistent | admin update form alone lacks attachment |
| **Representation symmetry** | list·detail·update same fields·naming | detail has attachment, update lists 0 |

**Forbidden**: remove whole feature block via a branch like `mode === 'edit'`. **Allowed**: edit differs only in *initial-value injection*·*delete UI*·*cap slot*.

---

## 2. Required rules (implementation)

### 2-1. Create ↔ Update parity
1. Write the create-form field list first (title·body·rating·secret·attachment·pin etc.).
2. Update form = **same list** base. Initial values = existing resource.
3. Attachment·related resource: update screen = **show existing list + delete + add(within cap)**; server = re-verify ownership/manage-permission then soft-delete·upload.
4. Using shared component/function → create/edit **one contract** — branch only on data·slots.

### 2-2. One-line check before done (required)
> **Can every field·attachment·related data made at create be viewed·changed on the update screen?** No → **no done**.

### 2-3. Authz consistency

| Layer | Rule |
|------|------|
| UI | button hide = UX. **not authz** |
| page/entry point | may redirect after session·role check |
| service · API · **data-access mutation** | check role·ownership via `viewer` arg. **no redirect**(fail via result object) |
| middleware/proxy | optimistic credential-existence check only |

Don't put `await requireRole()` in the data-access layer. Caller(service/API) injects session, data layer judges via `viewer.role`/`canManage*`.

### 2-4. Path consistency (multiple entry paths)
- Same business: same data access·same authz fn·same fields(same PII masking).
- Adding an entry path → no "screen-only work / API-only work". If no capacity, leave **unimplemented-symmetry list** in instruction Notes.

### 2-5. Verification scenario (≥1 applicable item before done)
- **Parity**: create(incl. attachment) → confirm list on update → delete 1·add 1 → reflected in detail.
- **Authz**(if roles exist): self allow / other deny / manage-permission allow(if per policy).
- **Unauthenticated**: 401 or login redirect(per path convention).

---

## 3. Per-role feature matrix (required output when working on a role-having project)

> If a role/permission concept exists, leave a **role × feature** table in new/extended feature instruction or PR/work result.
> For a single-run pipeline with no role distinction, this section may be skipped.

### 3-1. Table template (copy & fill)
> Role columns(`<역할1>`/`<역할2>`/…) are **placeholders** — replace with this project's actual roles.
```markdown
### 권한별 기능 일람 — <도메인명>

| 기능 ID | 기능 | <역할1> | <역할2> | … | <관리자> | 비고(소유권·등급) |
|---------|------|:-------:|:-------:|:-:|:--------:|-------------------|
| X-LIST  | 목록 조회 | △ | ✓ | ✓ | ✓ | … |
| X-READ  | 상세 | △ | ✓ | ✓ | ✓ | 비공개 항목: 작성자+관리자 |
| X-CREATE| 작성 | ✗ | ✓ | △ | ✓ | 공지=관리자 only |
| X-UPDATE| 수정 | ✗ | 본인 | 본인 | ✓ | 첨부 포함 |
| X-DELETE| 삭제(소프트) | ✗ | 본인 | 본인 | ✓ | 삭제 플래그 |
| X-ATTACH| 첨부 추가/삭제 | ✗ | 본인 | 본인 | ✓ | Create와 동일 상한 |
```
- ✓=allow, ✗=deny, △=conditional/partial, 본인=ownership required.
- **Manager role** = ✓ if policy allows managing all resources. If a scope-limited grade exists, note in 비고.
- UI hide & server deny must be **same result**(no button + server 403/error).

### 3-2. Role codes
> For a role-having project, fix actual defined role codes·entry points·detail grades in a table here. On implement, grade branching **only what's explicitly in the table**.

### 3-3. Feature ID naming
`{도메인약어}-{동사}` — e.g. `POST-CREATE`, `POST-ATTACH-DEL`, `JOB-ACCEPT`, `ADM-PIN`.

---

## 4. Checklist for instruction·done docs

Before start:
- [ ] Write create field list
- [ ] Confirm Update = same list + attachment parity
- [ ] (if roles) per-role feature matrix draft
- [ ] State ownership rule(`canManage*` / self / manager)

Before done:
- [ ] One-line parity check passed
- [ ] Double: UI hide + server re-verify
- [ ] self/other/manager(if applicable) scenario
- [ ] PII·internal identifier not exposed in response (security guideline)
- [ ] (if roles) final per-role feature matrix in work result/PR

---

## 5. Anti-patterns (real incidents)

| Anti-pattern | Result | Do instead |
|----------|------|------------|
| `{!isEdit && <업로드 />}` | update attachment hole | list+add+delete in edit too |
| implement only "CRUD security" from instruction | text-only update, attachment missing | field parity table required |
| `requireRole` redirect in data layer | token-based API returns HTML login | viewer check + return result |
| button-only hide | direct URL·API bypass | server re-verify |
| duplicate form/handler per role | admin-only feature missing | one contract + role arg |

---

## 6. Related docs
- Module structure: `.claude/rules/code-structure.md`
- Security guideline(if any): `.claude/rules/security-guideline.md`

Basis: user "make feature-dev consistency·per-role feature matrix a dev base guideline".
