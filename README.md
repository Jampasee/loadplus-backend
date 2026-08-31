# LOAD PLUS - Cloud License Server 🚀
ระบบเซิร์ฟเวอร์กลางสำหรับตรวจสอบ License Key, ผูกรหัสเครื่อง (Hardware ID), และระบบเช็คอัปเดตอัตโนมัติ

---

## 🌐 วิธีนำขึ้น Render.com (ฟรีตลอดชีพ 100%):

1. สมัครบัญชีฟรีที่ https://render.com
2. สร้าง Repository บน GitHub แล้วอัปโหลดโฟลเดอร์ cloud_backend/ ขึ้นไป
3. บน Render.com กด "New +" ➔ เลือก "Web Service"
4. เลือก Repository ของคุณ แล้วตั้งค่าตามนี้:
   - Environment: Python 3
   - Build Command: pip install -r requirements.txt
   - Start Command: uvicorn server:app --host 0.0.0.0 --port $PORT
   - Plan: Free (0 USD)
5. กด "Create Web Service"
6. คุณจะได้ URL เว็บไซต์ฟรี เช่น: https://loadplus-api.onrender.com

---

## ⏰ วิชามาร ปลุกเซิร์ฟเวอร์ห้ามหลับ 24 ชม. (ฟรี):
1. สมัครบัญชีฟรีที่ https://uptimerobot.com
2. กด "Add New Monitor" ➔ เลือก HTTP(s)
3. ใส่ URL ของ Render.com: https://loadplus-api.onrender.com/
4. ตั้งเวลา Every 10 minutes
5. เซิร์ฟเวอร์ของคุณจะตื่นพร้อมทำงานตลอด 24 ชั่วโมง ฟรีตลอดไป!

---

## 🔑 การสร้าง License Key ใหม่สำหรับขายลูกค้า:
ยิง POST Request ไปที่: https://loadplus-api.onrender.com/api/admin/generate
- Header: x-admin-secret: LOADPLUS_SUPER_ADMIN_SECRET_2026
- Body: {"count": 5, "key_type": "lifetime", "note": "Order #001"}
- ผลลัพธ์: จะได้รหัสคีย์รูปแบบ LP-PRO-XXXX-XXXX-XXXX นำไปส่งมอบให้ลูกค้าได้ทันที!
