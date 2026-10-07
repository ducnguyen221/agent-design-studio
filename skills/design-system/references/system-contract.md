# Hợp đồng hệ thống và nguồn chuẩn

DS ổn định thuộc project. Run thuộc `design/<date>-<slug>/` hoặc output directory
được giao. Mọi draft/as-is/delta ở run trước; existing canonical không bị đổi bởi
extract/audit. Promotion có owner decision và reviewer evidence, không suy từ im lặng.

## Cây trách nhiệm

- README: tổng quan người dùng, surface, version, link tới mục/specimen.
- DESIGN: contract ngắn cho agent, source authority theo domain, thứ tự đọc.
- manifest.json: index ID/path/status/version; không chứa bản sao token.
- provenance: nguồn/rights, owner decisions, keep/change/reject và drift hai phía.
- CHANGELOG: thay đổi ảnh hưởng visual/API/token và migration.
- brand: identity, voice-content; logo/imagery chỉ khi có dữ liệu/quyền.
- foundations: colors, typography, spacing-layout, radius, elevation, motion,
  accessibility; giá trị trỏ canonical, không nhập lại giá trị song song.
- tokens: naming/source/theme/alias, JSON/CSS khi thực sự sở hữu nguồn hoặc export.
- components: index và group/Component/spec.md, usage.prompt.md; code/d.ts/preview
  chỉ khi package sở hữu, nếu product sở hữu thì link tới source/story.
- patterns: cấu trúc/data/state tái dùng; templates: vùng/slot/compose/preview.
- surfaces: rules từng surface và screen ổn định được duyệt; draft ở run.
- ui-kit: link Figma/code/story/demo có thể lắp/sửa; không gắn nhãn kit cho Markdown.
- assets: manifest quyền và binary hợp scope; specimens: preview dùng source thật.
- integrations: hướng dẫn export/adaptor khi có nhu cầu; ZIP/dist/bundle là snapshot.

Chỉ materialize nhánh có đối tượng thực. READMEs/index không lặp token/API. Một domain
một canonical; không yêu cầu chuyển CSS/TS/Figma source sang JSON.

## Checklist bắt buộc cho pattern, template và screen spec

Mỗi spec có: nhiệm vụ người dùng; thứ tự thông tin và phân cấp; grid, chiều rộng và
breakpoints; định dạng dữ liệu (số/ngày/đơn vị/copy); loading/empty/error/permission;
tương tác/trigger/recovery; accessibility/keyboard/focus; link component và pattern
được dùng. Template còn khai vùng/slot và cách compose. Ghi source/evidence cho
từng trường; chưa biết ghi `unknown` cùng cách kiểm. Trường không áp dụng ghi
`N/A` cùng lý do, không bỏ trống hoặc suy state từ kỳ vọng. Giá trị source là
declared; behavior/computed chưa đo giữ unverified. Screen draft ở run; chỉ screen
được duyệt và cần duy trì mới được promotion vào surfaces.

## Manifest subset v1

`schemaVersion: "1"`, `system: {id,version,status}`, `canonical` map theo domain.
Mỗi source local có `kind: file|repo-path`, `path` relative với **project root được khai**.
Nguồn Figma/Storybook hoặc hệ external hiện hữu có `kind: external`, `url: https://...`,
không có `path`. URL chỉ là pointer; verifier không fetch, không chứng minh availability,
quyền dùng hoặc nội dung. Chặn URL có credentials hoặc syntax không hợp lệ. Không đưa
signed/private URL hay nội dung riêng vào package public. Khai owner, rights và ngày
kiểm thực trong provenance; nguồn chưa xem vẫn ghi unverified. Source local không có
`url`; không dùng URL thay đường file.
Các path doc/usage/preview/rules cũng relative với project root; không trộn relative
DS root. Index có thể thêm sections/components/surfaces/assets với ID duy nhất trong
mỗi collection. Status: draft/pending/as-is/proposed/approved/deprecated. Owner và
baseline được khai trong contract/provenance; source chưa biết nằm decisions pending.
Manifest draft chưa đủ canonical map phải ghi partial, không bịa đường.

## Authority và drift

Brand guideline/owner được xác nhận mô tả hướng đích; code/CSS tại baseline mô tả
hiện trạng. Token và component sources được khai theo domain. README, export và ảnh
không mặc nhiên thắng code, cũng không mặc nhiên thua ý định owner. Drift record:
domain → source A/evidence → source B/evidence → impact → proposal → owner decision
pending/quote → reviewer evidence. Không chọn giá trị phổ biến nhất làm chuẩn.

Promotion checklist: phạm vi được giao, owner chốt thay đổi, reviewer kiểm source/link/
consistency, tests/runtime phù hợp có evidence, migration/rollback; UI build cần ship
gate. Promotion xong cập nhật version/status/path khi thực sự đổi, không tự release.
