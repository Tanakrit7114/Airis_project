from __future__ import annotations
import re, threading, platform
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_MODEL="black-forest-labs/FLUX.2-klein-4B"; DEFAULT_STEPS=4; DEFAULT_WIDTH=1024; DEFAULT_HEIGHT=1024; DEFAULT_QUANTIZE=8
class LocalImageGenerator:
    def __init__(self,output_dir="data/generated_images",model_name=DEFAULT_MODEL,steps=DEFAULT_STEPS,width=DEFAULT_WIDTH,height=DEFAULT_HEIGHT,quantize=DEFAULT_QUANTIZE,keep_loaded=False):
        self.output_dir=Path(output_dir); self.output_dir.mkdir(parents=True,exist_ok=True); self.model_name=model_name; self.steps=max(1,min(20,int(steps))); self.width=max(256,min(1536,int(width))); self.height=max(256,min(1536,int(height))); self.quantize=quantize if quantize in (4,8) else None; self.keep_loaded=bool(keep_loaded); self._model=None; self._lock=threading.Lock()
    @staticmethod
    def sanitize_prompt(prompt):
        value=re.sub(r"\s+"," ",str(prompt or "")).strip()
        if not value: raise ValueError("กรุณาระบุคำอธิบายภาพที่ต้องการสร้าง")
        return value[:2000]
    def available(self):
        if not (platform.system()=="Darwin" and platform.machine().lower() in {"arm64","aarch64"}): return False
        try: import mflux  # noqa
        except ImportError: return False
        return True
    def _load_model(self):
        if self._model is not None:return self._model
        if not self.available(): raise RuntimeError("Local image generation ใช้ได้บน macOS Apple Silicon เท่านั้นในรุ่นนี้")
        try:
            from mflux.models.common.config import ModelConfig
            from mflux.models.flux2.variants import Flux2Klein
        except ImportError as exc: raise RuntimeError("MFLUX ยังไม่ได้ติดตั้ง") from exc
        self._model=Flux2Klein(model_path=self.model_name,model_config=ModelConfig.flux2_klein_4b(),quantize=self.quantize); return self._model
    def _release_model(self):
        self._model=None
        try:
            import mlx.core as mx; mx.clear_cache()
        except Exception: pass
    def generate(self,prompt,*,seed=None,width=None,height=None,steps=None):
        prompt=self.sanitize_prompt(prompt); w=max(256,min(1536,int(width or self.width))); h=max(256,min(1536,int(height or self.height))); st=max(1,min(20,int(steps or self.steps))); seed=int(seed) if seed is not None else abs(hash((prompt,datetime.now().isoformat())))%(2**31)
        # FLUX requires aligned dimensions. Always release memory after errors.
        w=max(256,(w//16)*16); h=max(256,(h//16)*16)
        with self._lock:
            try:
                model=self._load_model()
                result=model.generate_image(seed=seed,prompt=prompt,num_inference_steps=st,width=w,height=h,guidance=1.0)
                filename=f"airis_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{seed}.png"
                path=self.output_dir/filename
                result.image.save(path)
            finally:
                if not self.keep_loaded:self._release_model()
        return {"filename":filename,"url":f"/generated/{filename}","path":str(path),"prompt":prompt,"seed":seed,"width":w,"height":h,"steps":st,"model":self.model_name,"quantize":self.quantize}
