---
title: Design System audit and extraction report
status: template
---

# [Tên sản phẩm] — Design System [audit / extract] report

> Báo cáo này mô tả phạm vi đã kiểm, evidence và khoảng trống. `audit` là read-only. `extract` tạo proposal/as-is trong output directory của run. Không cập nhật canonical, đổi trạng thái approved hoặc biến inferred thành quyết định thương hiệu trong báo cáo này.

## 1. Run và phạm vi

| Trường bắt buộc | Giá trị |
|---|---|
| Mode | `audit` / `extract` |
| Run ID / ngày | `[id]` / `[YYYY-MM-DD]` |
| Run output directory | `[đường dẫn cụ thể; artifacts của lượt này nằm tại đây]` |
| Project root | `[đường dẫn repo đã được phép đọc]` |
| Baseline | `[branch + commit SHA; dirty/clean]` |
| Surface / sản phẩm | `[... ]` |
| Phạm vi đường dẫn được đọc | `[thư mục/file allowlist]` |
| Đường dẫn loại trừ | `[secret, env, credentials, generated/vendor/build, symlink ngoài phạm vi...]` |
| Framework / entrypoint | `[chỉ ghi đã quan sát; nếu chưa xác định ghi unknown]` |
| DS canonical hiện hữu | `[path/version/status; hoặc none found within scope]` |
| Owner / reviewer | `[vai trò/người hoặc unknown; reviewer chưa làm ghi pending]` |
| Output status | `proposal` / `audit-only` / `blocked` / `unverified` |

### Câu hỏi và điều kiện dừng

- Câu hỏi owner còn mở: `[câu hỏi + người cần quyết + status pending]`.
- Có thể tiếp tục phần chỉ đọc độc lập không? `[yes/no; lý do]`.
- Điều gì bị chặn khi thiếu trả lời? `[... ]`.

## 2. Phương pháp và coverage

Chỉ liệt kê thao tác đã thực hiện. Không ghi “đã kiểm toàn bộ” nếu chưa xác định mẫu số.

| Area | In-scope denominator | Examined numerator | Coverage | Method / locations | Limitations |
|---|---:|---:|---:|---|---|
| Token sources | `[N]` | `[n]` | `[n/N hoặc unknown]` | `[... ]` | `[... ]` |
| Components / exports | `[N]` | `[n]` | `[... ]` | `[... ]` | `[... ]` |
| Routes / screens | `[N]` | `[n]` | `[... ]` | `[... ]` | `[... ]` |
| Stories / tests | `[N]` | `[n]` | `[... ]` | `[... ]` | `[... ]` |
| Themes / assets | `[N]` | `[n]` | `[... ]` | `[... ]` | `[... ]` |

Browser/render checks: `[not run / unverified / run]`; môi trường, route, viewport, theme và timestamp: `[... ]`. Không có browser thì claim runtime/computed giữ `unverified`.

## 3. Evidence inventory

Mỗi dòng là một claim nhỏ và có source trace. Dùng `observed`, `inferred`, `unknown`; ghi riêng `declared` (khai trong file) và `computed` (đo từ rendered runtime) khi nói về giá trị style.

| ID | Claim / phát hiện | Class (`observed` / `inferred` / `unknown`) | Kind (`declared` / `computed` / `behavior` / `rights`) | Source (`path:line`, symbol, URL, Figma node) | Baseline / viewport | Confidence / limitation |
|---|---|---|---|---|---|---|
| `[E-01]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` |

Comment, README, token name hoặc screenshot là evidence có giới hạn; chúng không tự chứng minh intent, quyền sử dụng, runtime behavior hay giá trị computed. Không chạy script/package của repo chỉ để suy phong cách.

## 4. Canonical map và drift

