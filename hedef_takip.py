import airsim
import cv2
import numpy as np
import time
import math

# 1. BAĞLANTI VE KALKIŞ
print("AirSim'e bağlanılıyor...")
client = airsim.MultirotorClient()
client.confirmConnection()
client.enableApiControl(True)
client.armDisarm(True)

print("Kalkış yapılıyor...")
client.takeoffAsync().join()

# İlk kalkışta radar irtifasına (4.5m) çık
client.moveToPositionAsync(0, 0, -4.5, 2).join() 

# --- DURUM MAKİNESİ (STATE MACHINE) ---
# 1: Yeşil Silindir, 2: Turuncu Top, 3: Yeşil Koni, 4: Yeşil Küp
gorev = 1
print("GÖREV 1: Büyük Yeşil Silindir aranıyor...")

# 2. GÖRÜNTÜ İŞLEME VE RADAR/AVCI NAVİGASYON DÖNGÜSÜ
while True:
    responses = client.simGetImages([
        airsim.ImageRequest("0", airsim.ImageType.Scene, False, False)
    ])
    response = responses[0]
    
    img1d = np.frombuffer(response.image_data_uint8, dtype=np.uint8) 
    frame = img1d.reshape(response.height, response.width, 3).copy()
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # --- KUSURSUZLAŞTIRILMIŞ RENK MASKELERİ ---
    alt_yesil = np.array([35, 40, 40])
    ust_yesil = np.array([85, 255, 255])
    yesil_maske = cv2.inRange(hsv_frame, alt_yesil, ust_yesil)
    
    # KÖR NOKTA ÇÖZÜMÜ: Turuncu yelpazesi ışık parlamalarına karşı devasa oranda genişletildi!
    alt_turuncu = np.array([0, 50, 50])
    ust_turuncu = np.array([30, 255, 255])
    turuncu_maske = cv2.inRange(hsv_frame, alt_turuncu, ust_turuncu)

    aktif_maske = turuncu_maske if gorev == 2 else yesil_maske
    
    konturlar, _ = cv2.findContours(aktif_maske, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    ekran_merkezi_x = int(response.width / 2)
    ekran_merkezi_y = int(response.height / 2)
    
    hedef_bulundu = False
    en_buyuk_alan = 0
    en_iyi_kontur = None
    hedef_x, hedef_y = 0, 0
    hata_x, hata_y = 0, 0

    for kontur in konturlar:
        alan = cv2.contourArea(kontur)
        if alan > en_buyuk_alan:
            en_buyuk_alan = alan
            en_iyi_kontur = kontur

    if en_buyuk_alan > 800:
        cevre = cv2.arcLength(en_iyi_kontur, True)
        approx = cv2.approxPolyDP(en_iyi_kontur, 0.05 * cevre, True) 
        kose_sayisi = len(approx)
        
        sekil_adi = "Daire" if kose_sayisi > 6 else ("Ucgen" if kose_sayisi == 3 else "Dortgen")
        hedef_onaylandi = False
        hedef_ismi = ""

        # GÖREV ŞARTLARI
        if gorev == 1 and sekil_adi in ["Dortgen", "Daire"]:
            hedef_onaylandi = True
            hedef_ismi = "Buyuk Yesil Silindir"
        elif gorev == 2: # Turuncu maskede şekil sormaya gerek yok
            hedef_onaylandi = True
            hedef_ismi = "Turuncu Top"
        elif gorev == 3 and sekil_adi in ["Ucgen", "Daire"]:
            hedef_onaylandi = True
            hedef_ismi = "Buyuk Yesil Koni"
        elif gorev == 4 and sekil_adi in ["Dortgen", "Daire"]:
            hedef_onaylandi = True
            hedef_ismi = "Buyuk Yesil Kup"

        if hedef_onaylandi:
            hedef_bulundu = True
            x, y, w, h = cv2.boundingRect(en_iyi_kontur)
            
            hedef_x = int(x + w / 2)
            hedef_y = int(y + h / 2)
            hata_x = hedef_x - ekran_merkezi_x
            hata_y = hedef_y - ekran_merkezi_y
            
            renk = (0, 165, 255) if gorev == 2 else (0, 255, 0)
            cv2.rectangle(frame, (x, y), (x + w, y + h), renk, 2)
            cv2.putText(frame, f"HEDEF {gorev}: {hedef_ismi}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, renk, 2)
            
            # VURUŞ ONAYI: Hedef yeterince büyükse VE ekranın tam ortasındaysa (Hata payı < 70)
            if en_buyuk_alan > 35000 or (en_buyuk_alan > 8000 and abs(hata_x) < 70 and abs(hata_y) < 70):
                print(f"\n>>> [{hedef_ismi}] VURULDU! Sirada Gorev {gorev + 1} var! <<<")
                gorev += 1
                
                if gorev <= 4:
                    cv2.putText(frame, "VURULDU! RADAR MODUNA GECILIYOR...", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)
                    cv2.imshow("TEKNOFEST Radar Navigasyonu", frame)
                    cv2.waitKey(1)
                    
                    # DİKKAT: İleri uçuşu kesip sadece GÖKYÜZÜNE fırlıyor ve dönmeye başlıyor!
                    yaw_modu = airsim.YawMode(is_rate=True, yaw_or_rate=90)
                    client.moveByVelocityAsync(0, 0, -4.5, 2.0, airsim.DrivetrainType.MaxDegreeOfFreedom, yaw_modu)
                    time.sleep(2.0)
                
                continue 

    # --- PUSULA VE İRTİFA OKUMA ---
    orientation = client.simGetVehiclePose().orientation
    pitch, roll, yaw = airsim.to_eularian_angles(orientation)
    z_degeri = client.simGetVehiclePose().position.z_val

    # --- UÇUŞ ZEKASI (RADAR VE DALIŞ) ---
    if hedef_bulundu and gorev <= 4:
        # 1. AVCI DALIŞI MODU: Hedefe kilitlen ve üstüne uç!
        donus_hizi = hata_x * 0.1 
        yaw_modu = airsim.YawMode(is_rate=True, yaw_or_rate=donus_hizi)
        
        hiz_ileri = np.clip((20000 - en_buyuk_alan) * 0.0003, -1.0, 3.5)
        hiz_z = hata_y * 0.015 
        
        vx = hiz_ileri * math.cos(yaw)
        vy = hiz_ileri * math.sin(yaw)
        
        client.moveByVelocityAsync(vx, vy, hiz_z, 0.1, airsim.DrivetrainType.MaxDegreeOfFreedom, yaw_modu)
        cv2.putText(frame, "HEDEFE DALIYOR!", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
    elif gorev <= 4:
        # 2. RADAR (DENİZ FENERİ) MODU: İleri gitmek YOK! Sadece yüksel ve kendi etrafında fırıldak gibi dön.
        hiz_z = -1.5 if z_degeri > -4.5 else 0.0
        
        # Saniyede 45 derece hızla kendi ekseninde dön (İleri hız 0)
        yaw_modu = airsim.YawMode(is_rate=True, yaw_or_rate=45)
        client.moveByVelocityAsync(0, 0, hiz_z, 0.2, airsim.DrivetrainType.MaxDegreeOfFreedom, yaw_modu)
        
        durum_mesaji = "RADAR: 360 DERECE TARAMA" if z_degeri <= -4.0 else "RADAR ICIN TIRMANILIYOR"
        cv2.putText(frame, f"GOREV {gorev} ARANIYOR ({durum_mesaji})", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    cv2.imshow("TEKNOFEST Radar Navigasyonu", frame)

    # PARKUR BİTİŞİ
    if gorev == 5:
        cv2.putText(frame, "TEBRIKLER! TUM PARKUR TAMAMLANDI!", (30, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
        cv2.imshow("TEKNOFEST Radar Navigasyonu", frame)
        cv2.waitKey(4000) 
        break

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 3. İNİŞ VE GÜVENLİK
print("Görev sonlandırılıyor, inişe geçildi...")
cv2.destroyAllWindows()
client.landAsync().join()
client.armDisarm(False)
client.enableApiControl(False)
print("Sistem güvenli duruma geçti.")