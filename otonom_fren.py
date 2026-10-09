import airsim
import cv2
import numpy as np
from ultralytics import YOLO
import time

# 1. YAPAY ZEKA YÜKLEMESİ
print("YOLOv8 Yükleniyor...")
model = YOLO("yolov8n.pt") 

# 2. BAĞLANTI VE KALKIŞ
print("AirSim'e bağlanılıyor...")
client = airsim.MultirotorClient()
client.confirmConnection()
client.enableApiControl(True)
client.armDisarm(True)

print("Kalkış yapılıyor...")
client.takeoffAsync().join()

# 3. İLERİYE DOĞRU UÇUŞ (Asenkron - Kodu Bekletmez)
print("Otonom Devriye Başladı. İleri uçuş yapılıyor...")
# X ekseninde 50 metre ileri, 4 m/s hızla uç
client.moveToPositionAsync(50, 0, -5, 4)

# 4. CANLI TARAMA VE KARAR MEKANİZMASI
print("Sensörler Aktif. Tehlike anında Acil Fren yapılacak!")

while True:
    responses = client.simGetImages([airsim.ImageRequest("0", airsim.ImageType.Scene, False, False)])
    response = responses[0]
    
    if response.image_data_uint8 == b'':
        continue

    img1d = np.frombuffer(response.image_data_uint8, dtype=np.uint8)
    img_rgb = img1d.reshape(response.height, response.width, 3)

    # Görüntüyü YOLO'ya ver
    sonuclar = model(img_rgb, stream=True)
    tehlike_algilandi = False

    for sonuc in sonuclar:
        cizilmis_kare = sonuc.plot()
        
        # SİHRİN OLDUĞU YER: Bulunan nesnelerin sınıf (ID) numaralarını kontrol et
        # YOLO COCO veri setinde: 0 = İnsan, 2 = Araba, 3 = Motosiklet vb.
        for cls in sonuc.boxes.cls:
            sinif_id = int(cls)
            if sinif_id == 0 or sinif_id == 2:  
                tehlike_algilandi = True

    cv2.imshow("Yapay Zeka - Acil Fren Sistemi", cizilmis_kare)

    # 5. TEPKİ (ACİL FREN)
    if tehlike_algilandi:
        print("\n🚨 DİKKAT! Hedef (İnsan/Araç) algılandı!")
        print("🛑 ACİL FREN YAPILIYOR ve MOTORLAR DURDURULUYOR!")
        # Drone'a olduğu yerde havada asılı kalma (hover) komutu veriyoruz
        client.hoverAsync().join()
        time.sleep(3) # Ekrana bakman için 3 saniye bekletiyoruz
        break # Uçuşu iptal edip döngüden çıkıyoruz

    # Manuel çıkış için
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 6. İNİŞ VE KAPANMA
print("\nİniş prosedürü başlatıldı...")
cv2.destroyAllWindows()
client.landAsync().join()
client.armDisarm(False)
client.enableApiControl(False)
print("Sistem güvenli duruma geçti.")