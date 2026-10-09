import airsim
import cv2
import numpy as np
from ultralytics import YOLO

# 1. YAPAY ZEKA MODELİNİ YÜKLEME
print("YOLOv8 Yapay Zeka Modeli Yükleniyor...")
# 'yolov8n.pt' nano modeldir. İlk çalışmada otomatik olarak internetten indirilir.
model = YOLO("yolov8n.pt") 

# 2. BAĞLANTI VE KALKIŞ
print("AirSim ortamına bağlanılıyor...")
client = airsim.MultirotorClient()
client.confirmConnection()
client.enableApiControl(True)
client.armDisarm(True)

print("Kalkış yapılıyor...")
client.takeoffAsync().join()

# YENİ EKLENEN KISIM: Drone ileri doğru (X ekseninde 50 metre) yavaşça uçmaya başlar.
# Sonuna bilerek .join() KOYMUYORUZ ki kod aşağıya, kamera döngüsüne inebilsin.
print("Hedefe doğru otonom uçuş ve yapay zeka taraması başladı...")
client.moveToPositionAsync(50, 0, -5, 2) 

print("Yapay Zeka Destekli Kamera Aktif! (Çıkmak için 'q' tuşuna bas)")

# 3. CANLI YAYIN VE GÖRÜNTÜ İŞLEME DÖNGÜSÜ
while True:
    # Kameradan RGB görüntüyü çek (Sıkıştırmasız ham veri)
    responses = client.simGetImages([airsim.ImageRequest("0", airsim.ImageType.Scene, False, False)])
    response = responses[0]
    
    if response.image_data_uint8 == b'':
        continue

    # Ham bayt verisini OpenCV'nin anlayacağı Numpy matrisine çevir
    img1d = np.frombuffer(response.image_data_uint8, dtype=np.uint8)
    img_rgb = img1d.reshape(response.height, response.width, 3)

    # 4. YOLO İLE HEDEF TANIMA (Sihrin Gerçekleştiği Yer)
    # Görüntüyü YOLO'ya veriyoruz, o bize bulduğu nesneleri döndürüyor
    sonuclar = model(img_rgb, stream=True)
    
    # YOLO'nun bulduğu kutuları (bounding boxes) ve isimleri görüntünün üzerine çizdiriyoruz
    for sonuc in sonuclar:
        cizilmis_kare = sonuc.plot()

    # Çizilmiş kareyi ekranda göster
    cv2.imshow("Drone Gozu - YOLOv8 Hedef Tanıma", cizilmis_kare)

    # 'q' tuşuna basılırsa döngüyü kır
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 5. İNİŞ VE KAPANMA
print("Görev iptal edildi, iniş yapılıyor...")
cv2.destroyAllWindows()
client.landAsync().join()
client.armDisarm(False)
client.enableApiControl(False)
print("Sistem güvenli duruma geçti.")