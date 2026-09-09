# Airis: local code, HTML previews, and image classification

- Every fenced code block, including blocks without a language, has Copy and Download buttons. Copy supports localhost HTTPS clipboard and a legacy fallback.
- Ask for a website in HTML. The local LLM is instructed to generate a single self-contained document. Click **เปิด / อัปเดตตัวอย่าง** to render the current code and **ดาวน์โหลด HTML** to save `airis-website.html`.
- The preview runs inline scripts in an isolated iframe; remote scripts, images, network requests and forms are blocked. For best results use inline CSS/JS and SVG. Downloaded HTML contains the original code, not the preview restrictions.
- Attach a PNG/JPEG/WebP/BMP/TIFF with the paperclip. macOS Apple Vision classifies the image on-device and shows the top five labels and model confidence scores. These are candidate categories, not verified facts. The summary is attached as context for the next chat message. Non-image files continue through the document/OCR flow.
- Image classification currently requires macOS and the project's PyObjC Vision dependencies. No paid API, subscription, cloud inference, or additional model download is used for this feature. Chat/HTML uses existing local models. Electricity, hardware, and internet service are not free; third-party extensions retain their own provider terms.

Start the updated application with `bash scripts/run_web.sh`. If port 8000 already runs an older version, restart that process or use `PORT=8001 bash scripts/run_web.sh`.

Apple classification API: https://developer.apple.com/documentation/vision/vnclassifyimagerequest