| Domain | Canonical source hiện hữu | Baseline/version | Claim được nguồn này chứng minh | Status/owner | Drift hoặc khoảng trống |
|---|---|---|---|---|---|
| Brand intent | `[path/URL hoặc unknown]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` |
| Tokens | `[path/URL hoặc none]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` |
| Components | `[path/URL hoặc none]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` |
| Patterns/surfaces | `[path/URL hoặc none]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` |
| Assets/fonts | `[path/URL hoặc none]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` |

| Drift ID | Nguồn A + evidence | Nguồn B + evidence | As-is / to-be distinction | Impact | Owner decision | Status |
|---|---|---|---|---|---|---|
| `[D-01]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` | `[owner + pending/decision link]` | `[open/decided]` |

Code tại baseline mô tả as-is; guideline đã owner-approve mô tả to-be. Nếu khác nhau, ghi hai phía và để quyết định cho owner. Không tự tạo canonical token/component source thứ hai.

## 5. Token audit

| Token / selector | Declared value + type | Source (`path:line`) | Consumers | Computed value / render evidence | Class/status |
|---|---|---|---|---|---|
| `[... ]` | `[... ]` | `[... ]` | `[... ]` | `[unverified hoặc bằng chứng đo]` | `[observed/inferred/unknown]` |

Nếu kiểm theo DTCG subset: `$type` chỉ gồm `color`, `dimension`, `fontFamily`, `fontWeight`, `number`, `duration`; token cần `$value`; alias `{path.to.token}` phải trỏ token cùng file/cùng type. Báo target thiếu, type mismatch và alias cycle rõ ràng. Shadow/easing là composite chưa hỗ trợ trong subset: ghi ở doc/code với source trace, không ép thành DTCG token và không xuất CSS từ giá trị đoán.

- Validator/schema/version đã dùng: `[...; nếu chưa chạy ghi not run]`.
- Kết quả: `[pass/fail/unverified/not applicable]`.
- Giới hạn: `[subset không chứng nhận tuân thủ toàn chuẩn DTCG]`.

## 6. Component, route và state inventory

| ID | Component/surface | Implementation trace | Variants/states thấy được | Consumer route/story | Status | Missing evidence |
|---|---|---|---|---|---|---|
| `[... ]` | `[... ]` | `[path:line/symbol hoặc missing]` | `[... ]` | `[... ]` | `[observed/inferred/unknown]` | `[... ]` |

Các state runtime chưa quan sát được ghi `unknown`/`unverified`, không điền từ kỳ vọng. Shared component cần spec riêng; report này chỉ inventory và trỏ nguồn.

## 7. Quyền tài sản

| Asset/font/reference | Origin URL/path | Right to view | Right to reuse/distribute | Scope/conditions | Checked date / evidence | Status |
|---|---|---|---|---|---|---|
| `[... ]` | `[... ]` | `[yes/no/unknown]` | `[yes/no/unknown]` | `[... ]` | `[... ]` | `[... ]` |

Quyền xem không suy ra quyền sao chép hoặc đưa vào package public. Không đóng gói asset khi trạng thái quyền là `unknown`.

## 8. Kết luận và handoff

- **Đã xác minh:** `[claim + evidence IDs]`.
- **Suy luận cần xác nhận:** `[claim + cơ sở + owner]`.
- **Chưa biết / chưa kiểm:** `[câu hỏi hoặc phép kiểm còn thiếu]`.
- **Đề xuất delta:** `[file đích dự kiến trong run output; hoặc none]`.
- **Canonical thay đổi:** `no` trong mode audit/extract.
- **Owner decisions pending:** `[danh sách IDs; nếu không có ghi none]`.
- **Reviewer record:** `[reviewer, ngày, kết luận, đường dẫn run artifact; nếu chưa review ghi pending]`.
- **Điều kiện promotion:** `[owner approval + independent reviewer check + source/link consistency evidence]`.

### Tóm tắt coverage

`[n] / [N]` mục trong phạm vi đã khảo sát (`[percent hoặc not computed]`). Mẫu số là `[định nghĩa in-scope]`; loại trừ `[... ]`. Kết quả không đại diện cho phần ngoài phạm vi.
