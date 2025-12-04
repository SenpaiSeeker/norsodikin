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
        
        _, mask_white = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
        _, mask_black = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY_INV)
        
        mask = cv2.bitwise_or(mask_white, mask_black)
        
        h, w = mask.shape
        roi_mask = np.zeros_like(mask)
        corner_size = 150 
        
        roi_mask[0:corner_size, 0:corner_size] = 255
        roi_mask[0:corner_size, w-corner_size:w] = 255
        roi_mask[h-corner_size:h, 0:corner_size] = 255
        roi_mask[h-corner_size:h, w-corner_size:w] = 255
        
        final_mask = cv2.bitwise_and(mask, roi_mask)
        
        kernel = np.ones((3,3), np.uint8)
        final_mask = cv2.dilate(final_mask, kernel, iterations=1)
        
        res = cv2.inpaint(img, final_mask, 3, cv2.INPAINT_TELEA)
        
        is_success, buffer = cv2.imencode(".jpg", res)
        if not is_success:
            raise ValueError("Gagal encode gambar hasil.")
            
        return buffer.tobytes()

    async def remove_watermark(self, image_bytes: bytes) -> bytes:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(self._sync_remove_watermark, image_bytes))
