"""On-device image classification using Apple's system model."""
import io
import platform
from PIL import Image, ImageOps, UnidentifiedImageError


def classify_image(content: bytes) -> dict:
    if not content or len(content) > 10 * 1024 * 1024:
        raise ValueError('กรุณาใช้ภาพขนาดไม่เกิน 10 MB')
    try:
        with Image.open(io.BytesIO(content)) as source:
            if source.width * source.height > 25_000_000:
                raise ValueError('ภาพมีขนาดเกิน 25 ล้านพิกเซล')
            image = ImageOps.exif_transpose(source).convert('RGB')
            image.thumbnail((1536, 1536))
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG')
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError('ไม่สามารถอ่านไฟล์ภาพนี้ได้') from exc
    if platform.system() != 'Darwin':
        raise RuntimeError('การจำแนกภาพแบบออฟไลน์นี้รองรับ macOS (Apple Vision)')
    from Foundation import NSData
    from Vision import VNClassifyImageRequest, VNImageRequestHandler
    data = buffer.getvalue()
    request = VNClassifyImageRequest.alloc().init()
    handler = VNImageRequestHandler.alloc().initWithData_options_(NSData.dataWithBytes_length_(data, len(data)), {})
    success, error = handler.performRequests_error_([request], None)
    if not success:
        raise RuntimeError(f'Apple Vision ไม่สามารถวิเคราะห์ภาพได้: {error}')
    labels = sorted([{'label': str(x.identifier()), 'confidence': float(x.confidence())}
                     for x in request.results() or []], key=lambda x: x['confidence'], reverse=True)[:5]
    return {'labels': labels, 'engine': 'Apple Vision · on-device', 'api_cost': 0}
