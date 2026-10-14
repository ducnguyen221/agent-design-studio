# ECOSYSTEM — Agent Design Studio trong hệ thống ACD

## 🤝 ACD Ecosystem Integration
- **Role in ACD:** Studio thuộc Nhóm 2 (Production Studio) — xưởng thiết kế UI/UX: quy trình bảy bước từ intake tới review, ba hướng thiết kế thật, hệ token và chuyển động. `agent-skill-studio` là xưởng nền cấp chuẩn `SKILL.md` portable, công cụ kiểm (`validate`/`audit`/`package`) và đóng gói skill; repo này tự giữ nghiệp vụ của mình, không nhờ xưởng nền viết thay.
- **Upstream Controllers:** `agent-agile-team` (mức Cốt lõi, UI/UX và token), repo marketing (landing, banner), `agent-academy-team` (giao diện chứng chỉ) và các Team khác khi cần ấn phẩm giao diện, giao việc qua repo điều phối.
- **Downstream Consumers:** `agent-slide-studio` nhận brand token và màu; `agent-video-studio` nhận tài sản và phong cách; `agent-data-studio` nhận quy tắc theme cho dashboard. Các Team nhận giao diện đã qua review.
- **Recommended Bundles:** Hiện chưa nằm trong Bundle A–E nào của bản đồ hệ thống; cài riêng được, và là mắt xích thiết kế khi một Bundle media cần thương hiệu nhất quán. Không thuộc Bundle E.
- **Handoff Artifacts:** Đầu vào là `production-brief.md` do Team giao. Đầu ra là các artifact của từng bước quy trình (brief, wireframe, ba hướng, hệ token, báo cáo review) và biên nhận nghiệm thu; hai bước dừng chờ người duyệt.
