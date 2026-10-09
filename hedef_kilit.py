import airsim
import cv2
import numpy as np
from ultralytics import YOLO

print("YOLOv8 Yükleniyor...")
model = YOLO("yolov8n.pt") 

print("AirSim'e bağlanılıyor...")
client = airsim.MultirotorClient()
client.confirmConnection()
client.enableApiControl(True)
client.armDisarm(True)

print("Kalkış yapılıyor...")
client.takeoffAsync().join()

# İlerideki araçları rahat görmek için biraz yükseliyoruz
client.moveToPositionAsync(0, 0, -4, 2).join()
print("Taktik Kamera Aktif. Etraf Taranıyor...")

while True:
    responses = client.simGetImages([airsim.ImageRequest("0", airsim.ImageType.Scene, False, False)])
    response = responses[0]
    
    if response.image_data_uint8 == b'':
        continue

    img1d = np.frombuffer(response.image_data_uint8, dtype=np.uint8)
    img_rgb = img1d.reshape(response.height, response.width, 3)
    
    # 1. REFERANS NOKTASI: Kameranın tam ortası (X ekseni)
    ekran_merkezi_x = response.width / 2

    sonuclar = model(img_rgb, stream=True)
    hedef_bulundu = False
    
    for sonuc in sonuclar:
        cizilmis_kare = sonuc.plot()
        
        # 2. HEDEF KOORDİNATLARI
        for box in sonuc.boxes:
            if int(box.cls) == 2:  # Sınıf 2 = Araba
                hedef_bulundu = True
                # Kutunun köşelerini alıyoruz
                x1, y1, x2, y2 = box.xyxy[0]
                # Kutunun tam ortasını (hedefin merkezini) buluyoruz
                hedef_merkezi_x = (x1 + x2) / 2
                
                # 3. HATA (SAPMA) HESAPLAMA
                sapma = hedef_merkezi_x - ekran_merkezi_x
                
                # 4. TEPKİ (TAKİP VE KİLİTLENME)
                # moveByVelocityBodyFrameAsync komutu, dronun kendi burnunun baktığı yöne (ileri) gitmesini sağlar.
                # İlk parametre olan '2', ileri doğru 2 m/s hızla git demektir.
                if sapma > 60:
                    print(f"Hedef Sağda -> Sağa dönerek üzerine gidiliyor...")
                    client.moveByVelocityBodyFrameAsync(2, 0, 0, 0.5, airsim.DrivetrainType.MaxDegreeOfFreedom, airsim.YawMode(is_rate=True, yaw_or_rate=15))
                elif sapma < -60:
                    print(f"Hedef Solda -> Sola dönerek üzerine gidiliyor...")
                    client.moveByVelocityBodyFrameAsync(2, 0, 0, 0.5, airsim.DrivetrainType.MaxDegreeOfFreedom, airsim.YawMode(is_rate=True, yaw_or_rate=-15))
                else:
                    print("🎯 HEDEF MERKEZDE! Tam isabet, hedefe yaklaşılıyor...")
                    # Hedef merkezdeyse dönüş yapma (yaw=0), sadece dümdüz ileri uç!
                    client.moveByVelocityBodyFrameAsync(2, 0, 0, 0.5, airsim.DrivetrainType.MaxDegreeOfFreedom, airsim.YawMode(is_rate=True, yaw_or_rate=0))

    # 5. ARAMA MODU: Eğer ekranda araba yoksa, kendi etrafında yavaşça dönerek radar gibi tara
    if not hedef_bulundu:
         client.moveByVelocityAsync(0, 0, 0, 0.5, airsim.DrivetrainType.MaxDegreeOfFreedom, airsim.YawMode(is_rate=True, yaw_or_rate=10))

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
client.landAsync().join()
client.armDisarm(False)
client.enableApiControl(False)
print("Sistem güvenli duruma geçti.")