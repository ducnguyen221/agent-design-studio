# Token contract: existing source, DTCG subset và legacy

Hệ đã có CSS/TS/Figma source giữ authority đó. JSON export/delta không tự trở thành
canonical. Hệ mới chọn JSON thì chỉ gọi **DTCG 2025.10 subset**, không chứng nhận toàn
chuẩn (Community Group Report, không W3C Recommendation). Nguồn chính thức:
https://www.designtokens.org/tr/2025.10/format/

Mỗi token có `$value`, `$type` trực tiếp hoặc kế thừa từ group. Metadata lý do dùng
`$description`/`$extensions`. Group/token không trộn children vào token; tên path
không có dấu chấm hoặc ngoặc alias. Subset nhận Unicode và khoảng trắng trong tên;
cùng quy tắc áp lên mỗi đoạn alias. Ký tự điều khiển và ký hiệu cross-file `#`, `/`,
`\`, `:` không được hỗ trợ trong tên hoặc alias; tên bắt đầu `$` dành cho metadata.

| Type hỗ trợ | Value |
| --- | --- |
| color | `{colorSpace:"srgb",components:[r,g,b],alpha?}`; số hữu hạn 0–1 |
| dimension | `{value:number,unit:"px"|"rem"}` |
| duration | `{value:number,unit:"ms"|"s"}` |
| fontFamily | chuỗi không rỗng hoặc mảng chuỗi không rỗng |
| fontWeight | số 1–1000 hoặc tên weight chuẩn |
| number | số JSON hữu hạn, không boolean |

Alias `{path.to.token}` trong **cùng file, cùng type**; inherited type được resolve
trước so. Cross-file/reference đặc biệt chưa hỗ trợ. Cycle/missing target/type mismatch
báo `reference_cycle`, `missing_target`, `type_mismatch`; syntax alias ngoài subset
báo `unsupported_reference`. CSS string thay object báo `invalid_value`; shadow,
typography composite, gradient/easing chưa hỗ trợ báo `unsupported_type`.
Shadow/easing giữ ở docs/code có trace, không đưa vào file token subset đã nhận hợp lệ.

Ví dụ token hợp lệ:
```json
{"gap":{"$type":"dimension","$value":{"value":4,"unit":"px"}},
 "space":{"$type":"dimension","$value":"{gap}"}}
```

`tokens.json` map chuỗi và `_why` cũ là legacy; chỉ `--legacy-tokens` xác nhận đọc
map, không DTCG validate. Không sửa frozen example để ép schema mới.

Verifier không tạo CSS và không chứng nhận alias/theme runtime. Parity phải có map
JSON/source → CSS variable → component → route/render và evidence thay một token
trên fixture; xuất CSS thủ công/dẫn xuất phải ghi chiều authority. Không claim sync
chỉ vì file parse được. Khi validation fail không xuất/đưa lên token CSS từ input lỗi.
