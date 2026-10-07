---
title: Design System index and ownership contract
status: template
---

# [Tên hệ thống] — Design System index

> Đầu ra đầu tiên luôn nằm trong run/output directory đã được giao, ở trạng thái proposal hoặc as-is. Không ghi template này vào thư mục Design System ổn định khi chưa có owner xác nhận và reviewer kiểm tra promotion. File phải cho người và agent biết baseline nào được mô tả, nguồn nào hiện là canonical, và ai có quyền xác nhận thay đổi.

## 1. Nhận diện hệ thống

| Trường bắt buộc | Giá trị |
|---|---|
| ID hệ thống | `[id ổn định]` |
| Tên / sản phẩm | `[tên]` |
| Project root đã khai | `[repo root được phép đọc]` |
| Run output directory | `[đường dẫn cụ thể đã được giao; proposal/as-is được ghi tại đây]` |
| Thư mục Design System mục tiêu | `[đường dẫn sản phẩm dự kiến; chỉ là đích promotion, không phải nơi ghi đầu tiên]` |
| Surface trong phạm vi | `[web / app / mobile / ...]` |
| Phiên bản hoặc baseline | `[version; hoặc branch + commit SHA]` |
| Trạng thái | `draft` / `pending` / `as-is` / `proposed` / `approved` / `deprecated` |
| Owner | `[vai trò hoặc tên đã được phép ghi]` |
| Reviewer | `[vai trò hoặc tên; chưa có thì unknown]` |
| Ngày cập nhật | `[YYYY-MM-DD]` |
| Run ID / hồ sơ evidence | `[ID và link artifact trong run output]` |

Trạng thái chỉ dùng các giá trị trong bảng. `approved` cần bằng chứng owner xác nhận và reviewer độc lập kiểm tra; khi thiếu một trong hai, giữ `pending` hoặc `proposed`. Bản extract mô tả hiện trạng dùng `as-is`; audit không promote canonical.

## 2. Thứ tự đọc

1. `DESIGN.md` — luật áp dụng cho agent/code và thứ tự ưu tiên nguồn.
2. Manifest và bảng nguồn chuẩn theo domain bên dưới.
3. Foundation hoặc component spec liên quan đến surface/task.
4. `provenance.md` và drift đang mở nếu quyết định phụ thuộc nguồn.

Nếu chưa có một mục, ghi `missing` hoặc `unknown`; không tạo file rỗng chỉ để lấp cây.

## 3. Nguồn chuẩn theo domain

Mỗi domain có đúng một nguồn canonical. Nếu sản phẩm đã có nguồn đang dùng, hãy trỏ tới nguồn đó thay vì sao chép giá trị sang bộ thứ hai.

| Domain | Kind (`file` / `repo-path` / `external`) | Canonical path or URL | Baseline/version | Status | Owner | Evidence / source trace |
|---|---|---|---|---|---|---|
| Brand identity | `[... ]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` | `[path:line, URL, hoặc run artifact]` |
| Tokens | `[... ]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` |
| Components | `[... ]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` |
| Patterns / templates | `[... ]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` |
| Surfaces / screens | `[... ]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` |
| Assets / fonts | `[... ]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` | `[... ]` |

Với nguồn local dùng `kind: file` hoặc `kind: repo-path` và khai `path` tương đối với project root. Nguồn Figma/external dùng `kind: external` và `url: https://...`; không đặt URL vào trường `path`. URL là con trỏ nguồn, không có nghĩa agent đã fetch hay kiểm nội dung.

### Quy tắc hòa giải

- Guideline thương hiệu đã được owner xác nhận mô tả hướng đích; source code tại baseline mô tả hiện trạng. Ghi cả hai khi khác nhau.
- Token, component, screenshot, README hoặc reference bất đồng thì tạo drift record có link tới từng nguồn và chờ owner quyết định. Không suy canonical từ số lần xuất hiện.
- `external` cần URL trực tiếp, trạng thái quyền xem/tái sử dụng và ngày kiểm tra. Quyền xem không có nghĩa là quyền sao chép hoặc phân phối.

## 4. Manifest điều hướng

