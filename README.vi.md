# agent-design-studio

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Agent của bạn đã biết viết UI. Đây là thứ dạy nó thiết kế.**

Quy trình thiết kế UI bảy bước để một AI coding agent chạy từ đầu đến cuối — tiếp nhận,
chọn mức hoàn thiện, wireframe, ba hướng thiết kế thật, hệ token, chuyển động, rà soát.
Một skill Design System riêng tạo, trích xuất, audit và mở rộng hệ thống do sản phẩm sở
hữu. Cả hai đều để lại hiện vật có đường lần ngược; quy trình UI giữ hai cổng quyết định
của con người.

🔗 **[ducnguyen221.github.io/agent-design-studio](https://ducnguyen221.github.io/agent-design-studio)** ·
🇬🇧 **[English](README.md)**

---

## Vì sao có nó

Bảo agent làm một trang landing, bạn nhận được đúng thứ đầu tiên nó nghĩ ra, trong đúng ba
kiểu nó làm cho tất cả mọi người. Không phải vì mô hình thiếu gu — mà vì không có gì trong
yêu cầu buộc nó phải *chọn*. Không brief, không phương án để loại bỏ, không sàn chất lượng
để vượt, và không ai rà soát.

Bộ này cung cấp cả bốn qua hai skill. `design-routing` là quy trình UI; mười sáu tài liệu
tham chiếu của nó mang phần nghề thật sự — thứ tự ra quyết định, các ngưỡng cụ thể, giá
trị đường cong, phép tính màu, và cả những phần bảo agent dừng lại. `design-system` phụ
trách công việc hệ thống có thể dùng lại giữa các sản phẩm và codebase.

**Mỗi năng lực là một "slot".** Nếu máy bạn đã có công cụ mạnh hơn cho một bước, router sẽ
dùng nó; nếu không, playbook có sẵn sẽ chạy. Hai skill có phạm vi riêng: router xử lý việc
dựng UI hoặc chỉ phân tích reference; skill Design System xử lý hệ thống dùng lâu dài.

## Bảy bước

| Bước | Làm gì | Hiện vật |
| --- | --- | --- |
| **0** Chế độ đích | Sản phẩm tĩnh độc lập, hay một màn hình trong codebase thật. Điều này đổi nghĩa của chữ "xong" | — |
| **1** Tiếp nhận | Chủ thể, người dùng, và việc duy nhất màn hình này phải làm. Đọc thứ đã có trước đã | `00-brief.md` |
| **2** Mức hoàn thiện | Cần hoàn thiện tới đâu — quyết định thiết kế đầu tiên | `01-fidelity.md` |
| **3** Wireframe | Chỉ cấu trúc, cố ý trông chưa xong. Khai báo trạng thái, viewport và luồng bàn phím ngay tại đây | `02-wireframe.html` + `.png` |
| **4** Hướng thiết kế — **CỔNG** | Ba bản dựng khác nhau thật sự, mỗi bản có tối đa hai giả thuyết chuyển động bằng keyframe tĩnh | `03-directions/{a,b,c}` + `03-direction-decision.md` |
| **5** Hệ thiết kế + code | Màu lấy mẫu từ tài sản thật; dựng và kiểm bản tĩnh trước khi thêm chuyển động | `04-design-system/` + `05-implementation.md` |
| **6** Chuyển động | So từng giả thuyết với bốn cổng, chọn recipe theo mục đích hoặc từ chối | `06-motion-spec.md` |
| **7** Rà soát — **CỔNG** | Chấm trên sáu chiều so với sàn cứng. Sửa từng commit một, rồi kiểm lại | `07-uat-report.md` |

Tất cả nằm trong `<dự-án>/design/<ngày>-<slug>/`.

### Khác gì so với việc viết prompt

- **Ba hướng, dựng ra thật.** Không phải ba tính từ để chọn. Ba trang được render thật, tạo
  ra bởi ba logic cố ý không tương thích nhau để chúng không thể hội tụ, chụp màn hình rồi
  đặt cạnh nhau. Sau đó quy trình *dừng lại* — chọn hướng nào là quyền của bạn.
- **Màu được suy ra, không bịa.** Lấy mẫu từ tài sản thương hiệu, ảnh thật, hoặc từ chính
  thế giới của chủ đề; hội tụ trong không gian màu đều theo cảm nhận; và giải thích bằng
  một câu. Viết không nổi câu đó nghĩa là bạn đang chép công thức.
- **Chuyển động phải tự giành lấy chỗ đứng.** Bốn cổng — tần suất, mục đích, tốc độ, chức
  năng. Kết quả bao gồm cả những gì bị *từ chối* và vì sao. Ở hầu hết giao diện, danh sách
  đó dài hơn danh sách được chấp nhận.
- **Một sàn chất lượng không hạ.** Chữ nội dung ≥14px, nhãn ≥12px, tương phản ≥4.5:1, focus
  nhìn thấy được, thao tác đầy đủ bằng bàn phím, tôn trọng reduced-motion, và mọi trạng
  thái UI được khai báo ngay từ wireframe — không phải phát hiện lúc rà soát.
- **Hai cổng mà chế độ tự động không thể lặng lẽ bỏ qua.** Mỗi cổng là một file ở một trong
  ba trạng thái: `pending`, `human-approved`, hoặc `policy-auto-selected`. Một lần chạy
  không người trực hoặc là có quyền được cấp và phải ghi rõ lý do, hoặc là dừng lại và nói
  ra điều đó.

## STATUS.md — trang dành cho tất cả những người còn lại

Mỗi lần chạy đều duy trì một bảng theo dõi một trang: bước nào xong, bước nào đang chờ, chờ
ai, và đường dẫn tới mọi hiện vật. Viết cho người trả tiền chứ không phải người làm, để
không ai phải hỏi tiến độ.

## Cài đặt

**Claude Code**

```
/plugin marketplace add ducnguyen221/agent-design-studio
/plugin install agent-design-studio
```

**Codex**

```
codex plugin marketplace add ducnguyen221/agent-design-studio
codex plugin add agent-design-studio@agent-design-studio
```

**Bất kỳ agent nào đọc được `SKILL.md`**

```bash
git clone https://github.com/ducnguyen221/agent-design-studio
cp -r agent-design-studio/skills/design-routing ~/.agents/skills/
cp -r agent-design-studio/skills/design-system ~/.agents/skills/
```

Không phụ thuộc gói thư viện nào, không cần bước build. Trình duyệt mới là thứ biến bản
dựng thành bản đã được kiểm chứng — không có nó, các mục kiểm tra thị giác nằm ở
`unverified` và các cổng nằm ở `pending`. Quy trình có chủ đích gọi mạng ở hai chỗ: xác
minh một sản phẩm hay ví dụ tham chiếu có thật, và tải tài sản thương hiệu thật thay vì
đoán.

## Dùng thế nào

**→ [GUIDE.vi.md](GUIDE.vi.md) — cách ra đề cho tốt**: sáu đầu vào quyết định
chất lượng, mẫu prompt điền-vào-chỗ-trống, nói gì ở hai điểm chốt, và tìm cảm hứng
ở đâu. Năm phút đọc đổi lấy chất lượng của mọi thứ nó dựng cho bạn.

Khi chọn chữ cho giao diện Anh–Việt, xem
[tài liệu typography](skills/design-routing/references/typography-en-vi.md):
font theo từng việc, cỡ chữ khởi đầu và cách kiểm dấu, tải font, tăng cỡ chữ.

Khi cần mẫu UI/UX bên ngoài, xem link trong brief trước rồi mở
[chỉ mục nguồn](skills/design-routing/references/resource-index.md). Chỉ mục trỏ đến
[catalog JSON 75 nguồn](skills/design-routing/resources/uiux-catalog.json); lọc theo việc,
đưa hai hoặc ba nguồn phù hợp, chỉ mở mẫu cụ thể khi cần, rồi cùng người dùng chốt hướng
ở Bước 4. Catalog chỉ để mở link: trang đầu không chứng minh demo đã quan sát, runtime
đã chạy hay quyền dùng lại mã và asset. Có thể lọc local bằng
`python scripts/verify-resource-pack.py --query "loading" --stack React`; `--self-test`
kiểm pack mà không truy cập website.

Nếu chỉ cần phân tích ảnh UI, link hoặc nội dung mẫu trước khi dựng giao diện, dùng
[hướng dẫn distill reference](skills/design-routing/references/reference-distill.md)
và [mẫu Markdown](skills/design-routing/templates/reference-design.md). File kết quả
tách điều đã quan sát, suy luận và phần chưa biết; lựa chọn của bạn trở thành đầu vào
cho quy trình thiết kế. Phân tích riêng không khởi động cổng duyệt bản render.

Khi cần Design System dùng lại cho một sản phẩm, gọi thẳng `design-system`. Skill có bốn
mode: `create` từ reference hoặc tài liệu thương hiệu đã chọn, `extract` từ codebase,
`audit` hệ thống hiện có so với implementation, và `extend` hệ thống đã được duyệt.
Kết quả ban đầu là proposal/report trong thư mục của lượt chạy; nguồn canonical hiện hữu
giữ nguyên thẩm quyền cho tới khi owner xác nhận promotion và reviewer kiểm tra.

Luồng nối reference với hệ thống: cùng người dùng chọn mẫu trước, distill bằng hướng dẫn
và [template reference](skills/design-routing/templates/reference-design.md), rồi chuyển
source ID, nhận định observed/inferred/unknown, trạng thái quyền và câu hỏi cho owner sang
`design-system`. Shortlist hoặc bản distill không tự duyệt nhận diện thương hiệu. Xem
[system contract](skills/design-system/references/system-contract.md) để biết cấu trúc hệ
thống do sản phẩm sở hữu; bắt đầu với [design index](skills/design-system/templates/design-index.md),
rồi dùng [component spec](skills/design-system/templates/component-spec.md) và
[audit report](skills/design-system/templates/audit-report.md) khi phù hợp.

Với yêu cầu làm nguyên một giao diện, nó thường tự kích hoạt:

> "Làm cho tôi một trang landing cho công cụ đặt lịch."
> "Thiết kế lại cổng khách hàng — trông cũ quá rồi."
> "Thiết kế màn hình onboarding trong app React của bọn mình, brief đây."

Khi trong máy có nhiều skill thiết kế, gọi thẳng `design-routing` là đường chắc chắn nhất.

Nó cố ý đứng ngoài các việc lẻ một bước khác — phê bình một trang có sẵn, chuyển một thiết kế đã
duyệt thành HTML, chọn bảng màu, vẽ biểu đồ, hay chỉnh bố cục một bộ slide đã có. Những
việc đó có công cụ phù hợp hơn, và quy trình này sẽ là quá nặng. Thiết kế mới một bộ slide,
một báo cáo hay một infographic như nguyên một sản phẩm thì lại khác: việc đó nằm trong
phạm vi, và chạy ở chế độ static-artifact.

## Bên trong có gì

```
skills/design-routing/
├── SKILL.md                    router: chế độ, slot, các bước, cổng duyệt, sàn chất lượng
└── references/
    ├── ownership-matrix.md     mỗi năng lực đúng một chủ, và bước tiếp nhận
    ├── choosing-fidelity.md    wireframe / mockup / prototype / production
    ├── wireframe-playbook.md   chỉ cấu trúc, và hợp đồng trạng thái + viewport
    ├── prototype-playbook.md   mô hình hoá hành vi thật và trạng thái thật
    ├── direction-gate.md       ba logic chống hội tụ + thư viện 40 phong cách
    ├── brand-asset-protocol.md tìm logo và tài sản thật thay vì đoán
    ├── image-sourcing.md       ảnh là nội dung hay trang trí, và chứng minh nguồn từng tấm
    ├── color-protocol.md       lấy mẫu → hội tụ → lập luận, kèm bảng chroma
    ├── taste-calibration.md    các lối mòn cần né, và chữ nghĩa là vật liệu thiết kế
    ├── typography-en-vi.md     chọn font theo việc, thang chữ và kiểm tra EN/VI
    ├── motion-playbook.md      trọn vòng đời chuyển động, và những gì phải từ chối
    ├── motion-patterns.md      sáu recipe theo mục đích, có fallback và reduced motion
    ├── resource-index.md       shortlist nguồn theo việc; catalog chỉ nạp khi cần
    ├── reference-distill.md    chắt mẫu được cung cấp thành Markdown thiết kế
    ├── library-selection.md    chọn thư viện, hoặc không thêm thư viện nào
    └── uat-report-schema.md    bản rà soát có chấm điểm và sàn cứng
└── templates/
    ├── 06-motion-spec.md        mẫu quyết định motion có đường lần ngược
    ├── static-motion-demo.html  ví dụ CSS/WAAPI tự viết
    ├── react-motion-demo.tsx    ví dụ React tự viết, không thêm gói motion
    └── reference-design.md      mẫu một file để phân tích reference
```

```
skills/design-system/
├── SKILL.md                    router cho create / extract / audit / extend
├── references/
│   ├── system-contract.md      nguồn chuẩn, vòng đời và điều kiện promotion
│   ├── source-code-audit.md    bằng chứng và coverage khi đọc source
│   └── token-contract.md       subset token hỗ trợ và luật giữ nguồn hiện hữu
└── templates/
    ├── design-index.md         điểm vào hệ thống, nguồn chuẩn và owner
    ├── component-spec.md       hợp đồng component dùng lại
    └── audit-report.md         evidence, coverage và drift theo lượt chạy
```

`design-routing` giữ nguyên mười sáu tài liệu tham chiếu và phạm vi dựng UI/phân tích
reference. `design-system` là điểm vào riêng cho hệ thống tái dùng do sản phẩm sở hữu.
Mỗi skill chỉ nạp tài liệu cần cho việc hiện tại để context luôn gọn.

## Kiểm hợp đồng Design System

Từ repo này, chạy `python scripts/verify-design-system.py --self-test` để kiểm các
case hợp đồng, hoặc `python scripts/verify-design-system.py` để kiểm skill pack.
Với index của sản phẩm, dùng `--root <project> --manifest <relative-manifest.json>`;
mọi path trong manifest tính từ project root ấy. `--tokens <relative.json>` kiểm
DTCG subset được hỗ trợ; `--legacy-tokens <relative.json>` chỉ kiểm map legacy.
Các check không fetch con trỏ external hoặc tạo CSS. Kết quả cấu trúc đạt chưa
chứng minh render, coverage source, accessibility hoặc quyền tài sản.

## Trang web này do chính quy trình thiết kế ra

[`docs/index.html`](docs/index.html) được tạo ra bằng cách chạy đủ bảy bước — wireframe, ba
hướng, một cổng duyệt, bảng màu suy ra được, một lượt chuyển động với tám lần từ chối, và
một lượt rà soát tìm ra ba lỗi chặn rồi sửa chúng. Trang web trưng chính hiện vật của nó.

Năm cải tiến trong v1.0 đến từ lần chạy đó: một thư viện phong cách đã hứa mà chưa có, một
luật rằng chuyển động không bao giờ được chặn nội dung hiển thị, và ba chỗ làm rõ. Tự mình
làm người dùng đầu tiên là cách rà soát rẻ nhất.

**Toàn bộ lần chạy đã được công bố**, kể cả bản bị người duyệt từ chối:
[**xem tại đây**](https://ducnguyen.vn/agent-design-studio/example/), hoặc đọc file trong
[`docs/example/`](docs/example/). Bản brief, wireframe, ba phương án vẫn chạy được trong
trình duyệt, hệ thiết kế, bản đặc tả chuyển động kèm những lần từ chối, và ba báo cáo rà
soát — trong đó có một bản cho qua chính trang mà một giờ sau bị bác. Mọi thay đổi trước
khi công bố đều liệt kê ở [`docs/example/ABOUT.md`](docs/example/ABOUT.md).

## Đóng góp

Hoan nghênh issue và pull request. Luật duy nhất đáng nhớ: **mỗi tài liệu tham chiếu là một
playbook mà agent thi hành được** — thứ tự ra quyết định, checklist, ngưỡng, bảng biểu. Nếu
một thay đổi đọc như bài luận, chỗ của nó ở nơi khác.

## Ghi nhận

Quy trình này chắt lọc ý tưởng từ bốn dự án mở. Phần lập luận đã được diễn đạt lại bằng
ngôn ngữ của chúng tôi chứ không sao chép; những ngưỡng và giá trị cụ thể học được từ họ
thì được dùng với lòng biết ơn. Món nợ là thật và cụ thể.

Các recipe motion mới còn dùng [React Bits Animated Content](https://reactbits.dev/c/animations/animated-content)
làm tham khảo trực quan, cùng [demo/tài liệu GSAP](https://demos.gsap.com/) và
[tài liệu hiệu năng Motion](https://motion.dev/docs/performance) để phân biệt từng engine.
Pack **không chứa hay port** component React Bits: [giấy phép MIT + Commons Clause](https://github.com/DavidHDev/react-bits/blob/main/LICENSE.md)
hạn chế phân phối lại component. [Giấy phép runtime GSAP](https://gsap.com/community/standard-license/)
khác với MIT của [skill GSAP chính thức](https://github.com/greensock/gsap-skills).

| Dự án | Giấy phép | Đã dạy bộ này điều gì |
| --- | --- | --- |
| [emilkowalski/skills](https://github.com/emilkowalski/skills) | MIT | Nghề chuyển động: thứ tự ra quyết định, cổng tần suất, giá trị đường cong và thời lượng, spring và tính ngắt được, và chuẩn mực rằng sự chấp thuận phải giành lấy |
| [anthropics/skills → `skills/frontend-design`](https://github.com/anthropics/skills/tree/main/skills/frontend-design) | Apache-2.0 | Hiệu chỉnh chống rập khuôn, phương pháp hai lượt lập-kế-hoạch-rồi-tự-phản-biện, sự tiết chế, và chữ nghĩa được coi là vật liệu thiết kế |
| [plannotator/effective-html](https://github.com/plannotator/effective-html) | MIT | Chọn mức hoàn thiện trước tiên, wireframe cố ý để dở, prototype mô hình hoá trạng thái thật, và kiến trúc một-cửa-vào |
| [alchaincyf/huashu-design](https://github.com/alchaincyf/huashu-design) | MIT | Cổng ba hướng, giao thức tài sản thương hiệu, phương pháp suy ra màu, và bản phê bình có chấm điểm |

Cảm ơn các tác giả.

## Giấy phép

[MIT](LICENSE) © 2026 Duc Nguyen
