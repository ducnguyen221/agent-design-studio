# Cách ra đề cho "xưởng thiết kế" — để nhận kết quả tốt nhất

Quy trình chỉ tốt ngang đầu vào bạn đưa. Trang này chỉ rõ cần nói gì, đưa gì,
và chuyện gì xảy ra ở hai điểm bạn ra quyết định.
🇬🇧 [English](GUIDE.md)

## Sáu đầu vào quyết định chất lượng

Đủ sáu thứ này, agent chạy trọn quy trình mượt mà. Thiếu thì nó sẽ dừng lại hỏi —
vẫn chạy được, nhưng tốn một vòng hỏi-đáp.

| # | Đầu vào | Vì sao quan trọng | Ví dụ |
| --- | --- | --- | --- |
| 1 | **Cái gì, cho ai** | Mọi thứ khác suy ra từ đây | "Landing page cho phần mềm đặt lịch, khách là chủ phòng khám" |
| 2 | **Một việc duy nhất** | Trang cố làm ba việc thì hỏng cả ba | "Khiến họ bấm đặt lịch demo" |
| 3 | **Nội dung thật** | Tiêu đề thật, con số thật mới sinh ra bố cục thật; chữ giả đẻ ra thiết kế giả | Dán nguyên văn nội dung, tên sản phẩm, giá, ảnh màn hình |
| 4 | **Thương hiệu — hoặc chưa có** | Có brand thì màu được *trích từ asset thật*, không bao giờ đoán. Chưa có thì nói rõ — agent suy palette từ chính chủ đề | File logo, link website, hoặc "chưa có brand" |
| 5 | **Nó sống ở đâu** | Trang độc lập và màn hình trong app là hai bài toán khác luật | "Một file HTML" vs "trong app React, repo đây" |
| 6 | **Nhanh hay kỹ** | Chốt-3-phương-án là mặc định. Bạn được quyền bỏ qua | "Cho tôi xem phương án" hoặc "khỏi phương án, làm luôn" |

## Mẫu prompt — chép, điền, gửi

**Trang mới**

> Thiết kế và dựng landing page cho **[sản phẩm]**, hướng tới **[đối tượng]**.
> Việc duy nhất trang phải làm được: **[hành động]**.
> Nội dung thật đây: **[dán chữ / đính kèm file]**.
> Thương hiệu: **[logo/link — hoặc "chưa có, tự suy"]**.
> Cho tôi xem 3 hướng trước khi dựng.

**Thiết kế lại**

> Thiết kế lại **[URL hoặc file]**. Giữ nội dung, nghĩ lại thiết kế.
> Điều tôi khó chịu hiện tại: **[liệt kê thẳng]**.
> Điều không được đụng: **[ràng buộc]**.
> Cho tôi xem 3 hướng trước khi dựng.

**Màn hình trong app thật**

> Thiết kế màn **[tên màn]** trong app (repo ở **[đường dẫn]**). Theo đúng stack và
> component sẵn có của dự án. Mục tiêu của người dùng ở màn này: **[mục tiêu]**.
> Các trạng thái quan trọng: **[đang tải / rỗng / lỗi / …]**.

## Đầu vào tốt trông thế nào

- **Chữ thật ăn đứt lorem ipsum.** Câu thô mà thật vẫn hơn.
- **Cho xem, đừng tả.** Một link trang bạn thích nói nhiều hơn năm tính từ.
  Agent sẽ kiểm chứng trang đó có thật rồi mổ xẻ vì sao nó hay.
- **Nói thẳng thứ bạn ghét.** "Không nền tối, không gradient to đùng" là đầu vào cực quý.
- **Ảnh màn hình sản phẩm của bạn** giúp UI thật xuất hiện trong thiết kế thay vì ô xám.

## Hai điểm bạn ra quyết định

**Chốt 1 — chọn hướng.** Bạn nhận ba phiên bản khác hẳn nhau, dựng thật, kèm ảnh.
Chọn theo *ý tưởng*, đừng chọn theo độ bóng — đánh bóng là việc của bước sau.
Nói cảm nhận bằng lời thường; "B, nhưng dịu lại" là câu trả lời hoàn hảo.
Phân vân? Cứ yêu cầu trộn, hoặc thêm một vòng nữa.

**Chốt 2 — nghiệm thu.** Bạn nhận bản hoàn thiện kèm báo cáo tự kiểm trung thực:
điểm số, đã sửa gì, còn gì và vì sao. Mọi thứ của lần chạy nằm gọn một thư mục —
có trang tình trạng viết cho người không đọc code, và một file cho mỗi bước.

## Tìm cảm hứng và mẫu ở đâu

- **Thư viện style có sẵn trong pack** — 40 style đặt tên sẵn cho trang web, slide,
  infographic (`references/direction-gate.md`). Agent rút từ đây khi sinh phương án.
- **Các giải thưởng thiết kế** — [Awwwards](https://www.awwwards.com),
  [CSS Design Awards](https://www.cssdesignawards.com), [FWA](https://thefwa.com),
  [Godly](https://godly.website) cho website; [Land-book](https://land-book.com) và
  [SaaS Landing Page](https://saaslandingpage.com) cho landing page;
  [Mobbin](https://mobbin.com) cho pattern UI ứng dụng.
- **Chính thế giới của chủ đề.** Hướng hay nhất thường đến từ đời thật của lĩnh vực —
  bao bì của hãng cà phê, giấy tờ của phòng khám, poster của lễ hội. Chỉ cho agent xem.
- **Một lần chạy hoàn chỉnh của chính quy trình này** — [`docs/example/`](docs/example/),
  công bố tại
  [ducnguyen.vn/agent-design-studio/example](https://ducnguyen.vn/agent-design-studio/example/).
  Hữu ích theo kiểu khác với gallery: nó cho thấy một bản brief, một quyết định chọn hướng
  và một báo cáo rà soát khi viết tử tế thì trông ra sao — để bạn hình dung được dáng của
  một câu trả lời tốt trước khi tự viết.

Chọn một-hai tham chiếu thôi, đừng mười. Đống link trộn lại thành nhờ nhờ;
một ví dụ bạn thật sự thích cho agent thứ để mổ xẻ.

## Lỗi thường gặp

1. **Tính từ thay cho nội dung.** "Hiện đại, sạch, chuyên nghiệp" tả được mọi trang
   trên đời. Nội dung thật + một tham chiếu ăn đứt mọi danh sách tính từ.
2. **Chọn ở Chốt 1 theo màu.** Màu đổi dễ; ý tưởng lõi thì không. Hãy chọn concept.
3. **Bỏ chốt cho nhanh, rồi làm lại hai lần.** Chốt tồn tại vì sửa sau khi dựng
   đắt hơn quyết định trước khi dựng.
4. **Không có đối tượng.** Thiết kế "cho tất cả mọi người" là cho không ai cả.
   Hãy gọi tên một con người cụ thể.
5. **Giấu tin xấu.** Ngân sách hạn hẹp, logo bắt buộc phải dùng, sếp ghét màu tím —
   agent thiết kế quanh được mọi ràng buộc mà nó biết trước.
