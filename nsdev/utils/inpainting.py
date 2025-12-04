import cv2
import numpy as np
from io import BytesIO
import asyncio
from functools import partial

class ImageInpainter:
    def _sync_remove_watermark(self, image_bytes: bytes) -> bytes:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Gagal membaca data gambar.")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        gradient = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
        
        _, mask = cv2.threshold(gradient, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        h, w = img.shape[:2]
        roi_mask = np.zeros_like(mask)
        
        padding_x = int(w * 0.02)
        padding_y = int(h * 0.02)
        corner_w = int(w * 0.3) 
        corner_h = int(h * 0.15)

        cv2.rectangle(roi_mask, (padding_x, padding_y), (padding_x + corner_w, padding_y + corner_h), 255, -1)
        cv2.rectangle(roi_mask, (w - corner_w - padding_x, padding_y), (w - padding_x, padding_y + corner_h), 255, -1)
        cv2.rectangle(roi_mask, (padding_x, h - corner_h - padding_y), (padding_x + corner_w, h - padding_y), 255, -1)
        cv2.rectangle(roi_mask, (w - corner_w - padding_x, h - corner_h - padding_y), (w - padding_x, h - padding_y), 255, -1)
        
        mask = cv2.bitwise_and(mask, roi_mask)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 1)) 
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.dilate(mask, kernel, iterations=2) 

        res = cv2.inpaint(img, mask, 3, cv2.INPAINT_NS) 
        
        is_success, buffer = cv2.imencode(".jpg", res, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        if not is_success:
            raise ValueError("Gagal encode gambar hasil.")
            
        return buffer.tobytes()

    async def remove_watermark(self, image_bytes: bytes) -> bytes:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(self._sync_remove_watermark, image_bytes))