Trong manifest, mọi trường `path` trỏ file đều tương đối với project root đã khai ở mục 1, không tương đối với thư mục Design System. Chỉ liệt kê file đã tồn tại trong baseline hoặc run output. Các nguồn external dùng `kind: external` và `url: https://...`.

| ID | Loại | Path (relative to project root) hoặc URL | Status | Surface | Owner | Source trace |
|---|---|---|---|---|---|---|
| `[id]` | `[foundation/component/pattern/template/screen/asset/preview]` | `[relative/path hoặc https://...]` | `[draft/pending/as-is/proposed/approved/deprecated]` | `[surface hoặc shared]` | `[owner hoặc unknown]` | `[path:line, Figma node, URL, hoặc run artifact]` |

Manifest máy đọc: `[đường dẫn manifest.json; nếu chưa có ghi missing]`. Manifest trỏ tới canonical; không chép lại token values vào đây.

Pattern/template/screen dùng checklist bắt buộc trong `references/system-contract.md`
của skill: task, information order/hierarchy, grid/breakpoints, data formatting,
loading/empty/error/permission, interaction, accessibility và component/pattern links.
Mỗi trường có evidence, hoặc `unknown`/`N/A` kèm lý do; template thêm regions/slots.

Ví dụ canonical Figma trong manifest: `{"kind":"external","url":"https://www.figma.com/design/..."}`. Ví dụ file trong manifest: `{"kind":"file","path":"design/<date>-<slug>/04-design-system/tokens.json"}`. URL/path phải là con trỏ tới nguồn hoặc artifact thật; không giả định đã truy cập nội dung.

## 5. Hợp đồng token

- Token source: `[đường dẫn canonical; hoặc chưa có]`.
- Format/schema và version: `[DTCG subset / CSS / TS / Figma / khác; chỉ ghi đã kiểm]`.
- Theme/surface: `[liệt kê hoặc unknown]`.
- Cách kiểm hoặc sinh output: `[lệnh/quy trình đã có; hoặc chưa thiết lập]`.

Nếu dùng DTCG subset của bộ công cụ này, chỉ nhận `$type`: `color`, `dimension`, `fontFamily`, `fontWeight`, `number`, `duration`; từng token phải có `$value`. Alias dùng `{path.to.token}`, trỏ tới token cùng file và cùng type. Shadow/easing hiện ghi ở documentation hoặc code kèm provenance; không khai là token được hỗ trợ trong subset này. Nếu project dùng CSS/TS/Figma làm canonical, giữ nguồn đó và chỉ ghi export là dẫn xuất.

## 6. Trạng thái và quyết định cần người

| ID | Quyết định / drift | Decision state (`pending` / `decided`) | Người quyết | Bằng chứng xác nhận | Reviewer / kết quả |
|---|---|---|---|---|---|
| `[id]` | `[mô tả ngắn]` | `[... ]` | `[owner hoặc unknown]` | `[run artifact/link; chưa có ghi pending]` | `[reviewer, ngày, kết luận hoặc pending]` |

Đầu ra đầu tiên vẫn ở run/output directory. Chỉ promotion sang thư mục Design System mục tiêu sau khi owner xác nhận nội dung và reviewer kiểm đường dẫn, source trace và nhất quán giữa các file liên quan. Ghi bản ghi xác nhận trong hồ sơ run; nếu chưa đủ bằng chứng, status vẫn là `pending` hoặc `proposed`.

## 7. Nguồn gốc và lịch sử

- Provenance ledger: `[đường dẫn provenance.md; hoặc missing]`.
- Change log: `[đường dẫn CHANGELOG.md; hoặc missing]`.
- Run gần nhất: `[đường dẫn]` — kết quả `[proposal / approved update / audit only]`.
- Giới hạn đã biết: `[unknown, unverified, phạm vi chưa khảo sát]`.

Trong provenance ledger, phân loại từng nhận định là `observed` (thấy trực tiếp), `inferred` (suy ra, ghi cơ sở) hoặc `unknown` (chưa có bằng chứng). Gắn source trace cụ thể như `path:line`, symbol, URL, Figma node hoặc run artifact; ghi quyền xem/tái sử dụng riêng cho asset. Không dùng reference làm căn cứ canonical nếu chưa có xác nhận của owner.
