---
title: Reusable component specification
status: template
---

# [Tên component] — specification

> Một component spec mô tả hợp đồng dùng chung; nó không tự tạo code, Figma kit hoặc UI kit. Đường dẫn implementation, story, test và Figma phải trỏ tới nguồn thật. Phần suy luận và phần chưa kiểm cần được gắn nhãn riêng.

## 1. Định danh và trạng thái

| Trường bắt buộc | Giá trị |
|---|---|
| Component ID | `[id ổn định, chữ thường]` |
| Tên / nhóm | `[Tên / nhóm]` |
| Mục đích | `[công việc người dùng hoàn thành]` |
| Surface | `[shared hoặc danh sách surface]` |
| Status | `draft` / `pending` / `as-is` / `proposed` / `approved` / `deprecated` |
| Phiên bản / baseline | `[version hoặc branch + commit SHA]` |
| Owner | `[vai trò/người; hoặc unknown]` |
| Reviewer | `[vai trò/người; hoặc unknown]` |
| Project root đã khai | `[repo root được phép đọc]` |
| Run output directory | `[đường dẫn tới hồ sơ run chứa evidence/đề xuất]` |
| Run / hồ sơ nguồn | `[ID hoặc link tới artifact cụ thể trong run]` |
| Canonical spec hiện hữu | `[relative path từ project root; hoặc none]` |
| Spec proposal trong run | `[relative path từ project root tới file này]` |
| Implementation | `[relative path từ project root + symbol/export; hoặc missing/unverified]` |
| Story / test / preview | `[relative path từ project root; hoặc missing]` |
| Figma / external | `[URL https://...; manifest kind: external; hoặc not available]` |

Mọi path trong manifest tương đối với project root được khai ở run, không tương đối với thư mục Design System. Status chỉ dùng enum trong bảng; `approved` cần bằng chứng owner xác nhận và reviewer độc lập kiểm tra. Nếu chỉ có README, tên component hoặc ảnh chụp, giữ implementation ở `unverified`. Spec mới là proposal trong run, không ghi thẳng vào canonical path.

## 2. Evidence và provenance

Gắn mỗi claim với một trong ba nhãn. Đường dẫn source code ghi dạng `path:line` hoặc `path#symbol`; không ghi giá trị secret hay nội dung file nhạy cảm.

| Claim | Evidence class (`observed` / `inferred` / `unknown`) | Source (`path:line`, symbol, story, URL, Figma node, run artifact) | Baseline/ngày | Confidence hoặc giới hạn |
|---|---|---|---|---|
| `[claim cụ thể]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` |

- **Observed:** thấy trực tiếp trong code, tài liệu, rendered state hoặc nguồn đã nêu.
- **Inferred:** kết luận suy ra từ evidence; ghi lý do và cần owner xác nhận nếu ảnh hưởng intent.
- **Unknown:** chưa có evidence hoặc không kiểm được; ghi bước/câu hỏi cần để đóng.

Ảnh tĩnh không chứng minh DOM, font thực, behavior, responsive, thời điểm motion hay quyền sử dụng. Khai báo token trong source là `declared`; chỉ ghi `computed` khi đã đo trên build/render, kèm viewport, theme và evidence.

## 3. Quy tắc dùng

- **Dùng khi:** `[job / điều kiện cụ thể]`
- **Không dùng khi:** `[trường hợp gần giống nhưng cần component khác]`
- **Nội dung và accessibility:** `[label, accessible name, semantics, validation/copy]`
- **Token mapping:** `[token ID → vai trò; link canonical token source]`
- **Dependencies / composed components:** `[ID + spec links hoặc none]`

Chỉ tham chiếu token đã có trong canonical source; ghi token ID và link, không tự khai giá trị mới ở component spec. Nếu hệ dùng DTCG subset, tuân theo `token-contract.md`; shadow/easing chưa được hỗ trợ như token trong subset đó, nên ghi chúng ở docs/code với provenance thay vì thêm token giả.

## 4. Anatomy và variants

| Part / variant | Vai trò | Required? | Token / slot / API | Evidence |
|---|---|---|---|---|
| `[anatomy part]` | `[vai trò]` | `[yes/no/conditional]` | `[canonical token/API hoặc unknown]` | `[path:line/story/spec]` |

| Variant | Khi dùng | Khác biệt quan sát được | Canonical prop/token | Evidence class |
|---|---|---|---|---|
| `[variant]` | `[... ]` | `[... ]` | `[... ]` | `[observed/inferred/unknown]` |

## 5. API / props

| Prop / slot / event | Type | Default | Behavior | Required/optional | Source (`path:line` hoặc symbol) |
|---|---|---|---|---|---|
| `[name]` | `[type]` | `[value/none/unknown]` | `[behavior]` | `[... ]` | `[... ]` |

Chỉ ghi API hiện có khi có implementation evidence. API đề xuất phải ghi `candidate` và không trộn vào API đang chạy.

## 6. States và behavior

| State | Trigger | Visual/content result | Interaction / recovery | Keyboard / assistive tech | Evidence / status |
|---|---|---|---|---|---|
| Default | `[... ]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` |
| Hover | `[... ]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` |
| Focus-visible | `[... ]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` |
| Active/pressed | `[... ]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` |
| Disabled | `[... ]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` |
| Loading | `[nếu áp dụng; nếu không ghi n/a + lý do]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` |
| Error/validation | `[nếu áp dụng]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` |

Khai rõ state nào không áp dụng. Không để ô trống vì ô trống không phân biệt “không có” với “chưa kiểm”.

## 7. Responsive và accessibility

- Breakpoints / layout changes: `[breakpoint + behavior + source; hoặc unknown]`.
- Keyboard operation: `[phím, thứ tự focus, focus return; hoặc unverified]`.
- Semantics / ARIA: `[role/name/state; lý do cho mọi ARIA bổ sung]`.
- Contrast / target size / zoom / text resize: `[đoạn kiểm + evidence; hoặc unverified]`.
- Reduced motion: `[behavior khi bật; hoặc not applicable + lý do]`.

## 8. Ví dụ và quyết định chưa chốt

- **Do:** `[mẫu đúng + link preview/story]`
- **Avoid:** `[mẫu sai + lý do]`
- **Unknown / cần owner:** `[câu hỏi nhận diện hoặc hành vi; owner; trạng thái pending]`
- **Reviewer record:** `[người/ vai trò, ngày, kết luận, link run artifact; chưa kiểm ghi pending]`

## 9. Migration / deprecation (khi cập nhật component hiện hữu)

| Từ phiên bản | Thay đổi | Breaking? | Cách chuyển | Owner decision | Reviewer |
|---|---|---|---|---|---|
| `[version hoặc n/a]` | `[... ]` | `[yes/no/unknown]` | `[... ]` | `[link hoặc pending]` | `[link hoặc pending]` |
